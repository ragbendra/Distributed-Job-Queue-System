"""
Worker configuration.
"""
import os
from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Worker settings."""
    
    # Database
    database_url: str = "postgresql://jobqueue:jobqueue123@localhost:5432/jobqueue_db"
    
    # RabbitMQ
    rabbitmq_url: str = "amqp://admin:admin123@localhost:5672/"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Worker
    worker_id: str = os.getenv("WORKER_ID", "worker-1")
    worker_concurrency: int = 10
    worker_prefetch_count: int = 5
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = WorkerSettings()
