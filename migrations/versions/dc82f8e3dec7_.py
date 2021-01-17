"""empty message

Revision ID: dc82f8e3dec7
Revises: eddf06cbc32d
Create Date: 2021-01-16 10:26:05.675614

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "dc82f8e3dec7"
down_revision = "eddf06cbc32d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("password_hash", sa.String(length=100), nullable=True),
        sa.Column("pinboard_auth", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("id"),
    )
    op.create_unique_constraint(None, "asset_skips", ["id"])
    op.create_unique_constraint(None, "asset_tags", ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "asset_tags", type_="unique")
    op.drop_constraint(None, "asset_skips", type_="unique")
    op.drop_table("users")
    # ### end Alembic commands ###