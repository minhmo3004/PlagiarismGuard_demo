#!/usr/bin/env python3
"""
Script thu thập bài báo từ ArXiv và nhập vào Corpus

Thu thập các bài báo học thuật từ máy chủ preprint ArXiv và nhập vào cơ sở dữ liệu.

Cách sử dụng:
    # Thu thập bài báo AI
    python scripts/crawl_arxiv_import.py --ai 50
    
    # Thu thập bài báo Machine Learning
    python scripts/crawl_arxiv_import.py --ml 50
    
    # Thu thập bài báo Computer Vision
    python scripts/crawl_arxiv_import.py --cv 30
    
    # Thu thập bài báo liên quan đến Việt Nam
    python scripts/crawl_arxiv_import.py --vietnamese 100
    
    # Thu thập và đồng bộ ngay vào Redis
    python scripts/crawl_arxiv_import.py --ai 50 --sync-redis

Ví dụ:
    # Test nhanh
    python scripts/crawl_arxiv_import.py --ai 10
    
    # Thu thập lớn theo nhiều chuyên mục
    python scripts/crawl_arxiv_import.py --multi-category 20 --sync-redis
"""
import os
import sys
import uuid
import hashlib
import argparse
from datetime import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Document
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.preprocessing.text_normalizer import normalize_text
from crawlers.academic_crawlers import ArxivCrawler

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def import_documents_to_db(documents: list, db_session) -> int:
    """
    Nhập các tài liệu đã thu thập vào cơ sở dữ liệu PostgreSQL
    
    Args:
        documents: Danh sách tài liệu từ crawler
        db_session: Session SQLAlchemy
        
    Returns:
        Số lượng tài liệu nhập thành công
    """
    imported = 0
    skipped = 0
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📥 ĐANG NHẬP {len(documents)} TÀI LIỆU VÀO DATABASE")
    logger.info(f"{'='*70}\n")
    
    for i, doc_data in enumerate(documents, 1):
        try:
            # Chuẩn hóa và tokenize văn bản
            text = doc_data['content']
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            word_count = len(tokens)
            
            # Bỏ qua nếu bài quá ngắn
            if word_count < 100:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Quá ngắn ({word_count} từ), bỏ qua")
                skipped += 1
                continue
            
            # Kiểm tra trùng lặp theo hash
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            existing = db_session.query(Document).filter(
                Document.file_hash_sha256 == text_hash
            ).first()
            
            if existing:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Trùng lặp, bỏ qua")
                skipped += 1
                continue
            
            # Tạo bản ghi Document
            doc = Document(
                id=uuid.uuid4(),
                title=doc_data['title'][:500],
                author=doc_data.get('author', 'Unknown'),
                university=doc_data.get('university', 'ArXiv'),
                year=doc_data.get('year', datetime.now().year),
                original_filename=f"arxiv_{doc_data.get('source', 'unknown')}.txt",
                file_hash_sha256=text_hash,
                file_size_bytes=len(text.encode()),
                word_count=word_count,
                language='en',                    # ArXiv chủ yếu là tiếng Anh
                extraction_method='arxiv_crawler',
                extracted_text=text,
                is_corpus=1,                      # Đánh dấu là tài liệu corpus
                status='indexed',
                indexed_at=datetime.now()
            )
            
            db_session.add(doc)
            imported += 1
            
            logger.info(f"✅ [{imported}/{len(documents)}] {doc_data['title'][:50]}... - {word_count} từ")
            
            # Commit theo batch
            if imported % 50 == 0:
                try:
                    db_session.commit()
                    logger.info(f"   💾 Đã lưu {imported} tài liệu...")
                except Exception as commit_err:
                    logger.error(f"❌ Lỗi commit batch: {commit_err}")
                    db_session.rollback()
        
        except Exception as e:
            logger.error(f"❌ [{i}/{len(documents)}] Lỗi: {e}")
            db_session.rollback()
            skipped += 1
    
    # Commit lần cuối
    try:
        db_session.commit()
    except Exception as e:
        logger.error(f"❌ Lỗi commit cuối cùng: {e}")
        db_session.rollback()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ Tóm tắt nhập liệu:")
    logger.info(f"   • Nhập thành công: {imported} tài liệu")
    logger.info(f"   • Bỏ qua / Lỗi: {skipped} tài liệu")
    logger.info(f"   • Tổng đã xử lý: {len(documents)} tài liệu")
    logger.info(f"{'='*70}\n")
    
    return imported


