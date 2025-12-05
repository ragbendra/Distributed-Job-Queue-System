"""
Simplified models for worker (imports from API models).
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import sys
sys.path.append('/shared')
from shared.enums import JobStatus, JobPriority, JobType

Base = declarative_base()


class Job(Base):
    """Job model."""
    
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_type = Column(SQLEnum(JobType), nullable=False)
    priority = Column(SQLEnum(JobPriority), default=JobPriority.MEDIUM)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    payload = Column(JSON, nullable=False)
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    worker_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    retry_attempts = relationship("RetryAttempt", back_populates="job")
    dead_letter = relationship("DeadLetter", back_populates="job", uselist=False)


class RetryAttempt(Base):
    """Retry attempt model."""
    
    __tablename__ = "retry_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    job = relationship("Job", back_populates="retry_attempts")


class DeadLetter(Base):
    """Dead letter model."""
    
    __tablename__ = "dead_letters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(SQLEnum(JobType), nullable=False)
    payload = Column(JSON, nullable=False)
    total_attempts = Column(Integer, nullable=False)
    first_attempt_at = Column(DateTime(timezone=True), nullable=False)
    final_failure_at = Column(DateTime(timezone=True), server_default=func.now())
    failure_reason = Column(Text, nullable=False)
    all_error_messages = Column(JSON, nullable=True)
    
    job = relationship("Job", back_populates="dead_letter")
