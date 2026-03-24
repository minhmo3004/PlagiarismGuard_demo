"""
Crawler cho Wikipedia tiếng Việt
Thu thập các bài viết ngẫu nhiên hoặc theo chuyên mục từ Wikipedia tiếng Việt bằng MediaWiki API

Tính năng:
- Thu thập bài viết ngẫu nhiên
- Thu thập theo chuyên mục (Công nghệ, Khoa học, ...)
- Làm sạch văn bản và lọc nội dung
- Giới hạn tốc độ để tôn trọng Điều khoản dịch vụ của Wikipedia

Cách sử dụng:
    from crawlers.viwiki_crawler import ViWikiCrawler
    
    crawler = ViWikiCrawler()
    docs = crawler.crawl(limit=100)                    # Bài viết ngẫu nhiên
    
    # Hoặc thu thập theo chuyên mục cụ thể
    docs = crawler.crawl_category('Khoa_học_máy_tính', limit=50)
"""
import re
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler


class ViWikiCrawler(BaseCrawler):
    """Crawler cho Wikipedia tiếng Việt"""
    
    def __init__(self, delay_seconds: float = 1.5, **kwargs):
        super().__init__(delay_seconds=delay_seconds, **kwargs)
        self.api_url = "https://vi.wikipedia.org/w/api.php"
        
        # Các chuyên mục Công nghệ & Khoa học để thu thập có chủ đích
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
        Thu thập bài viết ngẫu nhiên từ Wikipedia tiếng Việt
        
        Args:
            limit: Số lượng bài viết tối đa cần thu thập
            
        Returns:
            Danh sách tài liệu đã được định dạng chuẩn
        """
        documents = []
        
        print(f"\n🔍 Đang thu thập {limit} bài viết ngẫu nhiên từ Wikipedia tiếng Việt...")
        
        for i in range(limit):
            # Lấy bài viết ngẫu nhiên
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'random',
                'rnnamespace': 0,      # Chỉ lấy không gian chính (bài viết)
                'rnlimit': 1
            }
            
            response = self._retry_request(self.api_url, params=params)
            if not response:
                continue
                
            try:
                data = response.json()
                page_id = data['query']['random'][0]['id']
                
                # Lấy nội dung chi tiết của bài viết
                content_params = {
                    'action': 'query',
                    'format': 'json',
                    'pageids': page_id,
                    'prop': 'extracts|info',
                    'explaintext': True,           # Lấy văn bản thuần
                    'exsectionformat': 'plain'
                }
                
                content_response = self._retry_request(self.api_url, params=content_params)
                if not content_response:
                    continue
                    
                content_data = content_response.json()
                page = content_data['query']['pages'][str(page_id)]
                
                title = page.get('title', '')
                extract = page.get('extract', '')
                
                # Bỏ qua bài viết quá ngắn hoặc là bản nháp (stub)
                if len(extract) < 200:
                    continue
                
                # Làm sạch văn bản
                extract = self._clean_text(extract)
                
                # Bỏ qua nếu sau khi làm sạch vẫn quá ngắn
                if len(extract) < 150 or len(extract.split()) < 50:
                    continue
                
                # Đếm số từ (ước lượng)
                word_count = len(extract.split())
                
                doc = self.format_document(
                    title=title,
                    content=extract[:10000],           # Giới hạn 10.000 ký tự
                    author="Wikipedia Contributors",
                    university="Vietnamese Wikipedia",
                    source=f"vi.wikipedia.org/wiki/{title.replace(' ', '_')}"
                )
                doc['word_count'] = word_count
                
                documents.append(doc)
                self.docs_crawled += 1
                
                print(f"  ✅ [{i + 1}/{limit}] {title[:50]}... ({word_count} từ)")
                
                if len(documents) >= limit:
                    break
                    
            except Exception as e:
                print(f"  ⚠️  Lỗi khi xử lý bài viết: {e}")
                continue
            
            # Giới hạn tốc độ
            self._rate_limit()
        
        print(f"\n✅ Tổng số bài viết thu thập từ Wikipedia: {len(documents)}\n")
        return documents
    
    def crawl_category(self, category: str, limit: int = 100) -> List[Dict]:
        """
        Thu thập bài viết từ một chuyên mục cụ thể trên Wikipedia
        
        Args:
            category: Tên chuyên mục (ví dụ: 'Khoa_học_máy_tính')
            limit: Số lượng bài viết tối đa
            
        Returns:
            Danh sách tài liệu đã định dạng
        """
        documents = []
        
        print(f"\n🔍 Đang thu thập chuyên mục: {category} (tối đa {limit} bài)...")
        
        # Lấy danh sách trang thuộc chuyên mục
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmlimit': min(limit * 2, 500),   # Lấy dư để lọc
            'cmnamespace': 0                  # Chỉ lấy bài viết chính
        }
        
        response = self._retry_request(self.api_url, params=params)
        if not response:
            return documents
        
        try:
            data = response.json()
            pages = data['query']['categorymembers']
            
            for page in pages[:limit]:
                page_title = page['title']
                
                # Lấy nội dung bài viết
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
                
                # Bỏ qua bài quá ngắn
                if len(extract) < 500:
                    continue
                
                # Làm sạch văn bản
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
                print(f"  ✅ [{len(documents)}/{limit}] {page_title[:50]}... ({word_count} từ)")
                
                if len(documents) >= limit:
                    break
                
                self._rate_limit()
                
        except Exception as e:
            print(f"  ❌ Lỗi khi thu thập chuyên mục: {e}")
        
        print(f"\n✅ Tổng số bài viết thu thập từ {category}: {len(documents)}\n")
        return documents
    
    def crawl_tech_categories(self, limit_per_category: int = 20) -> List[Dict]:
        """
        Thu thập bài viết từ tất cả các chuyên mục công nghệ
        
        Args:
            limit_per_category: Số bài viết tối đa cho mỗi chuyên mục
            
        Returns:
            Danh sách tất cả tài liệu từ các chuyên mục công nghệ
        """
        all_documents = []
        
        print(f"\n{'='*70}")
        print(f"🔍 ĐANG THU THẬP CÁC CHUYÊN MỤC CÔNG NGHỆ TỪ WIKIPEDIA TIẾNG VIỆT")
        print(f"{'='*70}")
        print(f"Số chuyên mục: {len(self.tech_categories)}")
        print(f"Giới hạn mỗi chuyên mục: {limit_per_category}")
        print(f"Dự kiến tổng số: ~{len(self.tech_categories) * limit_per_category}\n")
        
        for i, category in enumerate(self.tech_categories, 1):
            print(f"[{i}/{len(self.tech_categories)}] Chuyên mục: {category}")
            docs = self.crawl_category(category, limit=limit_per_category)
            all_documents.extend(docs)
        
        print(f"\n{'='*70}")
        print(f"✅ TỔNG SỐ BÀI VIẾT ĐÃ THU THẬP: {len(all_documents)}")
        print(f"{'='*70}\n")
        
        return all_documents
    
    def _clean_text(self, text: str) -> str:
        """Làm sạch văn bản Wikipedia"""
        # Xóa nhiều dòng trống liên tiếp
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Xóa tiêu đề dạng == Tiêu đề ==
        text = re.sub(r'={2,}.*?={2,}', '', text)
        # Xóa số tham chiếu [1], [2], ...
        text = re.sub(r'\[\d+\]', '', text)
        # Xóa chú thích ngôn ngữ (tiếng Anh: ...)
        text = re.sub(r'\(tiếng [^)]+\)', '', text)
        return text.strip()


if __name__ == "__main__":
    # Phần test crawler
    import sys
    
    crawler = ViWikiCrawler()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test nhanh
        print("Đang test thu thập bài viết ngẫu nhiên...")
        docs = crawler.crawl(limit=3)
        
        if docs:
            print(f"\n📊 Ví dụ một tài liệu:")
            doc = docs[0]
            print(f"Tiêu đề: {doc['title']}")
            print(f"Số từ: {doc.get('word_count', 'N/A')}")
            print(f"Xem trước nội dung: {doc['content'][:200]}...")
    else:
        print("Cách dùng: python -m crawlers.viwiki_crawler --test")
        print("Hoặc import trong script khác")