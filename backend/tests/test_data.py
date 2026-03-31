"""Testes da US-07 — catálogo centralizado de dados."""

import uuid
from datetime import datetime, timedelta

from models.annotation import Annotation, AnnotationConflict
from models.collection import Collection, Comment
from models.dataset import Dataset, DatasetEntry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_collection(db, user_id, *, video_id="vid123", status="completed"):
    col = Collection(
        video_id=video_id,
        status=status,
        collected_by=user_id,
        total_comments=5,
    )
    db.add(col)
    db.flush()
    return col


def _make_comments(db, collection_id, author_channel_id, count=5):
    comments = []
    for i in range(count):
        c = Comment(
            collection_id=collection_id,
            comment_id=f"{author_channel_id}_c{i}",
            author_channel_id=author_channel_id,
            author_display_name=f"User {author_channel_id}",
            text_original=f"Comentario {i} do {author_channel_id}",
            like_count=i,
            reply_count=0,
            published_at=datetime(2024, 1, 1) + timedelta(minutes=i),
            updated_at=datetime(2024, 1, 1) + timedelta(minutes=i),
        )
        db.add(c)
        comments.append(c)
    db.flush()
    return comments


def _make_dataset(db, collection_id, user_id, author_channel_ids):
    ds = Dataset(
        name=f"test_dataset_{uuid.uuid4().hex[:6]}",
        collection_id=collection_id,
        criteria_applied=["percentil"],
        thresholds={},
        total_users_original=10,
        total_users_selected=len(author_channel_ids),
        created_by=user_id,
    )
    db.add(ds)
    db.flush()
    for channel_id in author_channel_ids:
        entry = DatasetEntry(
            dataset_id=ds.id,
            author_channel_id=channel_id,
            author_display_name=f"User {channel_id}",
            comment_count=5,
            matched_criteria=["percentil"],
        )
        db.add(entry)
    db.flush()
    return ds


# ---------------------------------------------------------------------------
# GET /data/summary
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_retorna_contadores_corretos(self, client, db, auth_as_user):
        """Inserir 2 coletas com 5 comentários cada → counts corretos."""
        col1 = _make_collection(db, auth_as_user.id, video_id="vid1")
        col2 = _make_collection(db, auth_as_user.id, video_id="vid2")
        _make_comments(db, col1.id, "author_a", count=5)
        _make_comments(db, col2.id, "author_b", count=5)
        db.commit()

        resp = client.get("/data/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["collections_count"] == 2
        assert data["comments_count"] == 10
        assert data["datasets_count"] == 0
        assert data["annotations_count"] == 0
        assert data["estimated_size_mb"] >= 0

    def test_summary_sem_token_retorna_401(self, client):
        resp = client.get("/data/summary")
        assert resp.status_code == 401

    def test_summary_vazio(self, client, auth_as_user):
        """Banco vazio retorna zeros."""
        resp = client.get("/data/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["collections_count"] == 0
        assert data["comments_count"] == 0


# ---------------------------------------------------------------------------
# GET /data/collections
# ---------------------------------------------------------------------------


class TestCollections:
    def test_listagem_compartilhada(self, client, db, auth_as_user, admin_user):
        """User A cria coleta, user B (auth_as_user) consegue ver."""
        _make_collection(db, admin_user.id, video_id="vid_admin")
        db.commit()

        resp = client.get("/data/collections")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["video_id"] == "vid_admin"

    def test_collections_sem_token_retorna_401(self, client):
        resp = client.get("/data/collections")
        assert resp.status_code == 401

    def test_collections_retorna_campos_esperados(self, client, db, auth_as_user):
        col = _make_collection(db, auth_as_user.id, video_id="vid_check")
        db.commit()

        resp = client.get("/data/collections")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        item = data[0]
        assert item["collection_id"] == str(col.id)
        assert item["video_id"] == "vid_check"
        assert item["status"] == "completed"
        assert "created_at" in item
        assert "collected_by" in item

    def test_collections_vazio(self, client, auth_as_user):
        resp = client.get("/data/collections")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /data/datasets
# ---------------------------------------------------------------------------


class TestDatasets:
    def test_datasets_retorna_lista_vazia(self, client, auth_as_user):
        """Sem datasets cadastrados retorna []."""
        resp = client.get("/data/datasets")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_datasets_sem_token_retorna_401(self, client):
        resp = client.get("/data/datasets")
        assert resp.status_code == 401

    def test_datasets_retorna_dados(self, client, db, auth_as_user):
        col = _make_collection(db, auth_as_user.id)
        ds = _make_dataset(db, col.id, auth_as_user.id, ["ch1"])
        db.commit()

        resp = client.get("/data/datasets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["dataset_id"] == str(ds.id)
        assert data[0]["name"] == ds.name
        assert data[0]["criteria"] == ["percentil"]
        assert data[0]["total_selected"] == 1


# ---------------------------------------------------------------------------
# GET /data/annotations
# ---------------------------------------------------------------------------


class TestAnnotations:
    def test_annotations_retorna_lista_vazia(self, client, auth_as_user):
        """Sem datasets/anotações retorna []."""
        resp = client.get("/data/annotations")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_annotations_sem_token_retorna_401(self, client):
        resp = client.get("/data/annotations")
        assert resp.status_code == 401

    def test_annotations_progresso_correto(self, client, db, auth_as_user, admin_user):
        """Dataset com anotações e conflitos retorna progresso."""
        col = _make_collection(db, auth_as_user.id)
        comments = _make_comments(db, col.id, "ch_ann", count=3)
        ds = _make_dataset(db, col.id, auth_as_user.id, ["ch_ann"])

        # Anotar 2 dos 3 comentários
        ann1 = Annotation(
            comment_id=comments[0].id,
            annotator_id=auth_as_user.id,
            label="bot",
            justificativa="teste",
        )
        ann2 = Annotation(
            comment_id=comments[1].id,
            annotator_id=auth_as_user.id,
            label="humano",
        )
        db.add_all([ann1, ann2])
        db.flush()

        # Criar conflito no primeiro comentário
        ann1_admin = Annotation(
            comment_id=comments[0].id,
            annotator_id=admin_user.id,
            label="humano",
        )
        db.add(ann1_admin)
        db.flush()

        conflict = AnnotationConflict(
            comment_id=comments[0].id,
            annotation_a_id=ann1.id,
            annotation_b_id=ann1_admin.id,
            status="pending",
        )
        db.add(conflict)
        db.commit()

        resp = client.get("/data/annotations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        progress = data[0]
        assert progress["dataset_id"] == str(ds.id)
        assert progress["total"] == 3
        assert progress["annotated"] == 2
        assert progress["pending"] == 1
        assert progress["conflicts"] == 1
        assert progress["conflicts_resolved"] == 0
        assert progress["annotators_count"] == 2
        # comment[0] tem conflito pendente → sem rótulo final de bot
        # comment[1] tem label="humano" (consenso) → 0 bots
        assert progress["bots_comments"] == 0
        assert progress["bots_users"] == 0
