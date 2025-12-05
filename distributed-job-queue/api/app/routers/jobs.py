"""
Job management API endpoints.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import sys
sys.path.append('/shared')
from shared.enums import JobStatus, JobPriority

from app.database import get_db
from app.dependencies import get_rabbitmq, get_redis
from app.models import Job, RetryAttempt
from app.schemas import (
    JobCreateRequest,
    JobResponse,
    JobDetailResponse,
    JobWithRetriesResponse,
)
from shared.rabbitmq_client import RabbitMQClient
from shared.redis_client import RedisClient

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    job_request: JobCreateRequest,
    db: Session = Depends(get_db),
    rabbitmq: RabbitMQClient = Depends(get_rabbitmq),
    redis: RedisClient = Depends(get_redis),
):
    """Create and submit a new job.
    
    Args:
        job_request: Job creation request
        db: Database session
        rabbitmq: RabbitMQ client
        redis: Redis client
        
    Returns:
        Created job response
    """
    # Create job record
    job = Job(
        job_type=job_request.job_type,
        priority=job_request.priority,
        payload=job_request.payload,
        max_retries=job_request.max_retries,
        scheduled_for=job_request.scheduled_for,
        status=JobStatus.PENDING,
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Cache job status in Redis
    redis.set_job_status(str(job.id), job.status.value)
    
    # Publish to RabbitMQ (unless scheduled for future)
    if job.scheduled_for is None or job.scheduled_for <= datetime.utcnow():
        rabbitmq.publish_job(
            job_id=str(job.id),
            job_type=job.job_type.value,
            priority=job.priority,
            payload=job.payload,
        )
    
    return JobResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
    )


@router.get("/{job_id}", response_model=JobWithRetriesResponse)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get job details by ID.
    
    Args:
        job_id: Job identifier
        db: Database session
        redis: Redis client
        
    Returns:
        Job details with retry history
        
    Raises:
        HTTPException: If job not found
    """
    # Try to get status from Redis cache first
    cached_status = redis.get_job_status(str(job_id))
    
    # Get job from database
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get retry attempts
    retry_attempts = db.query(RetryAttempt).filter(
        RetryAttempt.job_id == job_id
    ).order_by(RetryAttempt.attempt_number).all()
    
    return JobWithRetriesResponse(
        job_id=job.id,
        job_type=job.job_type,
        priority=job.priority,
        status=job.status,
        payload=job.payload,
        max_retries=job.max_retries,
        retry_count=job.retry_count,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        scheduled_for=job.scheduled_for,
        worker_id=job.worker_id,
        error_message=job.error_message,
        retry_attempts=retry_attempts,
    )


@router.delete("/{job_id}", status_code=204)
async def cancel_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Cancel a pending job.
    
    Args:
        job_id: Job identifier
        db: Database session
        redis: Redis client
        
    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.PENDING, JobStatus.RETRYING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status {job.status}"
        )
    
    job.status = JobStatus.CANCELLED
    db.commit()
    
    # Update cache
    redis.set_job_status(str(job_id), JobStatus.CANCELLED.value)


@router.get("", response_model=list[JobDetailResponse])
async def list_jobs(
    status: Optional[JobStatus] = Query(None),
    priority: Optional[JobPriority] = Query(None),
    job_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List jobs with optional filtering.
    
    Args:
        status: Filter by status
        priority: Filter by priority
        job_type: Filter by job type
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of jobs
    """
    query = db.query(Job)
    
    if status:
        query = query.filter(Job.status == status)
    if priority:
        query = query.filter(Job.priority == priority)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    jobs = query.order_by(Job.created_at.desc()).limit(limit).offset(offset).all()
    
    return jobs