def sync_to_redis():
    """Hướng dẫn đồng bộ corpus vào Redis LSH index"""
    logger.info("\n⚠️  ĐỂ ĐỒNG BỘ VÀO REDIS LSH INDEX:")
    logger.info("   Chạy lệnh: docker restart plagiarism-backend")
    logger.info("   Hoặc dùng flag --sync-redis ở lần chạy sau\n")


def main():
    parser = argparse.ArgumentParser(
        description='Thu thập bài báo ArXiv và nhập vào corpus'
    )
    
    # Chọn chế độ thu thập
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ai', type=int, metavar='N',
                      help='Thu thập N bài báo AI (cs.AI)')
    group.add_argument('--ml', type=int, metavar='N',
                      help='Thu thập N bài báo Machine Learning (cs.LG)')
    group.add_argument('--cv', type=int, metavar='N',
                      help='Thu thập N bài báo Computer Vision (cs.CV)')
    group.add_argument('--nlp', type=int, metavar='N',
                      help='Thu thập N bài báo NLP (cs.CL)')
    group.add_argument('--vietnamese', type=int, metavar='N',
                      help='Thu thập N bài báo liên quan đến Việt Nam')
    group.add_argument('--multi-category', type=int, metavar='N',
                      help='Thu thập N bài báo từ mỗi chuyên mục chính')
    
    # Tùy chọn bổ sung
    parser.add_argument('--sync-redis', action='store_true',
                       help='Đồng bộ ngay vào Redis sau khi nhập (yêu cầu Docker)')
    
    args = parser.parse_args()
    
    # Khởi tạo crawler
    crawler = ArxivCrawler(delay_seconds=3.0)
    
    logger.info("\n🚀 Đang khởi động ArXiv Crawler...")
    
    # Xác định chế độ và thực hiện thu thập
    documents = []
    
    if args.ai:
        logger.info(f"Chế độ: Bài báo AI (cs.AI, n={args.ai})")
        documents = crawler.crawl(query='', category='cs.AI', limit=args.ai)
        
    elif args.ml:
        logger.info(f"Chế độ: Machine Learning (cs.LG, n={args.ml})")
        documents = crawler.crawl(query='', category='cs.LG', limit=args.ml)
        
    elif args.cv:
        logger.info(f"Chế độ: Computer Vision (cs.CV, n={args.cv})")
        documents = crawler.crawl(query='', category='cs.CV', limit=args.cv)
        
    elif args.nlp:
        logger.info(f"Chế độ: NLP (cs.CL, n={args.nlp})")
        documents = crawler.crawl(query='', category='cs.CL', limit=args.nlp)
        
    elif args.vietnamese:
        logger.info(f"Chế độ: Bài báo liên quan đến Việt Nam (n={args.vietnamese})")
        documents = crawler.search_vietnamese_ai(limit=args.vietnamese)
        
    elif args.multi_category:
        logger.info(f"Chế độ: Đa chuyên mục ({args.multi_category} bài mỗi chuyên mục)")
        categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.CR']
        documents = crawler.search_by_categories(
            query='',
            categories=categories,
            limit_per_cat=args.multi_category
        )
    
    # Nhập vào database
    if documents:
        db = SessionLocal()
        try:
            imported = import_documents_to_db(documents, db)
            logger.info(f"✅ Đã nhập thành công {imported} tài liệu vào database")
            
            # Đồng bộ Redis nếu có yêu cầu
            if args.sync_redis:
                logger.info("\n🔄 Đang đồng bộ vào Redis...")
                import subprocess
                try:
                    subprocess.run(['docker', 'restart', 'plagiarism-backend'], check=True)
                    logger.info("✅ Đã restart backend - Redis sẽ đồng bộ khi khởi động lại")
                except Exception as e:
                    logger.error(f"❌ Không thể restart backend: {e}")
                    sync_to_redis()
            else:
                sync_to_redis()
                
        finally:
            db.close()
    else:
        logger.warning("❌ Không thu thập được tài liệu nào. Kết thúc...")
    
    logger.info("\n✅ Hoàn tất!")


if __name__ == '__main__':
    main()