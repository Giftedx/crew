"""
Simple schema for testing OAuth imports without SQLAlchemy 2.0 dependencies.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

BaseModel = declarative_base()


class Account(BaseModel):
    """Platform account for a creator."""

    __tablename__ = "creator_ops_accounts"

    id = Column(Integer, primary_key=True)
    tenant = Column(String(255), nullable=False)
    workspace = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    handle = Column(String(255), nullable=False)
    display_name = Column(String(255))
    platform_id = Column(String(255), nullable=False)
    oauth_scopes = Column(Text)
    access_token_encrypted = Column(Text)
    refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
