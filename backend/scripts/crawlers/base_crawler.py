"""
Base Crawler Class
Provides common functionality for all crawlers
"""
import time
import random
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class BaseCrawler(ABC):
    """Base class for all crawlers"""
    
    def __init__(
        self,
        delay_seconds: float = 2.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self._get_random_user_agent()
        })
        self.docs_crawled = 0
        
    def _get_random_user_agent(self) -> str:
        """Get random user agent to avoid blocking"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(user_agents)
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        time.sleep(self.delay_seconds + random.uniform(0, 0.5))
    
    def _retry_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"❌ Failed after {self.max_retries} attempts: {url}")
                    print(f"   Error: {e}")
                    return None
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️  Retry {attempt + 1}/{self.max_retries} after {wait_time:.1f}s")
                time.sleep(wait_time)
        return None
    
    @abstractmethod
    def crawl(self, limit: int = 100) -> List[Dict]:
        """
        Crawl documents from source
        
        Returns:
            List of dicts with keys: title, content, author, year, source
        """
        pass
    
    def format_document(
        self,
        title: str,
        content: str,
        author: str = "Unknown",
        year: Optional[int] = None,
        university: str = "Unknown",
        source: str = "Unknown"
    ) -> Dict:
        """Format document in standard format"""
        return {
            "title": title.strip(),
            "content": content.strip(),
            "author": author.strip(),
            "year": year or datetime.now().year,
            "university": university.strip(),
            "source": source,
            "crawled_at": datetime.now().isoformat()
        }
