"""Move asset skips over to events table

Revision ID: a2e01120bb64
Revises: da2d7241137d
Create Date: 2021-01-23 12:06:34.708391

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import orm
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = "a2e01120bb64"
down_revision = "da2d7241137d"
branch_labels = None
depends_on = None

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    read_at = Column(DateTime)

    skips = relationship("AssetSkip", back_populates="asset")
    events = relationship("AssetEvent", back_populates="asset")


class AssetSkip(Base):
    __tablename__ = "asset_skips"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    occurred_at = Column(DateTime, nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    asset = relationship("Asset", back_populates="skips")


class AssetEvent(Base):
    __tablename__ = "asset_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    name = Column(String, nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False)

    asset = relationship("Asset", back_populates="events")


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for skip in session.query(AssetSkip):
        asset = skip.asset
        asset.events.append(AssetEvent(name="skipped", occurred_at=skip.occurred_at))
        session.add(asset)
    session.commit()
    op.drop_table("asset_skips")


def downgrade():
    op.create_table(
        "asset_skips",
        sa.Column("id", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "occurred_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column("asset_id", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"], ["assets.id"], name="asset_skips_asset_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="asset_skips_pkey"),
    )
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    for event in (
        session.query(AssetEvent)
        .filter(AssetEvent.name == "skipped")
        .order_by(AssetEvent.occurred_at)
    ):
        asset = event.asset
        asset.skips.append(AssetSkip(occurred_at=event.occurred_at))
        session.delete(event)
        session.add(asset)
    session.commit()
