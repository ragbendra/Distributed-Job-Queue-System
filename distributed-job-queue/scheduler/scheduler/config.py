"""
Scheduler configuration.
"""
from pydantic_settings import BaseSettings


class SchedulerSettings(BaseSettings):
    """Scheduler settings."""
    
    # Database
    database_url: str = "postgresql://jobqueue:jobqueue123@localhost:5432/jobqueue_db"
    
    # RabbitMQ
    rabbitmq_url: str = "amqp://admin:admin123@localhost:5672/"
    
    # Scheduler
    scheduler_poll_interval: int = 60  # seconds
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = SchedulerSettings()
