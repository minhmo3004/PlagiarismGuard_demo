"""
Gói chứa các crawler (trình thu thập dữ liệu)
Dùng để thu thập tài liệu học thuật và corpus tiếng Việt
"""
from .base_crawler import BaseCrawler
from .academic_crawlers import ArxivCrawler
from .viwiki_crawler import ViWikiCrawler

__all__ = ['BaseCrawler', 'ArxivCrawler', 'ViWikiCrawler']