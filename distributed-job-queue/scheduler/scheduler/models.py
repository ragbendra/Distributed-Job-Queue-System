"""
Simplified models for scheduler.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import sys
sys.path.append('/shared')
from shared.enums import JobType, JobPriority

Base = declarative_base()


class ScheduledJob(Base):
    """Scheduled job model."""
    
    __tablename__ = "scheduled_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, unique=True)
    job_type = Column(SQLEnum(JobType), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    priority = Column(SQLEnum(JobPriority), default=JobPriority.MEDIUM)
    is_active = Column(Integer, default=1)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
