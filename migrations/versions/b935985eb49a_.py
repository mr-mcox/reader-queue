"""Add asset tags table

Revision ID: b935985eb49a
Revises: 19b29f00aa97
Create Date: 2021-01-12 21:23:15.238037

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b935985eb49a"
down_revision = "19b29f00aa97"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "asset_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag", sa.String(), nullable=True),
        sa.Column("asset_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(op.f("ix_asset_tags_tag"), "asset_tags", ["tag"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_asset_tags_tag"), table_name="asset_tags")
    op.drop_table("asset_tags")
