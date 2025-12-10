"""
Worker main entry point.
"""
import logging
import signal
import sys
import time
sys.path.append('/shared')
from shared.redis_client import RedisClient

from worker.consumer import JobConsumer
from worker.config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Global consumer instance
consumer = None
redis_client = None


def signal_handler(signum, frame):
    """Handle shutdown signals.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    
    if consumer:
        consumer.stop()
    
    if redis_client:
        redis_client.close()
    
    sys.exit(0)


def send_heartbeat():
    """Send worker heartbeat to Redis."""
    global redis_client
    
    if not redis_client:
        redis_client = RedisClient(settings.redis_url)
        redis_client.connect()
    
    try:
        redis_client.set_worker_heartbeat(settings.worker_id, ttl=60)
    except Exception as e:
        logger.error(f"Failed to send heartbeat: {e}")


def main():
    """Main worker function."""
    global consumer
    
    logger.info(f"Starting worker {settings.worker_id}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"RabbitMQ: {settings.rabbitmq_url}")
    logger.info(f"Redis: {settings.redis_url}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Send initial heartbeat
    send_heartbeat()
    
    # Create and start consumer
    consumer = JobConsumer()
    
    try:
        # Start heartbeat in background (simplified - in production use threading)
        consumer.start()
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise


if __name__ == "__main__":
    main()
