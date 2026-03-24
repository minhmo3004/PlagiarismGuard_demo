"""
Crawler cho các bài báo học thuật từ Google Scholar (tập trung vào tài liệu tiếng Việt)
Thu thập các bài báo học thuật công khai từ Google Scholar

Tính năng:
- Tìm kiếm bài báo tiếng Việt theo từ khóa
- Lọc theo trường đại học
- Trích xuất tiêu đề, tác giả, tóm tắt
- Tôn trọng robots.txt và giới hạn tốc độ

Cách sử dụng:
    from crawlers.academic_crawlers import GoogleScholarCrawler
    
    crawler = GoogleScholarCrawler()
    docs = crawler.search(query="machine learning", university="Bách Khoa", limit=50)
"""
import re
import time
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler


class GoogleScholarCrawler(BaseCrawler):
    """Crawler cho bài báo trên Google Scholar (tập trung vào tài liệu Việt Nam)"""
    
    def __init__(self, delay_seconds: float = 3.0, **kwargs):
        # Tăng thời gian delay để tránh bị Google chặn
        super().__init__(delay_seconds=delay_seconds, **kwargs)
        self.base_url = "https://scholar.google.com/scholar"
        
        # Từ khóa các trường đại học Việt Nam
        self.universities = {
            'vnu': ['Đại học Quốc gia Hà Nội', 'Vietnam National University', 'VNU'],
            'hust': ['Bách Khoa Hà Nội', 'Hanoi University of Science and Technology', 'HUST'],
            'hcmut': ['Bách Khoa TP.HCM', 'HCMUT', 'Bach Khoa HCMC'],
            'uit': ['UIT', 'University of Information Technology'],
            'ptit': ['PTIT', 'Posts and Telecommunications'],
            'fpt': ['FPT University', 'Đại học FPT'],
        }
        
        # Các chủ đề nghiên cứu phổ biến bằng tiếng Việt
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
        Tìm kiếm bài báo trên Google Scholar
        
        Args:
            query: Từ khóa tìm kiếm (ví dụ: "machine learning")
            university: Lọc theo trường đại học (ví dụ: "hust", "vnu")
            limit: Số lượng kết quả tối đa
            language: Ngôn ngữ lọc ('vi' cho tiếng Việt)
            
        Returns:
            Danh sách tài liệu đã được định dạng
        """
        documents = []
        
        # Xây dựng query tìm kiếm
        search_query = query
        if university and university.lower() in self.universities:
            uni_keywords = self.universities[university.lower()]
            search_query = f"{query} ({' OR '.join(uni_keywords)})"
        
        print(f"\n🔍 Đang tìm kiếm trên Google Scholar: {search_query}")
        print(f"   Ngôn ngữ: {language}, Giới hạn: {limit}")
        
        # Lưu ý quan trọng:
        # Google Scholar KHÔNG có API chính thức
        # Đây chỉ là mẫu (template) để minh họa
        # Trong môi trường production, nên sử dụng:
        # 1. Thư viện scholarly[](https://github.com/scholarly-python-package/scholarly)
        # 2. SerpAPI[](https://serpapi.com/google-scholar-api)
        # 3. Kho lưu trữ của trường đại học có API công khai
        
        print("\n⚠️  LƯU Ý QUAN TRỌNG:")
        print("   Google Scholar không cung cấp API chính thức")
        print("   Để dùng trong production, vui lòng cân nhắc:")
        print("   1. Thư viện scholarly")
        print("   2. SerpAPI")
        print("   3. Kho lưu trữ của các trường đại học")
        print("\n   Crawler này chỉ là TEMPLATE - cần triển khai scraping cẩn thận")
        print("   để tuân thủ Điều khoản dịch vụ của Google và giới hạn tốc độ.\n")
        
        return documents
    
    def search_by_topic(self, topic: str, limit: int = 20) -> List[Dict]:
        """
        Tìm kiếm bài báo theo chủ đề nghiên cứu
        
        Args:
            topic: Chủ đề nghiên cứu (ví dụ: "trí tuệ nhân tạo")
            limit: Số lượng kết quả tối đa
            
        Returns:
            Danh sách tài liệu
        """
        return self.search(query=topic, limit=limit)
    
    def search_multi_universities(self, query: str, 
                                  universities: List[str],
                                  limit_per_uni: int = 10) -> List[Dict]:
        """
        Tìm kiếm trên nhiều trường đại học cùng lúc
        
        Args:
            query: Từ khóa tìm kiếm
            universities: Danh sách mã trường ['vnu', 'hust', ...]
            limit_per_uni: Giới hạn kết quả mỗi trường
            
        Returns:
            Danh sách tài liệu tổng hợp từ nhiều trường
        """
        all_docs = []
        
        for uni in universities:
            print(f"\n[{uni.upper()}] Đang tìm kiếm...")
            docs = self.search(query=query, university=uni, limit=limit_per_uni)
            all_docs.extend(docs)
            time.sleep(self.delay_seconds * 2)  # Delay lớn hơn giữa các trường
        
        return all_docs
    
    def _extract_abstract(self, html: str) -> str:
        """Trích xuất tóm tắt từ HTML của bài báo (placeholder)"""
        # Hàm này sẽ parse HTML của trang chi tiết bài báo
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Làm sạch văn bản học thuật"""
        # Xóa số tham chiếu [1], [2], ...
        text = re.sub(r'\[\d+\]', '', text)
        
        # Xóa khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text)
        
        # Xóa URL
        text = re.sub(r'https?://\S+', '', text)
        
        return text.strip()


