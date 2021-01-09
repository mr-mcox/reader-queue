"""Changing name of columns

Revision ID: 19b29f00aa97
Revises: 3fdf17b09342
Create Date: 2021-01-09 16:40:22.554836

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "19b29f00aa97"
down_revision = "3fdf17b09342"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assets", sa.Column("change_hash", sa.String(), nullable=True))
    op.add_column("assets", sa.Column("title", sa.String(), nullable=True))
    op.drop_column("assets", "description")


def downgrade():
    op.add_column(
        "assets",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_column("assets", "title")
    op.drop_column("assets", "change_hash")
