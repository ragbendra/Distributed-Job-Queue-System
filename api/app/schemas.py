"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
import sys
sys.path.append('/shared')
from shared.enums import JobStatus, JobPriority, JobType


# Job Schemas
class JobCreateRequest(BaseModel):
    """Request schema for creating a job."""
    job_type: JobType
    priority: JobPriority = JobPriority.MEDIUM
    payload: Dict[str, Any]
    max_retries: Optional[int] = 3
    scheduled_for: Optional[datetime] = None


class JobResponse(BaseModel):
    """Response schema for job creation."""
    job_id: UUID
    status: JobStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobDetailResponse(BaseModel):
    """Detailed job response."""
    job_id: UUID
    job_type: JobType
    priority: JobPriority
    status: JobStatus
    payload: Dict[str, Any]
    max_retries: int
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    worker_id: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class RetryAttemptResponse(BaseModel):
    """Retry attempt response."""
    id: UUID
    attempt_number: int
    started_at: datetime
    failed_at: Optional[datetime]
    error_message: Optional[str]
    next_retry_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class JobWithRetriesResponse(JobDetailResponse):
    """Job response with retry history."""
    retry_attempts: List[RetryAttemptResponse] = []


# Dead Letter Schemas
class DeadLetterResponse(BaseModel):
    """Dead letter response."""
    id: UUID
    job_id: UUID
    job_type: JobType
    payload: Dict[str, Any]
    total_attempts: int
    first_attempt_at: datetime
    final_failure_at: datetime
    failure_reason: str
    all_error_messages: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class DeadLetterListResponse(BaseModel):
    """Paginated dead letter list response."""
    items: List[DeadLetterResponse]
    total: int
    page: int
    page_size: int


# Scheduled Job Schemas
class ScheduledJobCreateRequest(BaseModel):
    """Request schema for creating a scheduled job."""
    name: str = Field(..., min_length=1, max_length=200)
    job_type: JobType
    cron_expression: str = Field(..., min_length=1, max_length=100)
    payload: Dict[str, Any]
    priority: JobPriority = JobPriority.MEDIUM
    is_active: bool = True


class ScheduledJobResponse(BaseModel):
    """Scheduled job response."""
    id: UUID
    name: str
    job_type: JobType
    cron_expression: str
    payload: Dict[str, Any]
    priority: JobPriority
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Statistics Schemas
class QueueStats(BaseModel):
    """Queue statistics."""
    high: int
    medium: int
    low: int


class StatsResponse(BaseModel):
    """Statistics response."""
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    dead_letter_count: int
    active_workers: int
    queue_breakdown: QueueStats
