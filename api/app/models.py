"""
Database models for job queue system.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
import sys
sys.path.append('/shared')
from shared.enums import JobStatus, JobPriority, JobType


class Job(Base):
    """Job model."""
    
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    priority = Column(SQLEnum(JobPriority), default=JobPriority.MEDIUM, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, index=True)
    payload = Column(JSON, nullable=False)
    max_retries = Column(Integer, default=3)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True, index=True)
    worker_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    retry_attempts = relationship("RetryAttempt", back_populates="job", cascade="all, delete-orphan")
    dead_letter = relationship("DeadLetter", back_populates="job", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job {self.id} - {self.job_type} - {self.status}>"


class RetryAttempt(Base):
    """Retry attempt model."""
    
    __tablename__ = "retry_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="retry_attempts")
    
    def __repr__(self):
        return f"<RetryAttempt {self.id} - Job {self.job_id} - Attempt {self.attempt_number}>"


class DeadLetter(Base):
    """Dead letter model for permanently failed jobs."""
    
    __tablename__ = "dead_letters"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    total_attempts = Column(Integer, nullable=False)
    first_attempt_at = Column(DateTime(timezone=True), nullable=False)
    final_failure_at = Column(DateTime(timezone=True), server_default=func.now())
    failure_reason = Column(Text, nullable=False)
    all_error_messages = Column(JSON, nullable=True)
    
    # Relationships
    job = relationship("Job", back_populates="dead_letter")
    
    def __repr__(self):
        return f"<DeadLetter {self.id} - Job {self.job_id}>"


class ScheduledJob(Base):
    """Scheduled job model for recurring jobs."""
    
    __tablename__ = "scheduled_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, unique=True)
    job_type = Column(SQLEnum(JobType), nullable=False)
    cron_expression = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    priority = Column(SQLEnum(JobPriority), default=JobPriority.MEDIUM)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ScheduledJob {self.name} - {self.cron_expression}>"
