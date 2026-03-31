"""Serviço da US-07 — catálogo centralizado de dados."""

import logging

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from models.annotation import Annotation, AnnotationConflict
from models.collection import Collection, Comment
from models.dataset import Dataset, DatasetEntry
from models.user import User

logger = logging.getLogger(__name__)

# Tabelas cujo tamanho é somado para estimar uso do banco
_SIZE_TABLES = (
    "collections",
    "comments",
    "datasets",
    "dataset_entries",
    "annotations",
    "annotation_conflicts",
    "resolutions",
    "users",
)


def get_summary(db: Session) -> dict:
    """Contagem de registros + estimativa de tamanho via pg_total_relation_size."""
    collections_count = db.query(func.count(Collection.id)).scalar() or 0
    comments_count = db.query(func.count(Comment.id)).scalar() or 0
    datasets_count = db.query(func.count(Dataset.id)).scalar() or 0
    annotations_count = db.query(func.count(Annotation.id)).scalar() or 0

    # Estimativa de tamanho em MB (dados + índices + TOAST)
    total_bytes = 0
    for table in _SIZE_TABLES:
        try:
            row = db.execute(
                text("SELECT pg_total_relation_size(:t)"),
                {"t": table},
            ).scalar()
            total_bytes += row or 0
        except Exception:
            logger.debug("pg_total_relation_size falhou para %s", table)

    estimated_size_mb = round(total_bytes / (1024 * 1024), 2)

    return {
        "collections_count": collections_count,
        "comments_count": comments_count,
        "datasets_count": datasets_count,
        "annotations_count": annotations_count,
        "estimated_size_mb": estimated_size_mb,
    }


def list_all_collections(db: Session) -> list[dict]:
    """Todas as coletas com nome do coletor, ordenadas por data decrescente."""
    collections = db.query(Collection).order_by(Collection.created_at.desc()).all()

    if not collections:
        return []

    # Batch load users
    user_ids = {c.collected_by for c in collections}
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    # Batch: autores distintos por coleta
    col_ids = [c.id for c in collections]
    user_counts = (
        db.query(
            Comment.collection_id,
            func.count(func.distinct(Comment.author_channel_id)),
        )
        .filter(Comment.collection_id.in_(col_ids))
        .group_by(Comment.collection_id)
        .all()
    )
    users_by_col = {row[0]: row[1] for row in user_counts}

    return [
        {
            "collection_id": c.id,
            "video_id": c.video_id,
            "video_title": c.video_title,
            "total_comments": c.total_comments,
            "total_users": users_by_col.get(c.id, 0),
            "status": c.status,
            "enrich_status": c.enrich_status,
            "channel_dates_failed": c.channel_dates_failed,
            "collected_by": user_map[c.collected_by].username
            if c.collected_by in user_map
            else "",
            "created_at": c.created_at,
            "completed_at": c.completed_at,
            "duration_seconds": c.duration_seconds,
        }
        for c in collections
    ]


def list_all_datasets(db: Session) -> list[dict]:
    """Todos os datasets limpos, ordenados por data decrescente."""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()

    if not datasets:
        return []

    # Batch load collections e users para enriquecer
    collection_ids = {ds.collection_id for ds in datasets}
    collections = db.query(Collection).filter(Collection.id.in_(collection_ids)).all()
    col_map = {c.id: c for c in collections}

    user_ids = {ds.created_by for ds in datasets}
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    results = []
    for ds in datasets:
        # Contar comentários dos autores selecionados neste dataset
        author_ids = [
            e.author_channel_id
            for e in db.query(DatasetEntry.author_channel_id)
            .filter(DatasetEntry.dataset_id == ds.id)
            .all()
        ]
        total_comments = 0
        if author_ids:
            total_comments = (
                db.query(func.count(Comment.id))
                .filter(
                    Comment.collection_id == ds.collection_id,
                    Comment.author_channel_id.in_(author_ids),
                )
                .scalar()
                or 0
            )

        results.append(
            {
                "dataset_id": ds.id,
                "name": ds.name,
                "collection_id": ds.collection_id,
                "video_id": col_map[ds.collection_id].video_id
                if ds.collection_id in col_map
                else "",
                "criteria": ds.criteria_applied,
                "total_users_original": ds.total_users_original,
                "total_selected": ds.total_users_selected,
                "total_comments": total_comments,
                "created_by": user_map[ds.created_by].username
                if ds.created_by in user_map
                else "",
                "created_at": ds.created_at,
            }
        )

    return results


