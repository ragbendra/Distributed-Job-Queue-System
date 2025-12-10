"""
Base handler class for job execution.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    """Base class for job handlers."""
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the job.
        
        Args:
            payload: Job payload data
            
        Returns:
            Result dictionary
            
        Raises:
            Exception: If job execution fails
        """
        pass
    
    def validate_payload(self, payload: Dict[str, Any], required_fields: list[str]):
        """Validate payload has required fields.
        
        Args:
            payload: Job payload
            required_fields: List of required field names
            
        Raises:
            ValueError: If required fields are missing
        """
        missing_fields = [field for field in required_fields if field not in payload]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
