"""Add asset events table and migrate read_at data

Revision ID: da2d7241137d
Revises: a0b09af877ba
Create Date: 2021-01-23 11:44:57.886461

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import orm
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "da2d7241137d"
down_revision = "a0b09af877ba"
branch_labels = None
depends_on = None


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    read_at = Column(DateTime)

    events = relationship("AssetEvent", back_populates="asset")


class AssetEvent(Base):
    __tablename__ = "asset_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    name = Column(String, nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False)

    asset = relationship("Asset", back_populates="events")


def upgrade():
    op.create_table(
        "asset_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["assets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index(
        op.f("ix_asset_events_name"), "asset_events", ["name"], unique=False
    )

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for asset in session.query(Asset).filter(Asset.read_at != None):
        asset.events.append(AssetEvent(name="read", occurred_at=asset.read_at))
        session.add(asset)
    session.commit()

    op.drop_column("assets", "read_at")


def downgrade():
    op.add_column(
        "assets",
        sa.Column(
            "read_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
    )
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for event in (
        session.query(AssetEvent)
        .filter(AssetEvent.name == "read")
        .order_by(AssetEvent.occurred_at)
    ):
        asset = event.asset
        asset.read_at = event.occurred_at
        session.add(asset)
    session.commit()

    op.drop_index(op.f("ix_asset_events_name"), table_name="asset_events")
    op.drop_table("asset_events")
