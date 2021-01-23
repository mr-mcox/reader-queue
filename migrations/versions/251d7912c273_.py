"""Migrate pinboard_created_at

Revision ID: 251d7912c273
Revises: a2e01120bb64
Create Date: 2021-01-23 12:21:06.818142

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

Base = declarative_base()

# revision identifiers, used by Alembic.
revision = "251d7912c273"
down_revision = "a2e01120bb64"
branch_labels = None
depends_on = None


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    pinboard_created_at = Column(DateTime)

    events = relationship("AssetEvent", back_populates="asset")


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

    for asset in session.query(Asset).filter(Asset.pinboard_created_at != None):
        asset.events.append(
            AssetEvent(name="bookmarked", occurred_at=asset.pinboard_created_at)
        )
        session.add(asset)
    session.commit()

    op.drop_column("assets", "pinboard_created_at")


def downgrade():
    op.add_column(
        "assets",
        sa.Column(
            "pinboard_created_at",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
    )

    bind = op.get_bind()
    session = orm.Session(bind=bind)

    for event in (
        session.query(AssetEvent)
        .filter(AssetEvent.name == "bookmarked")
        .order_by(AssetEvent.occurred_at)
    ):
        asset = event.asset
        asset.pinboard_created_at = event.occurred_at
        session.add(asset)
        session.delete(event)
    session.commit()
