"""
Job scheduler main process.
"""
import logging
import signal
import sys
import time
from datetime import datetime
from croniter import croniter
sys.path.append('/shared')
from shared.rabbitmq_client import RabbitMQClient

from scheduler.config import settings
from scheduler.database import get_db
from scheduler.models import ScheduledJob

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global state
running = True
rabbitmq_client = None


def signal_handler(signum, frame):
    """Handle shutdown signals.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False
    
    if rabbitmq_client:
        rabbitmq_client.close()
    
    sys.exit(0)


def process_scheduled_jobs():
    """Process scheduled jobs that are due."""
    global rabbitmq_client
    
    db = get_db()
    try:
        # Get active scheduled jobs that are due
        now = datetime.utcnow()
        due_jobs = db.query(ScheduledJob).filter(
            ScheduledJob.is_active == 1,
            ScheduledJob.next_run_at <= now
        ).all()
        
        if not due_jobs:
            logger.debug("No scheduled jobs due")
            return
        
        logger.info(f"Found {len(due_jobs)} scheduled jobs due for execution")
        
        # Connect to RabbitMQ if not connected
        if not rabbitmq_client:
            rabbitmq_client = RabbitMQClient(settings.rabbitmq_url)
            rabbitmq_client.connect()
        
        # Process each due job
        for scheduled_job in due_jobs:
            try:
                logger.info(f"Processing scheduled job: {scheduled_job.name}")
                
                # Publish job to queue
                # Note: We're creating a one-time job, not tracking it in the jobs table
                # In a real implementation, you'd create a Job record first
                rabbitmq_client.publish_job(
                    job_id=f"scheduled-{scheduled_job.id}-{int(time.time())}",
                    job_type=scheduled_job.job_type.value,
                    priority=scheduled_job.priority,
                    payload=scheduled_job.payload,
                )
                
                # Update last_run_at and calculate next_run_at
                scheduled_job.last_run_at = now
                
                # Calculate next run time using croniter
                cron = croniter(scheduled_job.cron_expression, now)
                next_run = cron.get_next(datetime)
                scheduled_job.next_run_at = next_run
                
                db.commit()
                
                logger.info(
                    f"Scheduled job {scheduled_job.name} published. "
                    f"Next run at {next_run}"
                )
                
            except Exception as e:
                logger.error(f"Error processing scheduled job {scheduled_job.name}: {e}")
                db.rollback()
                
    except Exception as e:
        logger.error(f"Error querying scheduled jobs: {e}")
    finally:
        db.close()


def main():
    """Main scheduler function."""
    global running
    
    logger.info("Starting job scheduler")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"RabbitMQ: {settings.rabbitmq_url}")
    logger.info(f"Poll interval: {settings.scheduler_poll_interval}s")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Main loop
    while running:
        try:
            process_scheduled_jobs()
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
        
        # Sleep for poll interval
        time.sleep(settings.scheduler_poll_interval)
    
    logger.info("Scheduler stopped")


if __name__ == "__main__":
    main()
