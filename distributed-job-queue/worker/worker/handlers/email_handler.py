"""
Email sending job handler (simulated).
"""
import time
import random
import logging
from typing import Dict, Any

from worker.handlers.base import BaseHandler

logger = logging.getLogger(__name__)


class EmailHandler(BaseHandler):
    """Handler for sending emails (simulated)."""
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email sending job.
        
        Args:
            payload: Job payload with 'to', 'subject', 'body'
            
        Returns:
            Result with email details
            
        Raises:
            ValueError: If payload is invalid
            Exception: If email sending fails (simulated)
        """
        # Validate payload
        self.validate_payload(payload, ['to', 'subject', 'body'])
        
        to_email = payload['to']
        subject = payload['subject']
        body = payload['body']
        
        logger.info(f"Sending email to {to_email} with subject '{subject}'")
        
        # Simulate email sending with random failure for testing
        failure_rate = payload.get('failure_rate', 0.0)  # For testing retries
        
        if random.random() < failure_rate:
            error_msg = f"Failed to send email to {to_email}: SMTP connection timeout"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Simulate processing time
        time.sleep(random.uniform(0.5, 2.0))
        
        logger.info(f"Successfully sent email to {to_email}")
        
        return {
            'status': 'sent',
            'to': to_email,
            'subject': subject,
            'sent_at': time.time(),
        }
