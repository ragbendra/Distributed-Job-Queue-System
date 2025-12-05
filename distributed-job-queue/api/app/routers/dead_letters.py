"""
Dead letter queue API endpoints.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import sys
sys.path.append('/shared')
from shared.enums import JobType, JobStatus

from app.database import get_db
from app.dependencies import get_rabbitmq
from app.models import DeadLetter, Job
from app.schemas import DeadLetterResponse, DeadLetterListResponse
from shared.rabbitmq_client import RabbitMQClient

router = APIRouter(prefix="/api/v1/dead-letters", tags=["dead-letters"])


@router.get("", response_model=DeadLetterListResponse)
async def list_dead_letters(
    job_type: Optional[JobType] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List dead letter jobs.
    
    Args:
        job_type: Filter by job type
        limit: Maximum number of results
        offset: Offset for pagination
        db: Database session
        
    Returns:
        Paginated list of dead letters
    """
    query = db.query(DeadLetter)
    
    if job_type:
        query = query.filter(DeadLetter.job_type == job_type)
    
    total = query.count()
    items = query.order_by(DeadLetter.final_failure_at.desc()).limit(limit).offset(offset).all()
    
    return DeadLetterListResponse(
        items=items,
        total=total,
        page=offset // limit + 1,
        page_size=limit,
    )


@router.get("/{dead_letter_id}", response_model=DeadLetterResponse)
async def get_dead_letter(
    dead_letter_id: UUID,
    db: Session = Depends(get_db),
):
    """Get dead letter details.
    
    Args:
        dead_letter_id: Dead letter identifier
        db: Database session
        
    Returns:
        Dead letter details
        
    Raises:
        HTTPException: If dead letter not found
    """
    dead_letter = db.query(DeadLetter).filter(DeadLetter.id == dead_letter_id).first()
    
    if not dead_letter:
        raise HTTPException(status_code=404, detail="Dead letter not found")
    
    return dead_letter


@router.post("/{dead_letter_id}/retry", status_code=202)
async def retry_dead_letter(
    dead_letter_id: UUID,
    db: Session = Depends(get_db),
    rabbitmq: RabbitMQClient = Depends(get_rabbitmq),
):
    """Retry a dead letter job.
    
    Args:
        dead_letter_id: Dead letter identifier
        db: Database session
        rabbitmq: RabbitMQ client
        
    Raises:
        HTTPException: If dead letter not found
    """
    dead_letter = db.query(DeadLetter).filter(DeadLetter.id == dead_letter_id).first()
    
    if not dead_letter:
        raise HTTPException(status_code=404, detail="Dead letter not found")
    
    # Get the original job
    job = db.query(Job).filter(Job.id == dead_letter.job_id).first()
    
    if job:
        # Reset job status and retry count
        job.status = JobStatus.PENDING
        job.retry_count = 0
        job.error_message = None
        
        # Delete dead letter record
        db.delete(dead_letter)
        db.commit()
        
        # Republish to queue
        rabbitmq.publish_job(
            job_id=str(job.id),
            job_type=job.job_type.value,
            priority=job.priority,
            payload=job.payload,
        )
        
        return {"message": "Job resubmitted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Original job not found")


@router.delete("/{dead_letter_id}", status_code=204)
async def delete_dead_letter(
    dead_letter_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a dead letter.
    
    Args:
        dead_letter_id: Dead letter identifier
        db: Database session
        
    Raises:
        HTTPException: If dead letter not found
    """
    dead_letter = db.query(DeadLetter).filter(DeadLetter.id == dead_letter_id).first()
    
    if not dead_letter:
        raise HTTPException(status_code=404, detail="Dead letter not found")
    
    db.delete(dead_letter)
    db.commit()
