"""
Retry logic with exponential backoff.
"""
import random
import logging
from datetime import datetime, timedelta
from typing import Optional
import sys
sys.path.append('/shared')
from shared.enums import RETRY_CONFIG, JobType

logger = logging.getLogger(__name__)


class RetryManager:
    """Manages retry logic with exponential backoff."""
    
    @staticmethod
    def calculate_backoff(
        job_type: JobType,
        attempt_number: int,
    ) -> int:
        """Calculate backoff delay with exponential backoff and jitter.
        
        Args:
            job_type: Type of job
            attempt_number: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        config = RETRY_CONFIG.get(job_type, {
            "base_delay": 2,
            "max_delay": 300,
        })
        
        base_delay = config["base_delay"]
        max_delay = config["max_delay"]
        
        # Exponential backoff: base * (2 ^ attempt)
        delay = base_delay * (2 ** attempt_number)
        
        # Add random jitter (±20%)
        jitter = delay * 0.2 * (2 * random.random() - 1)
        delay_with_jitter = delay + jitter
        
        # Cap at max delay
        final_delay = min(delay_with_jitter, max_delay)
        
        logger.info(
            f"Calculated backoff for {job_type} attempt {attempt_number}: "
            f"{final_delay:.2f}s (base: {base_delay}s, max: {max_delay}s)"
        )
        
        return int(final_delay)
    
    @staticmethod
    def should_retry(job_type: JobType, retry_count: int, max_retries: int) -> bool:
        """Determine if job should be retried.
        
        Args:
            job_type: Type of job
            retry_count: Current retry count
            max_retries: Maximum retries allowed
            
        Returns:
            True if should retry, False otherwise
        """
        should_retry = retry_count < max_retries
        
        logger.info(
            f"Retry decision for {job_type}: "
            f"retry_count={retry_count}, max_retries={max_retries}, "
            f"should_retry={should_retry}"
        )
        
        return should_retry
    
    @staticmethod
    def calculate_next_retry_time(
        job_type: JobType,
        attempt_number: int,
    ) -> datetime:
        """Calculate next retry time.
        
        Args:
            job_type: Type of job
            attempt_number: Current attempt number
            
        Returns:
            Next retry datetime
        """
        delay_seconds = RetryManager.calculate_backoff(job_type, attempt_number)
        next_retry = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        logger.info(
            f"Next retry for {job_type} scheduled at {next_retry} "
            f"(in {delay_seconds}s)"
        )
        
        return next_retry
