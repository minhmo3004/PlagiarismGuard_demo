"""
Seed Corpus Script
Tạo 20 tài liệu mẫu vào Redis để test
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import redis
import uuid
from datetime import datetime

# Import từ app modules để đảm bảo consistent với checker
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.preprocessing.text_normalizer import normalize_text
from app.services.algorithm.shingling import create_shingles
from app.services.algorithm.minhash import create_minhash_signature
from app.config import settings


# 20 tài liệu mẫu tiếng Việt
SAMPLE_DOCUMENTS = [
    {
        "title": "Ứng dụng trí tuệ nhân tạo trong y tế",
        "author": "Nguyễn Văn An",
        "university": "ĐHQG TP.HCM",
        "year": 2023,
        "content": """
        Trí tuệ nhân tạo đang được ứng dụng rộng rãi trong lĩnh vực y tế hiện đại.
        Các hệ thống AI có thể hỗ trợ chẩn đoán bệnh từ hình ảnh y khoa như X-quang và MRI.
        Machine learning giúp phân tích dữ liệu bệnh nhân để dự đoán nguy cơ mắc bệnh.
        Deep learning được sử dụng để phát hiện ung thư từ hình ảnh mô bệnh học.
        Chatbot AI hỗ trợ tư vấn sức khỏe và đặt lịch khám bệnh trực tuyến.
        """
    },
    {
        "title": "Blockchain trong thanh toán điện tử",
        "author": "Trần Thị Bình",
        "university": "ĐH Bách Khoa HCM",
        "year": 2023,
        "content": """
        Công nghệ blockchain đang thay đổi cách thức thanh toán điện tử trên toàn cầu.
        Bitcoin và Ethereum là hai đồng tiền điện tử phổ biến nhất hiện nay.
        Smart contract cho phép tự động hóa các giao dịch tài chính phức tạp.
        Tính phi tập trung của blockchain giúp giảm chi phí trung gian trong thanh toán.
        Các ngân hàng đang nghiên cứu ứng dụng blockchain vào hệ thống thanh toán quốc tế.
        """
    },
    {
        "title": "Học máy trong dự báo thời tiết",
        "author": "Lê Văn Cường",
        "university": "ĐH Khoa Học Tự Nhiên",
        "year": 2022,
        "content": """
        Các mô hình học máy đang được sử dụng để cải thiện độ chính xác dự báo thời tiết.
        Neural networks có thể phân tích dữ liệu khí tượng historycal để dự đoán tương lai.
        LSTM và RNN phù hợp cho việc dự báo chuỗi thời gian khí tượng học.
        Dữ liệu vệ tinh và cảm biến được kết hợp với AI để dự báo chính xác hơn.
        Mô hình ensemble giúp giảm sai số trong dự báo thời tiết dài hạn.
        """
    },
    {
        "title": "Xử lý ngôn ngữ tự nhiên cho tiếng Việt",
        "author": "Phạm Thị Dung",
        "university": "ĐHQG Hà Nội",
        "year": 2023,
        "content": """
        Xử lý ngôn ngữ tự nhiên tiếng Việt có nhiều thách thức đặc thù cần giải quyết.
        Tách từ là bước quan trọng đầu tiên trong quy trình xử lý văn bản tiếng Việt.
        Các từ ghép như trí tuệ nhân tạo cần được giữ nguyên khi tokenize.
        BERT đa ngôn ngữ đã được fine-tune cho tiếng Việt với kết quả tốt.
        PhoBERT là mô hình được huấn luyện riêng cho tiếng Việt đạt hiệu quả cao.
        """
    },
    {
        "title": "An ninh mạng trong thời đại số",
        "author": "Hoàng Văn Em",
        "university": "ĐH Công Nghệ",
        "year": 2022,
        "content": """
        An ninh mạng là một trong những ưu tiên hàng đầu của mọi tổ chức hiện đại.
        Tấn công ransomware và phishing đang ngày càng tinh vi và phức tạp hơn.
        Machine learning giúp phát hiện các hành vi bất thường trong mạng máy tính.
        Firewall thế hệ mới sử dụng AI để chống lại các cuộc tấn công zero-day.
        Bảo mật đa lớp là chiến lược quan trọng để bảo vệ dữ liệu doanh nghiệp.
        """
    },
    {
        "title": "Thương mại điện tử tại Việt Nam",
        "author": "Võ Thị Giang",
        "university": "ĐH Kinh Tế TP.HCM",
        "year": 2023,
        "content": """
        Thương mại điện tử tại Việt Nam đang phát triển với tốc độ nhanh chóng.
        Shopee, Lazada và Tiki là ba sàn thương mại điện tử lớn nhất hiện nay.
        Thanh toán qua ví điện tử như Momo và ZaloPay ngày càng phổ biến.
        Livestream bán hàng đang trở thành xu hướng mới trong e-commerce.
        Dịch vụ giao hàng nhanh trong ngày thúc đẩy doanh số bán hàng online.
        """
    },
    {
        "title": "Robot công nghiệp và tự động hóa",
        "author": "Đinh Văn Hải",
        "university": "ĐH Bách Khoa HN",
        "year": 2022,
        "content": """
        Robot công nghiệp đang thay thế con người trong nhiều công việc sản xuất.
        Cánh tay robot được sử dụng rộng rãi trong lắp ráp điện tử và ô tô.
        Industrial IoT kết nối các thiết bị sản xuất để tối ưu hóa quy trình.
        Cobots là robot cộng tác có thể làm việc an toàn bên cạnh con người.
        Tự động hóa nhà máy giúp tăng năng suất và giảm chi phí sản xuất.
        """
    },
    {
        "title": "Điện toán đám mây và dịch vụ cloud",
        "author": "Ngô Thị Kim",
        "university": "FPT University",
        "year": 2023,
        "content": """
        Cloud computing đang thay đổi cách các doanh nghiệp quản lý hạ tầng IT.
        AWS, Azure và Google Cloud là ba nhà cung cấp dịch vụ cloud lớn nhất.
        Serverless architecture cho phép triển khai ứng dụng mà không cần quản lý server.
        Containerization với Docker và Kubernetes giúp đóng gói ứng dụng hiệu quả.
        Multi-cloud strategy giúp tránh vendor lock-in và tăng tính linh hoạt.
        """
    },
    {
        "title": "Big Data và phân tích dữ liệu lớn",
        "author": "Bùi Văn Long",
        "university": "ĐH Công Nghệ Thông Tin",
        "year": 2022,
        "content": """
        Big Data đang mở ra cơ hội mới cho phân tích và ra quyết định kinh doanh.
        Hadoop và Spark là hai framework phổ biến để xử lý dữ liệu lớn.
        Data warehouse và data lake là hai mô hình lưu trữ dữ liệu phổ biến.
        Business Intelligence giúp trực quan hóa dữ liệu để hỗ trợ ra quyết định.
        Real-time analytics cho phép phân tích dữ liệu streaming ngay lập tức.
        """
    },
    {
        "title": "Internet of Things trong nông nghiệp",
        "author": "Trương Thị Mai",
        "university": "ĐH Nông Lâm",
        "year": 2023,
        "content": """
        IoT đang được ứng dụng để tạo ra nền nông nghiệp thông minh và bền vững.
        Cảm biến độ ẩm và nhiệt độ giúp theo dõi tình trạng cây trồng liên tục.
        Drone nông nghiệp được sử dụng để phun thuốc và giám sát đồng ruộng.
        Hệ thống tưới tiêu tự động giúp tiết kiệm nước và tăng năng suất.
        Truy xuất nguồn gốc sản phẩm bằng blockchain đảm bảo an toàn thực phẩm.
        """
    },
    {
        "title": "Thực tế ảo trong giáo dục",
        "author": "Lý Văn Nam",
        "university": "ĐH Sư Phạm",
        "year": 2022,
        "content": """
        Virtual Reality đang được ứng dụng để tạo ra trải nghiệm học tập mới mẻ.
        Học sinh có thể khám phá hệ mặt trời hoặc cơ thể người qua VR headset.
        Thí nghiệm ảo giúp sinh viên thực hành mà không cần phòng thí nghiệm thật.
        Augmented Reality bổ sung thông tin số vào sách giáo khoa truyền thống.
        Metaverse education cho phép học tập trong không gian ảo 3D tương tác.
        """
    },
    {
        "title": "Fintech và ngân hàng số",
        "author": "Đặng Thị Oanh",
        "university": "ĐH Ngân Hàng",
        "year": 2023,
        "content": """
        Fintech đang định hình lại ngành dịch vụ tài chính truyền thống.
        Mobile banking cho phép thực hiện giao dịch mọi lúc mọi nơi trên điện thoại.
        AI được sử dụng để đánh giá tín dụng và phát hiện gian lận tài chính.
        Open banking API cho phép chia sẻ dữ liệu giữa các tổ chức tài chính.
        Robo-advisor giúp tư vấn đầu tư tự động dựa trên mục tiêu cá nhân.
        """
    },
    {
        "title": "Năng lượng tái tạo và công nghệ xanh",
        "author": "Phan Văn Phong",
        "university": "ĐH Điện Lực",
        "year": 2022,
        "content": """
        Năng lượng tái tạo đang trở thành xu hướng tất yếu để chống biến đổi khí hậu.
        Điện mặt trời và điện gió là hai nguồn năng lượng sạch phát triển nhanh nhất.
        Pin lithium-ion được sử dụng để lưu trữ năng lượng từ các nguồn tái tạo.
        Smart grid giúp quản lý và phân phối điện hiệu quả trong lưới điện thông minh.
        Xe điện đang dần thay thế xe xăng để giảm phát thải carbon dioxide.
        """
    },
    {
        "title": "Học sâu trong nhận dạng khuôn mặt",
        "author": "Cao Thị Quỳnh",
        "university": "ĐH Bách Khoa Đà Nẵng",
        "year": 2023,
        "content": """
        Deep learning đã cách mạng hóa công nghệ nhận dạng khuôn mặt toàn cầu.
        Convolutional Neural Networks trích xuất đặc trưng từ hình ảnh khuôn mặt.
        Face embedding chuyển khuôn mặt thành vector số để so sánh nhanh chóng.
        Liveness detection giúp phân biệt khuôn mặt thật và ảnh hay video.
        Nhận dạng khuôn mặt được ứng dụng trong bảo mật và kiểm soát ra vào.
        """
    },
    {
        "title": "Phát triển game và thực tế ảo",
        "author": "Vũ Văn Rạng",
        "university": "Arena Multimedia",
        "year": 2022,
        "content": """
        Ngành công nghiệp game toàn cầu đang tăng trưởng với tốc độ nhanh chóng.
        Unity và Unreal Engine là hai game engine phổ biến nhất để phát triển game.
        VR gaming mang đến trải nghiệm chơi game nhập vai hoàn toàn mới.
        Esports đang trở thành ngành công nghiệp giải trí tỷ đô trên toàn cầu.
        Cloud gaming cho phép stream game chất lượng cao trên mọi thiết bị.
        """
    },
    {
        "title": "Xử lý ảnh y tế với deep learning",
        "author": "Nguyễn Thị Sen",
        "university": "ĐH Y Dược TP.HCM",
        "year": 2023,
        "content": """
        Deep learning đang được ứng dụng mạnh mẽ trong phân tích hình ảnh y tế.
        CNN có thể phát hiện khối u từ ảnh X-quang và CT với độ chính xác cao.
        Segmentation network giúp phân vùng các cơ quan và mô trong cơ thể.
        Transfer learning cho phép sử dụng mô hình pretrained với ít dữ liệu y tế.
        AI-assisted diagnosis giúp bác sĩ đưa ra quyết định chẩn đoán nhanh hơn.
        """
    },
    {
        "title": "Chatbot và trợ lý ảo thông minh",
        "author": "Hoàng Văn Tuấn",
        "university": "ĐH FPT",
        "year": 2022,
        "content": """
        Chatbot đang thay đổi cách doanh nghiệp tương tác với khách hàng mỗi ngày.
        NLP cho phép chatbot hiểu và phản hồi ngôn ngữ tự nhiên của con người.
        Intent recognition giúp xác định ý định người dùng từ câu hỏi đặt ra.
        Virtual assistant như Siri và Alexa hỗ trợ cuộc sống hàng ngày tiện lợi.
        GPT và các mô hình ngôn ngữ lớn tạo ra chatbot thông minh đáng kinh ngạc.
        """
    },
    {
        "title": "An toàn thông tin và mã hóa dữ liệu",
        "author": "Lâm Thị Uyên",
        "university": "Học viện Kỹ thuật Mật mã",
        "year": 2023,
        "content": """
        Mã hóa dữ liệu là nền tảng quan trọng để bảo vệ thông tin trong kỷ nguyên số.
        AES và RSA là hai thuật toán mã hóa được sử dụng phổ biến nhất hiện nay.
        End-to-end encryption đảm bảo chỉ người gửi và nhận đọc được tin nhắn.
        Blockchain sử dụng hàm băm và chữ ký số để đảm bảo tính toàn vẹn dữ liệu.
        Zero-knowledge proof cho phép xác thực mà không tiết lộ thông tin bí mật.
        """
    },
    {
        "title": "Phân tích cảm xúc trên mạng xã hội",
        "author": "Trần Văn Vinh",
        "university": "ĐH RMIT Việt Nam",
        "year": 2022,
        "content": """
        Sentiment analysis giúp doanh nghiệp hiểu được cảm xúc của khách hàng online.
        NLP được sử dụng để phân loại bình luận thành tích cực, tiêu cực hoặc trung tính.
        Social listening tools theo dõi thương hiệu và phản hồi trên mạng xã hội.
        Opinion mining giúp trích xuất ý kiến về sản phẩm từ reviews của khách hàng.
        Real-time sentiment tracking cho phép phản ứng nhanh với khủng hoảng truyền thông.
        """
    },
    {
        "title": "Xe tự hành và công nghệ ô tô",
        "author": "Đỗ Văn Xuân",
        "university": "ĐH Giao Thông Vận Tải",
        "year": 2023,
        "content": """
        Xe tự hành đang được phát triển bởi các công ty công nghệ lớn trên thế giới.
        LiDAR và camera là hai cảm biến chính giúp xe nhận biết môi trường xung quanh.
        Deep learning được sử dụng để nhận dạng biển báo, người đi bộ và phương tiện.
        V2X communication cho phép xe giao tiếp với cơ sở hạ tầng và xe khác.
        Tesla Autopilot và Waymo là hai hệ thống lái xe tự động tiên tiến nhất hiện nay.
        """
    },
]


def seed_corpus():
    """Seed 20 documents vào Redis"""
    
    print("=" * 60)
    print("🌱 SEED CORPUS - PlagiarismGuard 2.0")
    print("=" * 60)
    print(f"📊 Total documents: {len(SAMPLE_DOCUMENTS)}\n")
    
    # Connect Redis
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connected\n")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # Seed documents
    count = 0
    for i, doc in enumerate(SAMPLE_DOCUMENTS, 1):
        try:
            doc_id = str(uuid.uuid4())
            
            # Process text using app modules (same as checker)
            text = normalize_text(doc['content'])
            tokens = preprocess_vietnamese(text)
            shingles = create_shingles(tokens, k=settings.SHINGLE_SIZE)
            minhash = create_minhash_signature(shingles)
            
            # Store signature (serialize numpy array as json)
            import json
            sig_json = json.dumps(minhash.hashvalues.tolist())
            r.set(f"doc:sig:{doc_id}", sig_json)
            
            # Store metadata
            metadata = {
                'id': doc_id,
                'title': doc['title'],
                'author': doc['author'],
                'university': doc['university'],
                'year': str(doc['year']),
                'word_count': str(len(tokens)),
                'indexed_at': datetime.now().isoformat()
            }
            r.hset(f"doc:meta:{doc_id}", mapping=metadata)
            
            count += 1
            print(f"✅ [{i}/{len(SAMPLE_DOCUMENTS)}] {doc['title'][:40]}...")
            
        except Exception as e:
            print(f"❌ [{i}] Error: {e}")
    
    print()
    print("=" * 60)
    print(f"✅ DONE! Seeded {count}/{len(SAMPLE_DOCUMENTS)} documents")
    print("=" * 60)


if __name__ == "__main__":
    seed_corpus()
