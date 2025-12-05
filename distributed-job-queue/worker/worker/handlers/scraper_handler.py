"""
Website scraping job handler.
"""
import time
import logging
from typing import Dict, Any
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScraperHandler:
    """Handler for website scraping."""
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute website scraping job.
        
        Args:
            payload: Job payload with 'url', optional 'selector'
            
        Returns:
            Result with scraped data
            
        Raises:
            ValueError: If payload is invalid
            Exception: If scraping fails
        """
        # Validate payload
        if 'url' not in payload:
            raise ValueError("Missing required field: url")
        
        url = payload['url']
        selector = payload.get('selector', 'title')  # Default to title
        timeout = payload.get('timeout', 10)
        
        logger.info(f"Scraping website: {url}")
        
        try:
            # Make HTTP request
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'JobQueue-Scraper/1.0'
            })
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract data based on selector
            if selector == 'title':
                data = soup.title.string if soup.title else 'No title found'
            else:
                elements = soup.select(selector)
                data = [elem.get_text(strip=True) for elem in elements]
            
            logger.info(f"Successfully scraped {url}")
            
            return {
                'status': 'scraped',
                'url': url,
                'data': data,
                'status_code': response.status_code,
                'scraped_at': time.time(),
            }
            
        except requests.RequestException as e:
            error_msg = f"Failed to scrape {url}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error parsing {url}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
