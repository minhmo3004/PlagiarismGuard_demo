"""
Lớp cơ sở (Base Class) cho tất cả các Crawler
Cung cấp các chức năng chung cho mọi trình thu thập dữ liệu
"""
import time
import random
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class BaseCrawler(ABC):
    """Lớp cơ sở cho tất cả các crawler"""
    
    def __init__(
        self,
        delay_seconds: float = 2.0,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.delay_seconds = delay_seconds      # Thời gian nghỉ giữa các request
        self.max_retries = max_retries          # Số lần thử lại tối đa
        self.timeout = timeout                  # Thời gian timeout cho mỗi request
        self.session = requests.Session()
        
        # Sử dụng User-Agent chuyên nghiệp để tránh bị chặn
        self.session.headers.update({
            'User-Agent': 'PlagiarismGuard/2.0 (Educational Research; Contact: github.com/plagiarismguard) python-requests/2.31'
        })
        
        self.docs_crawled = 0                   # Đếm số tài liệu đã thu thập
    
    def _get_random_user_agent(self) -> str:
        """Trả về User-Agent ngẫu nhiên để tránh bị chặn"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        return random.choice(user_agents)
    
    def _rate_limit(self):
        """Áp dụng giới hạn tốc độ giữa các request"""
        time.sleep(self.delay_seconds + random.uniform(0, 0.5))
    
    def _retry_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Thực hiện request với cơ chế thử lại (retry)"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"❌ Thất bại sau {self.max_retries} lần thử: {url}")
                    print(f"   Lỗi: {e}")
                    return None
                
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️  Thử lại lần {attempt + 1}/{self.max_retries} sau {wait_time:.1f}s")
                time.sleep(wait_time)
        return None
    
    @abstractmethod
    def crawl(self, limit: int = 100) -> List[Dict]:
        """
        Thu thập tài liệu từ nguồn dữ liệu
        
        Returns:
            Danh sách các dict với các trường: title, content, author, year, source
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
        """Định dạng tài liệu theo chuẩn thống nhất"""
        return {
            "title": title.strip(),
            "content": content.strip(),
            "author": author.strip(),
            "year": year or datetime.now().year,
            "university": university.strip(),
            "source": source,
            "crawled_at": datetime.now().isoformat()
        }