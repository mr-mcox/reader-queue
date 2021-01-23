"""Adding status column

Revision ID: f2c09231bc08
Revises: 251d7912c273
Create Date: 2021-01-23 12:29:55.005831

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


# revision identifiers, used by Alembic.
revision = "f2c09231bc08"
down_revision = "251d7912c273"
branch_labels = None
depends_on = None


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    status = Column(String)


def upgrade():
    op.add_column("assets", sa.Column("status", sa.String(), nullable=True))
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for asset in session.query(Asset):
        asset.status = "active"
        session.add(asset)
    session.commit()

    op.alter_column("assets", "status", nullable=False)


def downgrade():
    op.drop_index(op.f("ix_assets_status"), table_name="assets")
    op.drop_column("assets", "status")
