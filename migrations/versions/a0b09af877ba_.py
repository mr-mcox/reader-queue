"""Add biblio and description

Revision ID: a0b09af877ba
Revises: 7b60399cd600
Create Date: 2021-01-19 08:20:22.685578

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a0b09af877ba"
down_revision = "7b60399cd600"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "assets",
        sa.Column("biblio", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "assets", sa.Column("description", sa.String(length=2000), nullable=True)
    )


def downgrade():
    op.drop_column("assets", "description")
    op.drop_column("assets", "biblio")
