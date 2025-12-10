"""
Redis client utilities.
"""
import json
import logging
from typing import Optional, Any
import redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for caching and real-time data."""
    
    def __init__(self, redis_url: str):
        """Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
    
    def connect(self):
        """Establish connection to Redis."""
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def set_job_status(self, job_id: str, status: str, ttl: int = 3600):
        """Cache job status.
        
        Args:
            job_id: Job identifier
            status: Job status
            ttl: Time to live in seconds
        """
        if not self.client:
            self.connect()
        
        key = f"job:{job_id}:status"
        self.client.setex(key, ttl, status)
    
    def get_job_status(self, job_id: str) -> Optional[str]:
        """Get cached job status.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status or None if not cached
        """
        if not self.client:
            self.connect()
        
        key = f"job:{job_id}:status"
        return self.client.get(key)
    
    def set_worker_heartbeat(self, worker_id: str, ttl: int = 60):
        """Set worker heartbeat.
        
        Args:
            worker_id: Worker identifier
            ttl: Time to live in seconds
        """
        if not self.client:
            self.connect()
        
        key = f"worker:{worker_id}:heartbeat"
        self.client.setex(key, ttl, "alive")
    
    def get_active_workers(self) -> list[str]:
        """Get list of active workers.
        
        Returns:
            List of active worker IDs
        """
        if not self.client:
            self.connect()
        
        pattern = "worker:*:heartbeat"
        keys = self.client.keys(pattern)
        return [key.split(':')[1] for key in keys]
    
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment a counter.
        
        Args:
            key: Counter key
            amount: Amount to increment
            
        Returns:
            New counter value
        """
        if not self.client:
            self.connect()
        
        return self.client.incrby(key, amount)
    
    def get_counter(self, key: str) -> int:
        """Get counter value.
        
        Args:
            key: Counter key
            
        Returns:
            Counter value
        """
        if not self.client:
            self.connect()
        
        value = self.client.get(key)
        return int(value) if value else 0
    
    def set_json(self, key: str, data: Any, ttl: Optional[int] = None):
        """Store JSON data.
        
        Args:
            key: Redis key
            data: Data to store
            ttl: Time to live in seconds
        """
        if not self.client:
            self.connect()
        
        json_data = json.dumps(data)
        if ttl:
            self.client.setex(key, ttl, json_data)
        else:
            self.client.set(key, json_data)
    
    def get_json(self, key: str) -> Optional[Any]:
        """Get JSON data.
        
        Args:
            key: Redis key
            
        Returns:
            Parsed JSON data or None
        """
        if not self.client:
            self.connect()
        
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    def delete(self, key: str):
        """Delete a key.
        
        Args:
            key: Redis key
        """
        if not self.client:
            self.connect()
        
        self.client.delete(key)
    
    def close(self):
        """Close the connection."""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")
