"""
FastAPI dependencies.
"""
from typing import Generator
import sys
sys.path.append('/shared')
from shared.rabbitmq_client import RabbitMQClient
from shared.redis_client import RedisClient
from .config import settings


# Global clients
_rabbitmq_client: RabbitMQClient = None
_redis_client: RedisClient = None


def get_rabbitmq() -> RabbitMQClient:
    """Get RabbitMQ client dependency.
    
    Returns:
        RabbitMQ client instance
    """
    global _rabbitmq_client
    if _rabbitmq_client is None:
        _rabbitmq_client = RabbitMQClient(settings.rabbitmq_url)
        _rabbitmq_client.connect()
    return _rabbitmq_client


def get_redis() -> RedisClient:
    """Get Redis client dependency.
    
    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient(settings.redis_url)
        _redis_client.connect()
    return _redis_client
