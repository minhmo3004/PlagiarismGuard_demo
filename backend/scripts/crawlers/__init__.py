"""Crawlers package"""
from .base_crawler import BaseCrawler
from .academic_crawlers import ArxivCrawler
from .viwiki_crawler import ViWikiCrawler

__all__ = ['BaseCrawler', 'ArxivCrawler', 'ViWikiCrawler']
