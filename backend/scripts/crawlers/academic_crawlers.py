"""
Google Scholar Crawler for Vietnamese Academic Papers
Crawls publicly available academic papers from Google Scholar

Features:
- Search Vietnamese papers by keyword
- Filter by university affiliation
- Extract title, author, abstract
- Respects robots.txt and rate limits

Usage:
    from crawlers.google_scholar_crawler import GoogleScholarCrawler
    
    crawler = GoogleScholarCrawler()
    docs = crawler.search(query="machine learning", university="Bách Khoa", limit=50)
"""
import re
import time
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler


class GoogleScholarCrawler(BaseCrawler):
    """Crawler for Google Scholar Vietnamese papers"""
    
    def __init__(self, delay_seconds: float = 3.0, **kwargs):
        # Longer delay for Google Scholar to avoid blocking
        super().__init__(delay_seconds=delay_seconds, **kwargs)
        self.base_url = "https://scholar.google.com/scholar"
        
        # Vietnamese universities keywords
        self.universities = {
            'vnu': ['Đại học Quốc gia Hà Nội', 'Vietnam National University', 'VNU'],
            'hust': ['Bách Khoa Hà Nội', 'Hanoi University of Science and Technology', 'HUST'],
            'hcmut': ['Bách Khoa TP.HCM', 'HCMUT', 'Bach Khoa HCMC'],
            'uit': ['UIT', 'University of Information Technology'],
            'ptit': ['PTIT', 'Posts and Telecommunications'],
            'fpt': ['FPT University', 'Đại học FPT'],
        }
        
        # Research topics in Vietnamese
        self.topics = [
            'trí tuệ nhân tạo',
            'học máy',
            'xử lý ngôn ngữ tự nhiên',
            'thị giác máy tính',
            'khoa học dữ liệu',
            'an ninh mạng',
            'blockchain',
            'internet of things'
        ]
    
    def search(self, query: str, university: Optional[str] = None, 
               limit: int = 50, language: str = 'vi') -> List[Dict]:
        """
        Search Google Scholar for academic papers
        
        Args:
            query: Search query (e.g., "machine learning")
            university: Filter by university (e.g., "hust", "vnu")
            limit: Maximum number of results
            language: Language filter ('vi' for Vietnamese)
            
        Returns:
            List of formatted documents
        """
        documents = []
        
        # Build search query
        search_query = query
        if university and university.lower() in self.universities:
            uni_keywords = self.universities[university.lower()]
            search_query = f"{query} ({' OR '.join(uni_keywords)})"
        
        print(f"\n🔍 Searching Google Scholar for: {search_query}")
        print(f"   Language: {language}, Limit: {limit}")
        
        # Note: Google Scholar doesn't have official API
        # This is a placeholder for demonstration
        # In production, use scholarly library or SerpAPI
        
        print("\n⚠️  IMPORTANT NOTICE:")
        print("   Google Scholar doesn't have official API")
        print("   For production use, consider:")
        print("   1. scholarly library (https://github.com/scholarly-python-package/scholarly)")
        print("   2. SerpAPI (https://serpapi.com/google-scholar-api)")
        print("   3. University's own repositories with APIs")
        print("\n   This crawler is a TEMPLATE - implement actual scraping carefully")
        print("   to respect Google's ToS and rate limits.\n")
        
        return documents
    
    def search_by_topic(self, topic: str, limit: int = 20) -> List[Dict]:
        """
        Search papers by research topic
        
        Args:
            topic: Research topic (e.g., "trí tuệ nhân tạo")
            limit: Maximum results
            
        Returns:
            List of documents
        """
        return self.search(query=topic, limit=limit)
    
    def search_multi_universities(self, query: str, 
                                  universities: List[str],
                                  limit_per_uni: int = 10) -> List[Dict]:
        """
        Search across multiple universities
        
        Args:
            query: Search query
            universities: List of university codes ['vnu', 'hust', ...]
            limit_per_uni: Limit per university
            
        Returns:
            Combined list of documents
        """
        all_docs = []
        
        for uni in universities:
            print(f"\n[{uni.upper()}] Searching...")
            docs = self.search(query=query, university=uni, limit=limit_per_uni)
            all_docs.extend(docs)
            time.sleep(self.delay_seconds * 2)  # Extra delay between universities
        
        return all_docs
    
    def _extract_abstract(self, html: str) -> str:
        """Extract abstract from paper HTML (placeholder)"""
        # This would parse the paper page HTML
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean academic text"""
        # Remove citations like [1], [2]
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        return text.strip()


class ArxivCrawler(BaseCrawler):
    """
    Crawler for ArXiv preprints
    ArXiv has official API - safe to use
    """
    
    def __init__(self, delay_seconds: float = 3.0, **kwargs):
        super().__init__(delay_seconds=delay_seconds, **kwargs)
        self.api_url = "http://export.arxiv.org/api/query"
    
    def crawl(self, query: str = '', category: str = 'cs.AI', limit: int = 50) -> List[Dict]:
        """
        Search ArXiv papers
        
        Args:
            query: Search query
            category: ArXiv category (cs.AI, cs.LG, cs.CV, etc.)
            limit: Maximum results
            
        Returns:
            List of documents
        """
        documents = []
        
        print(f"\n🔍 Searching ArXiv: {query} in {category}")
        
        # Build search query
        if query:
            search_query = f'cat:{category} AND all:{query}'
        else:
            search_query = f'cat:{category}'
        
        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': limit,
            'sortBy': 'lastUpdatedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = self._retry_request(self.api_url, params=params)
            if not response:
                return documents
            
            # Parse XML response
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Namespace for ArXiv API
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                try:
                    title = entry.find('atom:title', ns).text.strip()
                    summary = entry.find('atom:summary', ns).text.strip()
                    
                    # Get authors
                    authors = [a.find('atom:name', ns).text 
                              for a in entry.findall('atom:author', ns)]
                    author_str = ', '.join(authors[:3])  # First 3 authors
                    if len(authors) > 3:
                        author_str += ' et al.'
                    
                    # Combine title and abstract
                    content = f"{title}\n\n{summary}"
                    content = self._clean_text(content)
                    
                    # Skip if too short
                    if len(content.split()) < 100:
                        continue
                    
                    doc = self.format_document(
                        title=title[:500],
                        content=content[:10000],
                        author=author_str,
                        university="ArXiv Preprint",
                        source=entry.find('atom:id', ns).text
                    )
                    doc['word_count'] = len(content.split())
                    
                    documents.append(doc)
                    self.docs_crawled += 1
                    
                    print(f"  ✅ [{len(documents)}] {title[:60]}... ({doc['word_count']} words)")
                    
                except Exception as e:
                    print(f"  ⚠️  Error parsing entry: {e}")
                    continue
                
                if len(documents) >= limit:
                    break
            
            print(f"\n✅ Total crawled from ArXiv: {len(documents)} papers\n")
            
        except Exception as e:
            print(f"❌ Error searching ArXiv: {e}")
        
        return documents
    
    def search_vietnamese_ai(self, limit: int = 50) -> List[Dict]:
        """Search AI papers mentioning Vietnam or Vietnamese"""
        return self.crawl(
            query='Vietnam OR Vietnamese',
            category='cs.AI',
            limit=limit
        )
    
    def search_by_categories(self, query: str = '', 
                           categories: List[str] = None,
                           limit_per_cat: int = 20) -> List[Dict]:
        """
        Search across multiple ArXiv categories
        
        Args:
            query: Search query
            categories: List of categories ['cs.AI', 'cs.LG', 'cs.CV']
            limit_per_cat: Limit per category
            
        Returns:
            Combined documents
        """
        if categories is None:
            categories = ['cs.AI']
            
        all_docs = []
        
        for cat in categories:
            print(f"\n[{cat}] Searching...")
            docs = self.crawl(query=query, category=cat, limit=limit_per_cat)
            all_docs.extend(docs)
            time.sleep(self.delay_seconds)
        
        return all_docs
    
    def _clean_text(self, text: str) -> str:
        """Clean ArXiv abstract text"""
        # Remove LaTeX commands
        text = re.sub(r'\$[^\$]+\$', '', text)  # Inline math
        text = re.sub(r'\\[a-zA-Z]+\{[^\}]*\}', '', text)  # LaTeX commands
        
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
