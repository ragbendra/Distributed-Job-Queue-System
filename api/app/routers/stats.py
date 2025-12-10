"""
Statistics and monitoring API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import sys
sys.path.append('/shared')
from shared.enums import JobStatus, JobPriority

from app.database import get_db
from app.dependencies import get_redis
from app.models import Job, DeadLetter
from app.schemas import StatsResponse, QueueStats
from shared.redis_client import RedisClient

router = APIRouter(prefix="/api/v1/stats", tags=["statistics"])


@router.get("", response_model=StatsResponse)
async def get_statistics(
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Get system statistics.
    
    Args:
        db: Database session
        redis: Redis client
        
    Returns:
        System statistics
    """
    # Count jobs by status
    pending_jobs = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.PENDING
    ).scalar()
    
    running_jobs = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.RUNNING
    ).scalar()
    
    completed_jobs = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.COMPLETED
    ).scalar()
    
    failed_jobs = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.FAILED
    ).scalar()
    
    # Count dead letters
    dead_letter_count = db.query(func.count(DeadLetter.id)).scalar()
    
    # Get active workers from Redis
    active_workers = len(redis.get_active_workers())
    
    # Count pending jobs by priority
    high_priority = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.PENDING,
        Job.priority == JobPriority.HIGH
    ).scalar()
    
    medium_priority = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.PENDING,
        Job.priority == JobPriority.MEDIUM
    ).scalar()
    
    low_priority = db.query(func.count(Job.id)).filter(
        Job.status == JobStatus.PENDING,
        Job.priority == JobPriority.LOW
    ).scalar()
    
    return StatsResponse(
        pending_jobs=pending_jobs or 0,
        running_jobs=running_jobs or 0,
        completed_jobs=completed_jobs or 0,
        failed_jobs=failed_jobs or 0,
        dead_letter_count=dead_letter_count or 0,
        active_workers=active_workers,
        queue_breakdown=QueueStats(
            high=high_priority or 0,
            medium=medium_priority or 0,
            low=low_priority or 0,
        ),
    )
