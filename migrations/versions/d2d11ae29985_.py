"""Create assets table

Revision ID: d2d11ae29985
Revises: 
Create Date: 2021-01-02 17:43:10.665628

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2d11ae29985"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("pinboard_created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_url"), "assets", ["url"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_assets_url"), table_name="assets")
    op.drop_table("assets")
