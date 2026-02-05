#!/usr/bin/env python3
"""
Seed Corpus with 20%+ Match to docs_test/

Tạo corpus ~3000 documents, mỗi doc ~1000 từ, đảm bảo có ít nhất 20% 
similarity với các documents trong docs_test/ folder.

Chiến lược:
1. Đọc tất cả source docs từ docs_test/
2. Trích xuất các đoạn văn, câu quan trọng
3. Tạo documents mới bằng cách:
   - Lấy 20-40% nội dung gốc (đảm bảo match)
   - Thêm 60-80% nội dung mới/paraphrase
   - Đạt ~1000 từ

Usage:
    python scripts/seed_corpus_matched.py --num-docs 3000
    python scripts/seed_corpus_matched.py --num-docs 3000 --sync-redis
"""
import os
import sys
import uuid
import hashlib
import argparse
import random
import json
from datetime import datetime
from typing import List, Dict, Tuple
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.db.database import engine, SessionLocal
from app.db.models import Document, Base

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# DOCS_TEST FOLDER PATH
# ═══════════════════════════════════════════════════════════════
# Try multiple paths (Docker container vs local)
POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs_test"),  # /app/docs_test
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "docs_test"),  # project root
    "/app/docs_test",  # Docker container absolute
]

DOCS_TEST_PATH = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        DOCS_TEST_PATH = path
        break

if not DOCS_TEST_PATH:
    DOCS_TEST_PATH = POSSIBLE_PATHS[0]  # Default fallback

# ═══════════════════════════════════════════════════════════════
# METADATA TEMPLATES
# ═══════════════════════════════════════════════════════════════
UNIVERSITIES = [
    "Đại học Bách khoa Hà Nội",
    "Đại học Công nghệ - ĐHQGHN",
    "Đại học Khoa học Tự nhiên - ĐHQGHN",
    "Đại học Bách khoa TP.HCM",
    "Đại học Công nghệ Thông tin - ĐHQG TP.HCM",
    "Đại học Khoa học Tự nhiên - ĐHQG TP.HCM",
    "Học viện Công nghệ Bưu chính Viễn thông",
    "Đại học FPT",
    "Đại học Sư phạm Kỹ thuật TP.HCM",
    "Đại học Cần Thơ",
    "Đại học Đà Nẵng",
    "Đại học Kinh tế TP.HCM",
]

AUTHOR_FIRST = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ"]
AUTHOR_MIDDLE = ["Văn", "Thị", "Đức", "Minh", "Quốc", "Hữu", "Thanh", "Ngọc", "Kim", "Anh", "Hoàng", "Xuân"]
AUTHOR_LAST = ["An", "Bình", "Cường", "Dũng", "Hào", "Khoa", "Long", "Nam", "Phong", "Quân", "Tùng", "Việt", "Hưng", "Đạt"]

# ═══════════════════════════════════════════════════════════════
# EXPANSION TEMPLATES - Để mở rộng nội dung
# ═══════════════════════════════════════════════════════════════

INTRO_TEMPLATES = [
    "Trong bối cảnh công nghệ phát triển như vũ bão, {topic} đang trở thành xu hướng được quan tâm hàng đầu trong cộng đồng khoa học và công nghệ.",
    "Nghiên cứu về {topic} đã và đang mang lại những đóng góp quan trọng cho sự phát triển của xã hội hiện đại.",
    "Bài viết này tập trung phân tích các khía cạnh quan trọng của {topic} trong bối cảnh chuyển đổi số toàn cầu.",
    "{topic} là một trong những lĩnh vực đang nhận được sự đầu tư lớn từ cả khu vực công và tư nhân.",
    "Với sự tiến bộ không ngừng của khoa học kỹ thuật, {topic} ngày càng chứng minh vai trò thiết yếu trong đời sống.",
]

METHODOLOGY_TEMPLATES = [
    "Phương pháp nghiên cứu được áp dụng bao gồm phân tích tài liệu, khảo sát thực nghiệm và đánh giá định lượng kết quả.",
    "Nghiên cứu này sử dụng phương pháp định tính kết hợp định lượng để đảm bảo tính khách quan và toàn diện.",
    "Dữ liệu được thu thập từ nhiều nguồn khác nhau và xử lý bằng các công cụ phân tích hiện đại.",
    "Quy trình nghiên cứu tuân thủ các chuẩn mực khoa học quốc tế với sự kiểm chứng chéo từ nhiều chuyên gia.",
]

