"""
RabbitMQ consumer for worker.
"""
import json
import logging
import traceback
from datetime import datetime
import sys
sys.path.append('/shared')
from shared.enums import JobType, JobStatus, QUEUE_NAMES, JobPriority
from shared.rabbitmq_client import RabbitMQClient

from worker.executor import JobExecutor
from worker.retry_logic import RetryManager
from worker.models import Job, RetryAttempt, DeadLetter
from worker.database import get_db
from worker.config import settings

logger = logging.getLogger(__name__)


class JobConsumer:
    """Consumes jobs from RabbitMQ queues."""
    
    def __init__(self):
        """Initialize job consumer."""
        self.rabbitmq = RabbitMQClient(settings.rabbitmq_url)
        self.executor = JobExecutor()
        self.retry_manager = RetryManager()
        self.running = True
    
    def start(self):
        """Start consuming jobs from queues."""
        logger.info(f"Worker {settings.worker_id} starting...")
        
        # Connect to RabbitMQ
        self.rabbitmq.connect()
        
        # Start consuming from high priority queue first
        # In a real implementation, we'd consume from all queues with different priorities
        # For simplicity, we'll consume from medium priority queue
        queue_name = QUEUE_NAMES[JobPriority.MEDIUM]
        
        logger.info(f"Consuming from queue: {queue_name}")
        
        try:
            self.rabbitmq.consume(
                queue_name=queue_name,
                callback=self.on_message,
                prefetch_count=settings.worker_prefetch_count,
            )
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop()
    
    def on_message(self, channel, method, properties, body):
        """Handle incoming message.
        
        Args:
            channel: RabbitMQ channel
            method: Delivery method
            properties: Message properties
            body: Message body
        """
        try:
            # Parse message
            message = json.loads(body)
            job_id = message['job_id']
            job_type = JobType(message['job_type'])
            payload = message['payload']
            
            logger.info(f"Received job {job_id} of type {job_type}")
            
            # Execute job
            try:
                result = self.executor.execute(job_id, job_type, payload)
                
                # Acknowledge message on success
                self.rabbitmq.ack_message(method.delivery_tag)
                logger.info(f"Job {job_id} completed successfully")
                
            except Exception as e:
                # Job failed, handle retry logic
                self.handle_job_failure(job_id, job_type, payload, str(e), traceback.format_exc())
                
                # Acknowledge message (we'll handle retry manually)
                self.rabbitmq.ack_message(method.delivery_tag)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
            
            # Negative acknowledge and requeue
            self.rabbitmq.nack_message(method.delivery_tag, requeue=False)
    
    def handle_job_failure(self, job_id: str, job_type: JobType, payload: dict, error_msg: str, error_traceback: str):
        """Handle job failure with retry logic.
        
        Args:
            job_id: Job identifier
            job_type: Type of job
            payload: Job payload
            error_msg: Error message
            error_traceback: Error traceback
        """
        logger.info(f"Handling failure for job {job_id}")
        
        db = get_db()
        try:
            # Get job from database
            job = db.query(Job).filter(Job.id == job_id).first()
            
            if not job:
                logger.error(f"Job {job_id} not found in database")
                return
            
            # Increment retry count
            job.retry_count += 1
            
            # Log retry attempt
            retry_attempt = RetryAttempt(
                job_id=job_id,
                attempt_number=job.retry_count,
                started_at=job.started_at or datetime.utcnow(),
                failed_at=datetime.utcnow(),
                error_message=error_msg,
                error_traceback=error_traceback,
            )
            
            # Check if should retry
            if self.retry_manager.should_retry(job_type, job.retry_count, job.max_retries):
                # Calculate next retry time
                next_retry_time = self.retry_manager.calculate_next_retry_time(
                    job_type,
                    job.retry_count
                )
                
                retry_attempt.next_retry_at = next_retry_time
                
                # Update job status
                job.status = JobStatus.RETRYING
                job.error_message = error_msg
                
                db.add(retry_attempt)
                db.commit()
                
                # Calculate delay in seconds
                delay = int((next_retry_time - datetime.utcnow()).total_seconds())
                
                # Republish job with delay
                logger.info(f"Scheduling retry for job {job_id} in {delay}s")
                self.rabbitmq.publish_job(
                    job_id=str(job_id),
                    job_type=job_type.value,
                    priority=job.priority,
                    payload=payload,
                    delay=delay,
                )
                
            else:
                # Max retries exceeded, move to dead letter queue
                logger.warning(f"Job {job_id} exceeded max retries, moving to dead letter queue")
                
                job.status = JobStatus.FAILED
                
                # Get all error messages
                all_attempts = db.query(RetryAttempt).filter(
                    RetryAttempt.job_id == job_id
                ).all()
                all_errors = [attempt.error_message for attempt in all_attempts]
                all_errors.append(error_msg)
                
                # Create dead letter record
                dead_letter = DeadLetter(
                    job_id=job_id,
                    job_type=job_type,
                    payload=payload,
                    total_attempts=job.retry_count,
                    first_attempt_at=job.created_at,
                    failure_reason=error_msg,
                    all_error_messages=all_errors,
                )
                
                db.add(retry_attempt)
                db.add(dead_letter)
                db.commit()
                
                logger.info(f"Job {job_id} moved to dead letter queue")
                
        except Exception as e:
            logger.error(f"Error handling job failure: {e}")
            logger.error(traceback.format_exc())
            db.rollback()
        finally:
            db.close()
    
    def stop(self):
        """Stop the consumer."""
        logger.info("Stopping worker...")
        self.running = False
        self.rabbitmq.close()