def get_annotation_progress(db: Session) -> list[dict]:
    """Progresso de anotação por dataset."""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()

    if not datasets:
        return []

    results = []
    for ds in datasets:
        # Comentários associados ao dataset via entries
        entries = (
            db.query(DatasetEntry.author_channel_id)
            .filter(DatasetEntry.dataset_id == ds.id)
            .all()
        )
        author_ids = [e[0] for e in entries]

        if not author_ids:
            results.append(
                {
                    "dataset_id": ds.id,
                    "dataset_name": ds.name,
                    "total": 0,
                    "annotated": 0,
                    "pending": 0,
                    "conflicts": 0,
                    "conflicts_resolved": 0,
                    "annotators_count": 0,
                    "bots_users": 0,
                    "bots_comments": 0,
                }
            )
            continue

        # Contar comentários únicos desses autores na coleta do dataset
        comment_ids_q = db.query(Comment.id).filter(
            Comment.collection_id == ds.collection_id,
            Comment.author_channel_id.in_(author_ids),
        )
        total = comment_ids_q.count()

        comment_ids = [r[0] for r in comment_ids_q.all()]

        # Comentários que possuem pelo menos uma anotação
        annotated = 0
        if comment_ids:
            annotated = (
                db.query(func.count(func.distinct(Annotation.comment_id)))
                .filter(Annotation.comment_id.in_(comment_ids))
                .scalar()
                or 0
            )

        # Conflitos
        conflicts = 0
        conflicts_resolved = 0
        if comment_ids:
            conflicts = (
                db.query(func.count(AnnotationConflict.id))
                .filter(AnnotationConflict.comment_id.in_(comment_ids))
                .scalar()
                or 0
            )
            conflicts_resolved = (
                db.query(func.count(AnnotationConflict.id))
                .filter(
                    AnnotationConflict.comment_id.in_(comment_ids),
                    AnnotationConflict.status == "resolved",
                )
                .scalar()
                or 0
            )

        # Anotadores distintos que interagiram com comentários do dataset
        annotators_count = 0
        if comment_ids:
            annotators_count = (
                db.query(func.count(func.distinct(Annotation.annotator_id)))
                .filter(Annotation.comment_id.in_(comment_ids))
                .scalar()
                or 0
            )

        # Contagem de bots: comentários cujo rótulo final é "bot"
        # Rótulo final = resolução do conflito OU consenso entre anotadores
        bots_comments = 0
        bot_author_ids: set[str] = set()
        if comment_ids:
            # Comentários com consenso "bot" (todas as anotações = bot, sem conflito)
            conflict_comment_ids = {
                r[0]
                for r in db.query(AnnotationConflict.comment_id)
                .filter(AnnotationConflict.comment_id.in_(comment_ids))
                .all()
            }
            for cid in comment_ids:
                if cid in conflict_comment_ids:
                    continue
                anns = (
                    db.query(Annotation.label)
                    .filter(Annotation.comment_id == cid)
                    .all()
                )
                if anns and all(a[0] == "bot" for a in anns):
                    bots_comments += 1
                    comment_obj = (
                        db.query(Comment.author_channel_id)
                        .filter(Comment.id == cid)
                        .first()
                    )
                    if comment_obj:
                        bot_author_ids.add(comment_obj[0])

            # Comentários resolvidos como "bot"
            resolved_bot_ids = (
                db.query(AnnotationConflict.comment_id)
                .filter(
                    AnnotationConflict.comment_id.in_(comment_ids),
                    AnnotationConflict.status == "resolved",
                    AnnotationConflict.resolved_label == "bot",
                )
                .all()
            )
            for (rid,) in resolved_bot_ids:
                bots_comments += 1
                comment_obj = (
                    db.query(Comment.author_channel_id)
                    .filter(Comment.id == rid)
                    .first()
                )
                if comment_obj:
                    bot_author_ids.add(comment_obj[0])

        results.append(
            {
                "dataset_id": ds.id,
                "dataset_name": ds.name,
                "total": total,
                "annotated": annotated,
                "pending": total - annotated,
                "conflicts": conflicts,
                "conflicts_resolved": conflicts_resolved,
                "annotators_count": annotators_count,
                "bots_users": len(bot_author_ids),
                "bots_comments": bots_comments,
            }
        )

    return results
