from sqlalchemy import (
    Column,
    String,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False, index=True, unique=True)
    description = Column(String)
    pinboard_created_at = Column(DateTime)
