from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from flask_login import UserMixin
import uuid

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    upstream_id = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    url = Column(String, nullable=False, index=True, unique=True)
    title = Column(String)
    description = Column(String(2000))
    biblio = Column(JSON)
    change_hash = Column(String)
    status = Column(String, index=True, nullable=False, default="active")
    user = relationship("User", back_populates="assets")
    tags = relationship("AssetTag", back_populates="asset")
    events = relationship("AssetEvent", back_populates="asset")


class AssetTag(Base):
    __tablename__ = "asset_tags"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    tag = Column(String, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    asset = relationship("Asset", back_populates="tags")


class User(UserMixin, Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String(100))
    pinboard_auth = Column(String(100))
    assets = relationship("Asset", back_populates="user")


class AssetEvent(Base):
    __tablename__ = "asset_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id"))
    name = Column(String, nullable=False, index=True)
    occurred_at = Column(DateTime, nullable=False)

    asset = relationship("Asset", back_populates="events")
