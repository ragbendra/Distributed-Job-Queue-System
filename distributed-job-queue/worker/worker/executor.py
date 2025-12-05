"""
Job executor that runs job handlers.
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
import sys
sys.path.append('/shared')
from shared.enums import JobType, JobStatus

from worker.handlers.email_handler import EmailHandler
from worker.handlers.video_handler import VideoHandler
from worker.handlers.scraper_handler import ScraperHandler
from worker.models import Job
from worker.database import get_db
from worker.config import settings

logger = logging.getLogger(__name__)


class JobExecutor:
    """Executes jobs using appropriate handlers."""
    
    def __init__(self):
        """Initialize job executor with handlers."""
        self.handlers = {
            JobType.SEND_EMAIL: EmailHandler(),
            JobType.PROCESS_VIDEO: VideoHandler(),
            JobType.SCRAPE_WEBSITE: ScraperHandler(),
        }
    
    def execute(self, job_id: str, job_type: JobType, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a job.
        
        Args:
            job_id: Job identifier
            job_type: Type of job
            payload: Job payload
            
        Returns:
            Execution result
            
        Raises:
            Exception: If job execution fails
        """
        logger.info(f"Executing job {job_id} of type {job_type}")
        
        # Update job status to RUNNING
        db = get_db()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.utcnow()
                job.worker_id = settings.worker_id
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update job status to RUNNING: {e}")
        finally:
            db.close()
        
        # Get appropriate handler
        handler = self.handlers.get(job_type)
        if not handler:
            raise ValueError(f"No handler found for job type: {job_type}")
        
        try:
            # Execute job
            start_time = datetime.utcnow()
            result = handler.execute(payload)
            end_time = datetime.utcnow()
            
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Job {job_id} completed successfully in {duration:.2f}s")
            
            # Update job status to COMPLETED
            db = get_db()
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.utcnow()
                    job.error_message = None
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to update job status to COMPLETED: {e}")
            finally:
                db.close()
            
            return {
                'success': True,
                'result': result,
                'duration': duration,
            }
            
        except Exception as e:
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            
            logger.error(f"Job {job_id} failed: {error_msg}")
            logger.debug(f"Traceback: {error_traceback}")
            
            # Update job with error
            db = get_db()
            try:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.error_message = error_msg
                    db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update job error message: {update_error}")
            finally:
                db.close()
            
            raise Exception(error_msg)