class ArxivCrawler(BaseCrawler):
    """
    Crawler cho bài báo preprint trên ArXiv
    ArXiv có API chính thức - an toàn và khuyến khích sử dụng
    """
    
    def __init__(self, delay_seconds: float = 3.0, **kwargs):
        super().__init__(delay_seconds=delay_seconds, **kwargs)
        self.api_url = "http://export.arxiv.org/api/query"
    
    def crawl(self, query: str = '', category: str = 'cs.AI', limit: int = 50) -> List[Dict]:
        """
        Tìm kiếm bài báo trên ArXiv
        
        Args:
            query: Từ khóa tìm kiếm
            category: Danh mục ArXiv (cs.AI, cs.LG, cs.CV, ...)
            limit: Số lượng kết quả tối đa
            
        Returns:
            Danh sách tài liệu
        """
        documents = []
        
        print(f"\n🔍 Đang tìm kiếm trên ArXiv: {query} trong danh mục {category}")
        
        # Xây dựng query tìm kiếm
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
            
            # Phân tích XML response
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Namespace cho ArXiv API
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                try:
                    title = entry.find('atom:title', ns).text.strip()
                    summary = entry.find('atom:summary', ns).text.strip()
                    
                    # Lấy tác giả
                    authors = [a.find('atom:name', ns).text 
                              for a in entry.findall('atom:author', ns)]
                    author_str = ', '.join(authors[:3])  # Lấy 3 tác giả đầu
                    if len(authors) > 3:
                        author_str += ' et al.'
                    
                    # Kết hợp tiêu đề và tóm tắt
                    content = f"{title}\n\n{summary}"
                    content = self._clean_text(content)
                    
                    # Bỏ qua nếu nội dung quá ngắn
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
                    
                    print(f"  ✅ [{len(documents)}] {title[:60]}... ({doc['word_count']} từ)")
                    
                except Exception as e:
                    print(f"  ⚠️  Lỗi khi phân tích entry: {e}")
                    continue
                
                if len(documents) >= limit:
                    break
            
            print(f"\n✅ Tổng số bài báo thu thập từ ArXiv: {len(documents)}\n")
            
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm ArXiv: {e}")
        
        return documents
    
    def search_vietnamese_ai(self, limit: int = 50) -> List[Dict]:
        """Tìm kiếm bài báo AI có đề cập đến Việt Nam hoặc tiếng Việt"""
        return self.crawl(
            query='Vietnam OR Vietnamese',
            category='cs.AI',
            limit=limit
        )
    
    def search_by_categories(self, query: str = '', 
                           categories: List[str] = None,
                           limit_per_cat: int = 20) -> List[Dict]:
        """
        Tìm kiếm trên nhiều danh mục ArXiv cùng lúc
        
        Args:
            query: Từ khóa tìm kiếm
            categories: Danh sách danh mục ['cs.AI', 'cs.LG', 'cs.CV']
            limit_per_cat: Giới hạn mỗi danh mục
            
        Returns:
            Danh sách tài liệu tổng hợp
        """
        if categories is None:
            categories = ['cs.AI']
            
        all_docs = []
        
        for cat in categories:
            print(f"\n[{cat}] Đang tìm kiếm...")
            docs = self.crawl(query=query, category=cat, limit=limit_per_cat)
            all_docs.extend(docs)
            time.sleep(self.delay_seconds)
        
        return all_docs
    
    def _clean_text(self, text: str) -> str:
        """Làm sạch văn bản tóm tắt từ ArXiv"""
        # Xóa công thức LaTeX
        text = re.sub(r'\$[^\$]+\$', '', text)      # Công thức inline
        text = re.sub(r'\\[a-zA-Z]+\{[^\}]*\}', '', text)  # Lệnh LaTeX
        
        # Xóa nhiều dòng trống
        text = re.sub(r'\n+', '\n', text)
        
        # Xóa khoảng trắng thừa
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()