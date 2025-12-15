"""
arXiv Crawler
Crawls Computer Science papers from arXiv using official API
"""
import xml.etree.ElementTree as ET
from typing import List, Dict
from .base_crawler import BaseCrawler


class ArxivCrawler(BaseCrawler):
    """Crawler for arXiv.org papers"""
    
    def __init__(self, **kwargs):
        super().__init__(delay_seconds=3.0, **kwargs)  # arXiv requires 3s delay
        self.base_url = "http://export.arxiv.org/api/query"
        
    def crawl(self, limit: int = 100) -> List[Dict]:
        """
        Crawl papers from arXiv
        
        Args:
            limit: Number of papers to crawl
            
        Returns:
            List of formatted documents
        """
        documents = []
        batch_size = 100  # arXiv max results per query
        
        # Search for CS papers (Computer Science)
        categories = ['cs.AI', 'cs.CL', 'cs.CV', 'cs.LG', 'cs.NE']
        
        print(f"\n🔍 Crawling arXiv for {limit} papers...")
        
        for start in range(0, limit, batch_size):
            current_batch = min(batch_size, limit - start)
            
            # Build query for multiple CS categories
            category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
            
            params = {
                'search_query': category_query,
                'start': start,
                'max_results': current_batch,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            print(f"  Fetching batch {start}-{start + current_batch}...")
            
            response = self._retry_request(self.base_url, params=params)
            if not response:
                continue
                
            # Parse XML response
            try:
                root = ET.fromstring(response.content)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                entries = root.findall('atom:entry', ns)
                
                for entry in entries:
                    title = entry.find('atom:title', ns)
                    summary = entry.find('atom:summary', ns)
                    authors = entry.findall('atom:author', ns)
                    published = entry.find('atom:published', ns)
                    
                    if title is not None and summary is not None:
                        # Get first author
                        author_name = "Unknown"
                        if authors:
                            author_elem = authors[0].find('atom:name', ns)
                            if author_elem is not None:
                                author_name = author_elem.text
                        
                        # Extract year
                        year = None
                        if published is not None:
                            year = int(published.text[:4])
                        
                        # Combine title + abstract as content
                        content = f"{title.text.strip()}\n\n{summary.text.strip()}"
                        
                        doc = self.format_document(
                            title=title.text,
                            content=content,
                            author=author_name,
                            year=year,
                            university="arXiv",
                            source="arXiv"
                        )
                        
                        documents.append(doc)
                        self.docs_crawled += 1
                        
                print(f"  ✅ Got {len(entries)} papers from this batch")
                
            except Exception as e:
                print(f"  ❌ Error parsing XML: {e}")
                continue
            
            # Rate limit between batches
            if start + current_batch < limit:
                self._rate_limit()
        
        print(f"\n✅ Total crawled from arXiv: {len(documents)} papers\n")
        return documents


if __name__ == "__main__":
    # Test crawler
    crawler = ArxivCrawler()
    docs = crawler.crawl(limit=10)
    
    print(f"\n📊 Sample document:")
    if docs:
        doc = docs[0]
        print(f"Title: {doc['title'][:80]}...")
        print(f"Author: {doc['author']}")
        print(f"Year: {doc['year']}")
        print(f"Content length: {len(doc['content'])} chars")
