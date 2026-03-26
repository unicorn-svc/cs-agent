"""SQLAlchemy models for database."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ProcessingHistory(Base):
    """Processing history record."""

    __tablename__ = "processing_history"

    id = Column(String(36), primary_key=True)
    query_hash = Column(String(64))
    inquiry_channel = Column(String(50))
    category = Column(String(50))
    complexity = Column(String(20))
    process_type = Column(String(20))
    top_score = Column(Float)
    search_attempts = Column(Integer)
    saved_cost = Column(Integer)
    elapsed_ms = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DailyCostSummary(Base):
    """Daily cost summary."""

    __tablename__ = "daily_cost_summary"

    date = Column(String(10), primary_key=True)
    total_inquiries = Column(Integer, default=0)
    auto_processed = Column(Integer, default=0)
    total_saved = Column(Integer, default=0)
    avg_response_ms = Column(Float, default=0.0)
    alert_triggered = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
