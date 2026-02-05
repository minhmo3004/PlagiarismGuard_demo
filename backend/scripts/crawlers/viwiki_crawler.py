"""
Vietnamese Wikipedia Crawler
Crawls random Vietnamese Wikipedia articles using MediaWiki API

Features:
- Random article crawling
- Category-based crawling (Technology, Science, etc.)
- Text cleaning and filtering
- Rate limiting to respect Wikipedia ToS

Usage:
    from crawlers.viwiki_crawler import ViWikiCrawler
    
    crawler = ViWikiCrawler()
    docs = crawler.crawl(limit=100)  # Random articles
    
    # Or crawl from specific category
    docs = crawler.crawl_category('Khoa_học_máy_tính', limit=50)
"""
import re
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler


class ViWikiCrawler(BaseCrawler):
    """Crawler for Vietnamese Wikipedia"""
    
    def __init__(self, delay_seconds: float = 1.5, **kwargs):
        super().__init__(delay_seconds=delay_seconds, **kwargs)
        self.api_url = "https://vi.wikipedia.org/w/api.php"
        
        # Technology & Science categories for targeted crawling
        self.tech_categories = [
            'Khoa_học_máy_tính',
            'Trí_tuệ_nhân_tạo',
            'Công_nghệ_thông_tin',
            'Lập_trình_máy_tính',
            'Khoa_học_dữ_liệu',
            'Mạng_máy_tính',
            'Phần_mềm',
            'Cơ_sở_dữ_liệu'
        ]
        
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
                if len(extract) < 200:  # Skip very short articles
                    continue
                
                # Clean text
                extract = self._clean_text(extract)
                
                # Skip if too short after cleaning or not enough words
                if len(extract) < 150 or len(extract.split()) < 50:
                    continue
                
                # Count words (rough estimate)
                word_count = len(extract.split())
                
                doc = self.format_document(
                    title=title,
                    content=extract[:10000],  # Limit to 10000 chars
                    author="Wikipedia Contributors",
                    university="Vietnamese Wikipedia",
                    source=f"vi.wikipedia.org/wiki/{title.replace(' ', '_')}"
                )
                doc['word_count'] = word_count
                
                documents.append(doc)
                self.docs_crawled += 1
                
                print(f"  ✅ [{i + 1}/{limit}] {title[:50]}... ({word_count} words)")
                
                if len(documents) >= limit:
                    break
                    
            except Exception as e:
                print(f"  ⚠️  Error processing article: {e}")
                continue
            
            # Rate limit
            self._rate_limit()
        
        print(f"\n✅ Total crawled from Wikipedia: {len(documents)} articles\n")
        return documents
    
    def crawl_category(self, category: str, limit: int = 100) -> List[Dict]:
        """
        Crawl articles from a specific Wikipedia category
        
        Args:
            category: Category name (e.g., 'Khoa_học_máy_tính')
            limit: Number of articles to crawl
            
        Returns:
            List of formatted documents
        """
        documents = []
        
        print(f"\n🔍 Crawling category: {category} ({limit} articles max)...")
        
        # Get pages in category
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': min(limit * 2, 500),  # Get more to filter
            'cmnamespace': 0  # Main namespace only
        }
        
        response = self._retry_request(self.api_url, params=params)
        if not response:
            return documents
        
        try:
            data = response.json()
            pages = data['query']['categorymembers']
            
            for page in pages[:limit]:
                page_title = page['title']
                
                # Get article content
                content_params = {
                    'action': 'query',
                    'format': 'json',
                    'titles': page_title,
                    'prop': 'extracts',
                    'explaintext': True,
                    'exsectionformat': 'plain'
                }
                
                content_response = self._retry_request(self.api_url, params=content_params)
                if not content_response:
                    continue
                
                content_data = content_response.json()
                page_data = list(content_data['query']['pages'].values())[0]
                
                extract = page_data.get('extract', '')
                
                # Filter out short articles
                if len(extract) < 500:
                    continue
                
                # Clean text
                extract = self._clean_text(extract)
                word_count = len(extract.split())
                
                doc = self.format_document(
                    title=page_title,
                    content=extract[:10000],
                    author="Wikipedia Contributors",
                    university="Vietnamese Wikipedia",
                    source=f"vi.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                )
                doc['word_count'] = word_count
                doc['category'] = category
                
                documents.append(doc)
                print(f"  ✅ [{len(documents)}/{limit}] {page_title[:50]}... ({word_count} words)")
                
                if len(documents) >= limit:
                    break
                
                self._rate_limit()
                
        except Exception as e:
            print(f"  ❌ Error crawling category: {e}")
        
        print(f"\n✅ Total crawled from {category}: {len(documents)} articles\n")
        return documents
    
    def crawl_tech_categories(self, limit_per_category: int = 20) -> List[Dict]:
        """
        Crawl articles from all technology-related categories
        
        Args:
            limit_per_category: Number of articles per category
            
        Returns:
            List of all documents from tech categories
        """
        all_documents = []
        
        print(f"\n{'='*70}")
        print(f"🔍 CRAWLING TECH CATEGORIES FROM VIETNAMESE WIKIPEDIA")
        print(f"{'='*70}")
        print(f"Categories: {len(self.tech_categories)}")
        print(f"Limit per category: {limit_per_category}")
        print(f"Expected total: ~{len(self.tech_categories) * limit_per_category}\n")
        
        for i, category in enumerate(self.tech_categories, 1):
            print(f"[{i}/{len(self.tech_categories)}] Category: {category}")
            docs = self.crawl_category(category, limit=limit_per_category)
            all_documents.extend(docs)
        
        print(f"\n{'='*70}")
        print(f"✅ TOTAL CRAWLED: {len(all_documents)} articles")
        print(f"{'='*70}\n")
        
        return all_documents
    
    def _clean_text(self, text: str) -> str:
        """Clean Wikipedia text"""
        # Remove multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove == headers ==
        text = re.sub(r'={2,}.*?={2,}', '', text)
        # Remove citation markers [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        # Remove (tiếng ...: ...) language references
        text = re.sub(r'\(tiếng [^)]+\)', '', text)
        return text.strip()


if __name__ == "__main__":
    # Test crawler
    import sys
    
    crawler = ViWikiCrawler()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Quick test
        print("Testing random article crawl...")
        docs = crawler.crawl(limit=3)
        
        if docs:
            print(f"\n📊 Sample document:")
            doc = docs[0]
            print(f"Title: {doc['title']}")
            print(f"Words: {doc.get('word_count', 'N/A')}")
            print(f"Content preview: {doc['content'][:200]}...")
    else:
        # Full crawl
        print("Use: python -m crawlers.viwiki_crawler --test")
        print("Or import in another script")
