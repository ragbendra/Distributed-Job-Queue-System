"""
Scheduled jobs API endpoints.
"""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from croniter import croniter
import sys
sys.path.append('/shared')

from app.database import get_db
from app.models import ScheduledJob
from app.schemas import ScheduledJobCreateRequest, ScheduledJobResponse

router = APIRouter(prefix="/api/v1/scheduled-jobs", tags=["scheduled-jobs"])


@router.post("", response_model=ScheduledJobResponse, status_code=201)
async def create_scheduled_job(
    job_request: ScheduledJobCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new scheduled job.
    
    Args:
        job_request: Scheduled job creation request
        db: Database session
        
    Returns:
        Created scheduled job
        
    Raises:
        HTTPException: If cron expression is invalid or name already exists
    """
    # Validate cron expression
    try:
        cron = croniter(job_request.cron_expression, datetime.utcnow())
        next_run = cron.get_next(datetime)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cron expression: {str(e)}")
    
    # Check if name already exists
    existing = db.query(ScheduledJob).filter(ScheduledJob.name == job_request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Scheduled job with this name already exists")
    
    # Create scheduled job
    scheduled_job = ScheduledJob(
        name=job_request.name,
        job_type=job_request.job_type,
        cron_expression=job_request.cron_expression,
        payload=job_request.payload,
        priority=job_request.priority,
        is_active=1 if job_request.is_active else 0,
        next_run_at=next_run,
    )
    
    db.add(scheduled_job)
    db.commit()
    db.refresh(scheduled_job)
    
    return ScheduledJobResponse(
        id=scheduled_job.id,
        name=scheduled_job.name,
        job_type=scheduled_job.job_type,
        cron_expression=scheduled_job.cron_expression,
        payload=scheduled_job.payload,
        priority=scheduled_job.priority,
        is_active=bool(scheduled_job.is_active),
        last_run_at=scheduled_job.last_run_at,
        next_run_at=scheduled_job.next_run_at,
        created_at=scheduled_job.created_at,
    )


@router.get("", response_model=list[ScheduledJobResponse])
async def list_scheduled_jobs(
    is_active: bool = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List scheduled jobs.
    
    Args:
        is_active: Filter by active status
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of scheduled jobs
    """
    query = db.query(ScheduledJob)
    
    if is_active is not None:
        query = query.filter(ScheduledJob.is_active == (1 if is_active else 0))
    
    jobs = query.order_by(ScheduledJob.next_run_at).limit(limit).offset(offset).all()
    
    return [
        ScheduledJobResponse(
            id=job.id,
            name=job.name,
            job_type=job.job_type,
            cron_expression=job.cron_expression,
            payload=job.payload,
            priority=job.priority,
            is_active=bool(job.is_active),
            last_run_at=job.last_run_at,
            next_run_at=job.next_run_at,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.delete("/{scheduled_job_id}", status_code=204)
async def delete_scheduled_job(
    scheduled_job_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a scheduled job.
    
    Args:
        scheduled_job_id: Scheduled job identifier
        db: Database session
        
    Raises:
        HTTPException: If scheduled job not found
    """
    scheduled_job = db.query(ScheduledJob).filter(ScheduledJob.id == scheduled_job_id).first()
    
    if not scheduled_job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    
    db.delete(scheduled_job)
    db.commit()


@router.patch("/{scheduled_job_id}/toggle", response_model=ScheduledJobResponse)
async def toggle_scheduled_job(
    scheduled_job_id: UUID,
    db: Session = Depends(get_db),
):
    """Toggle scheduled job active status.
    
    Args:
        scheduled_job_id: Scheduled job identifier
        db: Database session
        
    Returns:
        Updated scheduled job
        
    Raises:
        HTTPException: If scheduled job not found
    """
    scheduled_job = db.query(ScheduledJob).filter(ScheduledJob.id == scheduled_job_id).first()
    
    if not scheduled_job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    
    scheduled_job.is_active = 0 if scheduled_job.is_active else 1
    db.commit()
    db.refresh(scheduled_job)
    
    return ScheduledJobResponse(
        id=scheduled_job.id,
        name=scheduled_job.name,
        job_type=scheduled_job.job_type,
        cron_expression=scheduled_job.cron_expression,
        payload=scheduled_job.payload,
        priority=scheduled_job.priority,
        is_active=bool(scheduled_job.is_active),
        last_run_at=scheduled_job.last_run_at,
        next_run_at=scheduled_job.next_run_at,
        created_at=scheduled_job.created_at,
    )
