"""Adding read at column

Revision ID: eddf06cbc32d
Revises: b935985eb49a
Create Date: 2021-01-16 08:45:28.604715

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "eddf06cbc32d"
down_revision = "b935985eb49a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("assets", sa.Column("read_at", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("assets", "read_at")
