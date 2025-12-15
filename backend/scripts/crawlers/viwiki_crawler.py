"""
Vietnamese Wikipedia Crawler
Crawls random Vietnamese Wikipedia articles
"""
import re
from typing import List, Dict
from .base_crawler import BaseCrawler


class ViWikiCrawler(BaseCrawler):
    """Crawler for Vietnamese Wikipedia"""
    
    def __init__(self, **kwargs):
        super().__init__(delay_seconds=1.0, **kwargs)
        self.api_url = "https://vi.wikipedia.org/w/api.php"
        
    def crawl(self, limit: int = 100) -> List[Dict]:
        """
        Crawl random Vietnamese Wikipedia articles
        
        Args:
            limit: Number of articles to crawl
            
        Returns:
            List of formatted documents
        """
        documents = []
        
        print(f"\n🔍 Crawling Vietnamese Wikipedia for {limit} articles...")
        
        for i in range(limit):
            # Get random article
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'random',
                'rnnamespace': 0,  # Main namespace only
                'rnlimit': 1
            }
            
            response = self._retry_request(self.api_url, params=params)
            if not response:
                continue
                
            try:
                data = response.json()
                page_id = data['query']['random'][0]['id']
                
                # Get article content
                content_params = {
                    'action': 'query',
                    'format': 'json',
                    'pageids': page_id,
                    'prop': 'extracts|info',
                    'explaintext': True,
                    'exsectionformat': 'plain'
                }
                
                content_response = self._retry_request(self.api_url, params=content_params)
                if not content_response:
                    continue
                    
                content_data = content_response.json()
                page = content_data['query']['pages'][str(page_id)]
                
                title = page.get('title', '')
                extract = page.get('extract', '')
                
                # Filter out short articles or stubs
                if len(extract) < 500:  # Skip very short articles
                    continue
                
                # Clean text
                extract = self._clean_text(extract)
                
                doc = self.format_document(
                    title=title,
                    content=extract[:5000],  # Limit to 5000 chars
                    author="Wikipedia Contributors",
                    university="Vietnamese Wikipedia",
                    source="vi.wikipedia.org"
                )
                
                documents.append(doc)
                self.docs_crawled += 1
                
                if (i + 1) % 50 == 0:
                    print(f"  Progress: {i + 1}/{limit} articles")
                    
            except Exception as e:
                print(f"  ⚠️  Error processing article: {e}")
                continue
            
            # Rate limit
            self._rate_limit()
        
        print(f"\n✅ Total crawled from Wikipedia: {len(documents)} articles\n")
        return documents
    
    def _clean_text(self, text: str) -> str:
        """Clean Wikipedia text"""
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove == headers ==
        text = re.sub(r'={2,}.*?={2,}', '', text)
        return text.strip()


if __name__ == "__main__":
    # Test crawler
    crawler = ViWikiCrawler()
    docs = crawler.crawl(limit=5)
    
    print(f"\n📊 Sample document:")
    if docs:
        doc = docs[0]
        print(f"Title: {doc['title']}")
        print(f"Content preview: {doc['content'][:200]}...")
        print(f"Content length: {len(doc['content'])} chars")