TECHNICAL_PARAGRAPHS = [
    "Hệ thống được thiết kế theo kiến trúc microservices với khả năng mở rộng linh hoạt theo nhu cầu sử dụng. Việc triển khai trên nền tảng đám mây giúp tối ưu chi phí vận hành và đảm bảo tính sẵn sàng cao. Container hóa với Docker và Kubernetes giúp đơn giản hóa quy trình DevOps.",
    "Cơ sở dữ liệu được thiết kế theo mô hình quan hệ với các bảng được chuẩn hóa đến dạng 3NF. PostgreSQL được lựa chọn làm RDBMS chính vì hỗ trợ ACID transactions và hiệu năng cao. Redis được sử dụng cho caching và session management.",
    "API được phát triển theo chuẩn RESTful với xác thực JWT và OAuth 2.0. Documentation API được tạo tự động với OpenAPI/Swagger. Rate limiting và request throttling được implement để bảo vệ hệ thống.",
    "Giao diện người dùng được xây dựng với React và TypeScript, tuân thủ nguyên tắc thiết kế responsive. State management sử dụng Redux Toolkit để đảm bảo tính nhất quán dữ liệu. Unit tests và E2E tests được viết với Jest và Cypress.",
    "Monitoring và logging được tích hợp với Prometheus và Grafana để theo dõi health metrics. ELK stack được sử dụng cho centralized logging. Alerting được cấu hình để thông báo kịp thời các sự cố.",
    "CI/CD pipeline được thiết lập với GitHub Actions để tự động hóa testing và deployment. Infrastructure as Code với Terraform đảm bảo reproducibility. Blue-green deployment giảm thiểu downtime khi release.",
]

CONCLUSION_TEMPLATES = [
    "Tổng kết lại, nghiên cứu này đã đạt được những kết quả đáng khích lệ và mở ra hướng phát triển tiếp theo cho {topic}.",
    "Kết quả nghiên cứu cho thấy tiềm năng ứng dụng rộng rãi của {topic} trong thực tiễn sản xuất và đời sống.",
    "Những đóng góp của nghiên cứu này hy vọng sẽ góp phần thúc đẩy sự phát triển của {topic} tại Việt Nam.",
    "Hướng nghiên cứu tiếp theo sẽ tập trung vào việc tối ưu hóa và mở rộng quy mô ứng dụng của {topic}.",
]

FILLER_PARAGRAPHS = [
    "Việc áp dụng các phương pháp tiên tiến đã mang lại những cải thiện đáng kể về hiệu suất. Các thử nghiệm được tiến hành trên nhiều bộ dữ liệu benchmark cho thấy kết quả vượt trội so với baseline. Đặc biệt, thời gian xử lý được giảm đáng kể trong khi vẫn duy trì độ chính xác cao.",
    "Các thách thức gặp phải trong quá trình triển khai đã được giải quyết thông qua việc áp dụng các best practices trong ngành. Việc tối ưu hóa thuật toán giúp cải thiện hiệu năng xử lý lên đến 40%. Khả năng mở rộng của hệ thống đã được kiểm chứng qua stress testing.",
    "So sánh với các phương pháp hiện có cho thấy giải pháp đề xuất có nhiều ưu điểm vượt trội. Chi phí triển khai được tối ưu hóa nhờ sử dụng các công nghệ mã nguồn mở. Tính bảo trì và khả năng nâng cấp được đảm bảo thông qua kiến trúc modular.",
    "Phản hồi từ người dùng thử nghiệm cho thấy mức độ hài lòng cao với hệ thống. Giao diện trực quan và dễ sử dụng giúp giảm thời gian training cho người dùng mới. Các tính năng được thiết kế dựa trên nhu cầu thực tế của người dùng cuối.",
    "Bảo mật là một trong những ưu tiên hàng đầu trong quá trình phát triển hệ thống. Mã hóa end-to-end được áp dụng cho tất cả dữ liệu nhạy cảm. Penetration testing được thực hiện định kỳ để phát hiện và khắc phục các lỗ hổng bảo mật.",
]


def generate_author() -> str:
    """Generate random Vietnamese author name"""
    return f"{random.choice(AUTHOR_FIRST)} {random.choice(AUTHOR_MIDDLE)} {random.choice(AUTHOR_LAST)}"


