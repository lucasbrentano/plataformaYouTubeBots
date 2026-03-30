"""add indexes on comments for clean queries

Revision ID: 0012
Revises: 0011
Create Date: 2026-03-29 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_comments_collection_id",
        "comments",
        ["collection_id"],
    )
    op.create_index(
        "ix_comments_author_channel_id",
        "comments",
        ["author_channel_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_comments_author_channel_id", table_name="comments")
    op.drop_index("ix_comments_collection_id", table_name="comments")
