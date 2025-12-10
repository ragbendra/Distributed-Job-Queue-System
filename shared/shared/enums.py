"""
Shared enums for job queue system.
"""
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    """Job priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class JobType(str, Enum):
    """Supported job types."""
    SEND_EMAIL = "send_email"
    PROCESS_VIDEO = "process_video"
    SCRAPE_WEBSITE = "scrape_website"


# Queue names for RabbitMQ
QUEUE_NAMES = {
    JobPriority.HIGH: "jobs.high",
    JobPriority.MEDIUM: "jobs.medium",
    JobPriority.LOW: "jobs.low",
}

# Dead letter exchange and queue
DEAD_LETTER_EXCHANGE = "dlx"
DEAD_LETTER_QUEUE = "jobs.dead_letter"

# Retry configuration by job type
RETRY_CONFIG = {
    JobType.SEND_EMAIL: {
        "max_retries": 3,
        "base_delay": 2,  # seconds
        "max_delay": 300,  # 5 minutes
    },
    JobType.PROCESS_VIDEO: {
        "max_retries": 5,
        "base_delay": 5,
        "max_delay": 3600,  # 1 hour
    },
    JobType.SCRAPE_WEBSITE: {
        "max_retries": 3,
        "base_delay": 10,
        "max_delay": 600,  # 10 minutes
    },
}