def load_source_documents() -> Dict[str, Dict]:
    """
    Load all documents from docs_test/ folder
    
    Returns:
        Dict mapping filename to {text, sentences, paragraphs, topic}
    """
    sources = {}
    
    if not os.path.exists(DOCS_TEST_PATH):
        logger.error(f"docs_test/ folder not found at {DOCS_TEST_PATH}")
        return sources
    
    for filename in os.listdir(DOCS_TEST_PATH):
        if not filename.endswith('.txt'):
            continue
        
        filepath = os.path.join(DOCS_TEST_PATH, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            # Extract topic from filename
            topic = filename.replace('.txt', '').replace('_', ' ').title()
            
            # Split into sentences and paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            sentences = []
            for p in paragraphs:
                sents = [s.strip() for s in p.replace('\n', ' ').split('.') if s.strip() and len(s.strip()) > 10]
                sentences.extend(sents)
            
            sources[filename] = {
                'text': text,
                'sentences': sentences,
                'paragraphs': paragraphs,
                'topic': topic,
                'word_count': len(text.split())
            }
            
            logger.info(f"Loaded {filename}: {len(sentences)} sentences, {len(paragraphs)} paragraphs")
            
        except Exception as e:
            logger.warning(f"Error loading {filename}: {e}")
    
    return sources


def create_matched_document(
    sources: Dict[str, Dict],
    target_words: int = 1000,
    match_ratio: float = 0.25  # 25% from source to ensure 20%+ match
) -> Tuple[str, str, str]:
    """
    Create a document with ~25% content from source (ensures 20%+ similarity)
    
    Args:
        sources: Dict of source documents
        target_words: Target word count
        match_ratio: Ratio of content to take from sources
        
    Returns:
        Tuple of (text, topic, source_filename)
    """
    # Pick a random source document
    source_file = random.choice(list(sources.keys()))
    source = sources[source_file]
    topic = source['topic']
    
    # Calculate how many words to take from source
    source_words = int(target_words * match_ratio)
    filler_words = target_words - source_words
    
    document_parts = []
    current_words = 0
    
    # 1. Add intro (filler)
    intro = random.choice(INTRO_TEMPLATES).format(topic=topic)
    document_parts.append(intro)
    current_words += len(intro.split())
    
    # 2. Add some source sentences (ensure match)
    source_sentences = source['sentences'].copy()
    random.shuffle(source_sentences)
    
    matched_content = []
    words_from_source = 0
    
    for sent in source_sentences:
        if words_from_source >= source_words:
            break
        sent_clean = sent.strip()
        if not sent_clean.endswith('.'):
            sent_clean += '.'
        matched_content.append(sent_clean)
        words_from_source += len(sent_clean.split())
    
    # Insert matched content throughout the document
    if matched_content:
        # Split into chunks to distribute
        chunk_size = max(1, len(matched_content) // 3)
        chunks = [matched_content[i:i+chunk_size] for i in range(0, len(matched_content), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            # Add a paragraph of matched content
            matched_para = ' '.join(chunk)
            document_parts.append(matched_para)
            current_words += len(matched_para.split())
            
            # Add filler between chunks
            if i < len(chunks) - 1:
                filler = random.choice(FILLER_PARAGRAPHS)
                document_parts.append(filler)
                current_words += len(filler.split())
    
    # 3. Add methodology section
    methodology = random.choice(METHODOLOGY_TEMPLATES)
    document_parts.append(methodology)
    current_words += len(methodology.split())
    
    # 4. Add technical paragraphs to reach target
    while current_words < target_words - 100:
        para = random.choice(TECHNICAL_PARAGRAPHS + FILLER_PARAGRAPHS)
        document_parts.append(para)
        current_words += len(para.split())
    
    # 5. Add conclusion
    conclusion = random.choice(CONCLUSION_TEMPLATES).format(topic=topic)
    document_parts.append(conclusion)
    
    # Join with double newlines
    final_text = '\n\n'.join(document_parts)
    
    return final_text, topic, source_file


def seed_corpus(num_docs: int = 3000, sync_redis: bool = False):
    """
    Generate and seed corpus with documents matching docs_test/
    
    Args:
        num_docs: Number of documents to generate
        sync_redis: Also sync to Redis after seeding
    """
    logger.info("=" * 60)
    logger.info("SEEDING CORPUS WITH MATCHED DOCUMENTS")
    logger.info("=" * 60)
    
    # Load source documents
    sources = load_source_documents()
    if not sources:
        logger.error("No source documents found in docs_test/")
        return
    
    logger.info(f"Loaded {len(sources)} source documents from docs_test/")
    
    # Connect to PostgreSQL
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        logger.info("✅ Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"❌ Cannot connect to PostgreSQL: {e}")
        return
    
    stats = {
        "total": 0,
        "success": 0,
        "duplicates": 0,
        "source_distribution": {},
    }
    
    try:
        for i in range(num_docs):
            # Create matched document
            text, topic, source_file = create_matched_document(
                sources,
                target_words=random.randint(900, 1100),  # ~1000 words
                match_ratio=random.uniform(0.22, 0.35)    # 22-35% from source
            )
            
            word_count = len(text.split())
            author = generate_author()
            university = random.choice(UNIVERSITIES)
            year = random.randint(2018, 2024)
            title = f"Nghiên cứu về {topic} - {random.randint(1, 9999):04d}"
            
            # Track source distribution
            stats["source_distribution"][source_file] = stats["source_distribution"].get(source_file, 0) + 1
            
            # Create hash
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            # Check duplicate
            existing = db.query(Document).filter(
                Document.file_hash_sha256 == text_hash
            ).first()
            
            if existing:
                stats["duplicates"] += 1
                continue
            
            # Create document
            doc = Document(
                id=uuid.uuid4(),
                title=title,
                author=author,
                university=university,
                year=year,
                topic=topic,
                word_count=word_count,
                file_hash_sha256=text_hash,
                extracted_text=text,
                status='indexed',
                is_corpus=1,
                language='vi',
                indexed_at=datetime.now()
            )
            
            db.add(doc)
            stats["success"] += 1
            stats["total"] += 1
            
            # Commit batch
            if (i + 1) % 100 == 0:
                db.commit()
                logger.info(f"Progress: {i + 1}/{num_docs} ({stats['success']} saved, ~{word_count} words each)")
        
        # Final commit
        db.commit()
        
        # Get total count
        total_corpus = db.query(Document).filter(Document.is_corpus == 1).count()
        stats["total_in_db"] = total_corpus
        
        logger.info("=" * 60)
        logger.info("✅ SEEDING COMPLETE")
        logger.info(f"   Generated: {stats['total']}")
        logger.info(f"   Saved to PostgreSQL: {stats['success']}")
        logger.info(f"   Duplicates skipped: {stats['duplicates']}")
        logger.info(f"   Total corpus in DB: {total_corpus}")
        logger.info("")
        logger.info("Source document distribution:")
        for src, count in sorted(stats["source_distribution"].items(), key=lambda x: -x[1]):
            logger.info(f"   {src}: {count} docs")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    # Sync to Redis if requested
    if sync_redis:
        sync_postgres_to_redis()
    
    return stats


def sync_postgres_to_redis():
    """Sync corpus from PostgreSQL to Redis (rebuild LSH index)"""
    import redis
    
    logger.info("Syncing PostgreSQL corpus to Redis...")
    
    try:
        from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
        from app.services.preprocessing.text_normalizer import normalize_text
        from app.services.algorithm.shingling import create_shingles
        from app.services.algorithm.minhash import create_minhash_signature
    except ImportError as e:
        logger.error(f"Cannot import processing modules: {e}")
        return
    
    # Connect
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=False)
        r.ping()
        db = SessionLocal()
        logger.info("✅ Connected to Redis and PostgreSQL")
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return
    
    # Get all corpus documents
    docs = db.query(Document).filter(
        Document.is_corpus == 1,
        Document.extracted_text.isnot(None)
    ).all()
    
    logger.info(f"Found {len(docs)} corpus documents to sync")
    
    synced = 0
    for doc in docs:
        try:
            # Create short doc_id (first 8 chars of UUID)
            doc_id = str(doc.id)[:8]
            
            # Process text
            text = doc.extracted_text
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            
            if len(tokens) < 10:
                continue
            
            shingles = create_shingles(tokens, k=settings.SHINGLE_SIZE)
            minhash = create_minhash_signature(shingles)
            
            # Store in Redis
            sig_json = json.dumps(minhash.hashvalues.tolist())
            r.set(f"doc:sig:{doc_id}", sig_json)
            
            r.hset(f"doc:meta:{doc_id}", mapping={
                "title": doc.title or "",
                "author": doc.author or "",
                "university": doc.university or "",
                "year": str(doc.year or 2024),
                "word_count": str(doc.word_count or 0),
                "topic": doc.topic or "",
                "pg_id": str(doc.id),
            })
            
            synced += 1
            
            if synced % 200 == 0:
                logger.info(f"Synced {synced}/{len(docs)} documents to Redis")
                
        except Exception as e:
            logger.warning(f"Error syncing doc {doc.id}: {e}")
    
    db.close()
    logger.info(f"✅ Synced {synced} documents to Redis LSH index")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed corpus with documents matching docs_test/")
    parser.add_argument("--num-docs", type=int, default=3000, help="Number of documents to generate")
    parser.add_argument("--sync-redis", action="store_true", help="Also sync to Redis after seeding")
    
    args = parser.parse_args()
    
    seed_corpus(args.num_docs, args.sync_redis)
