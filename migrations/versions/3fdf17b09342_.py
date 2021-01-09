"""Add asset_skips table

Revision ID: 3fdf17b09342
Revises: d2d11ae29985
Create Date: 2021-01-09 12:37:32.440975

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3fdf17b09342"
down_revision = "d2d11ae29985"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "asset_skips",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )


def downgrade():
    op.drop_table("asset_skips")
