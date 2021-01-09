from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False, index=True, unique=True)
    description = Column(String)
    pinboard_created_at = Column(DateTime)
    skips = relationship("AssetSkip", back_populates="asset")


class AssetSkip(Base):
    __tablename__ = "asset_skips"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    occurred_at = Column(DateTime, nullable=False)
    asset_id = Column(String, ForeignKey("assets.id"))
    asset = relationship("Asset", back_populates="skips")
