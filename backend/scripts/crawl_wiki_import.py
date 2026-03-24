#!/usr/bin/env python3
"""
Script thu thập bài viết từ Wikipedia tiếng Việt và nhập trực tiếp vào Corpus

Thu thập các bài viết từ Wikipedia tiếng Việt và lưu vào cơ sở dữ liệu.

Cách sử dụng:
    # Thu thập 100 bài viết ngẫu nhiên
    python scripts/crawl_wiki_import.py --random 100
    
    # Thu thập từ các chuyên mục công nghệ (20 bài mỗi chuyên mục)
    python scripts/crawl_wiki_import.py --tech-categories 20
    
    # Thu thập từ một chuyên mục cụ thể
    python scripts/crawl_wiki_import.py --category "Khoa_học_máy_tính" --limit 50
    
    # Thu thập và đồng bộ ngay vào Redis
    python scripts/crawl_wiki_import.py --random 100 --sync-redis

Ví dụ:
    # Test nhanh
    python scripts/crawl_wiki_import.py --random 10
    
    # Thu thập lớn từ các chuyên mục công nghệ
    python scripts/crawl_wiki_import.py --tech-categories 30 --sync-redis
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
from crawlers.viwiki_crawler import ViWikiCrawler

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
    
    # Theo dõi hash để tránh trùng lặp trong cùng batch
    seen_hashes = set()
    
    for i, doc_data in enumerate(documents, 1):
        try:
            # Chuẩn hóa và tokenize văn bản
            text = doc_data['content']
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            word_count = len(tokens)
            
            # Bỏ qua bài quá ngắn (tối thiểu 50 từ cho Wikipedia)
            if word_count < 50:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Quá ngắn ({word_count} từ), bỏ qua")
                skipped += 1
                continue
            
            # Kiểm tra trùng lặp theo hash (trong bộ nhớ + database)
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            if text_hash in seen_hashes:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Trùng trong batch, bỏ qua")
                skipped += 1
                continue
            
            existing = db_session.query(Document).filter(
                Document.file_hash_sha256 == text_hash
            ).first()
            
            if existing:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Đã tồn tại trong DB, bỏ qua")
                seen_hashes.add(text_hash)
                skipped += 1
                continue
            
            # Tạo bản ghi Document
            doc = Document(
                id=uuid.uuid4(),
                title=doc_data['title'][:500],
                author=doc_data.get('author', 'Wikipedia Contributors'),
                university=doc_data.get('university', 'Vietnamese Wikipedia'),
                year=doc_data.get('year', datetime.now().year),
                original_filename=f"wiki_{doc_data.get('source', 'unknown')}.txt",
                file_hash_sha256=text_hash,
                file_size_bytes=len(text.encode()),
                word_count=word_count,
                language='vi',
                extraction_method='wikipedia_crawler',
                extracted_text=text,
                is_corpus=1,          # Đánh dấu là tài liệu corpus
                status='indexed',
                indexed_at=datetime.now()
            )
            
            # Commit từng tài liệu một để tránh lỗi lan tỏa
            db_session.add(doc)
            try:
                db_session.commit()
                seen_hashes.add(text_hash)
                imported += 1
                logger.info(f"✅ [{imported}/{len(documents)}] {doc_data['title'][:50]}... - {word_count} từ")
            except Exception as commit_err:
                db_session.rollback()
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Lỗi DB, bỏ qua: {str(commit_err)[:80]}")
                seen_hashes.add(text_hash)
                skipped += 1
        
        except Exception as e:
            logger.error(f"❌ [{i}/{len(documents)}] Lỗi: {e}")
            try:
                db_session.rollback()
            except Exception:
                pass
            skipped += 1
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ Tóm tắt nhập liệu:")
    logger.info(f"   • Nhập thành công: {imported} tài liệu")
    logger.info(f"   • Bỏ qua / Lỗi: {skipped} tài liệu")
    logger.info(f"   • Tổng đã xử lý: {len(documents)} tài liệu")
    logger.info(f"{'='*70}\n")
    
    return imported


def sync_to_redis():
    """
    Hướng dẫn đồng bộ corpus vào Redis LSH index
    """
    logger.info("\n⚠️  ĐỂ ĐỒNG BỘ VÀO REDIS LSH INDEX:")
    logger.info("   Chạy lệnh: docker restart plagiarism-backend")
    logger.info("   Hoặc dùng flag --sync-redis ở lần chạy sau\n")


def main():
    parser = argparse.ArgumentParser(
        description='Thu thập bài viết Wikipedia tiếng Việt và nhập vào corpus'
    )
    
    # Chọn chế độ thu thập
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--random', type=int, metavar='N',
                      help='Thu thập N bài viết ngẫu nhiên')
    group.add_argument('--tech-categories', type=int, metavar='N',
                      help='Thu thập N bài từ mỗi chuyên mục công nghệ')
    group.add_argument('--category', type=str,
                      help='Thu thập từ một chuyên mục cụ thể (kết hợp với --limit)')
    
    # Tùy chọn bổ sung
    parser.add_argument('--limit', type=int, default=50,
                       help='Giới hạn cho chế độ chuyên mục (mặc định: 50)')
    parser.add_argument('--sync-redis', action='store_true',
                       help='Đồng bộ ngay vào Redis sau khi nhập (yêu cầu Docker)')
    parser.add_argument('--delay', type=float, default=1.5,
                       help='Thời gian nghỉ giữa các request (giây, mặc định: 1.5)')
    
    args = parser.parse_args()
    
    # Khởi tạo crawler
    logger.info("\n🚀 Đang khởi động Wikipedia Crawler...")
    crawler = ViWikiCrawler(delay_seconds=args.delay)
    
    # Thu thập theo chế độ
    documents = []
    
    try:
        if args.random:
            logger.info(f"Chế độ: Bài viết ngẫu nhiên (n={args.random})")
            documents = crawler.crawl(limit=args.random)
        
        elif args.tech_categories:
            logger.info(f"Chế độ: Chuyên mục công nghệ ({args.tech_categories} bài mỗi chuyên mục)")
            documents = crawler.crawl_tech_categories(limit_per_category=args.tech_categories)
        
        elif args.category:
            logger.info(f"Chế độ: Chuyên mục cụ thể '{args.category}' (limit={args.limit})")
            documents = crawler.crawl_category(args.category, limit=args.limit)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Quá trình thu thập bị ngắt bởi người dùng")
        if documents:
            logger.info(f"Tiếp tục nhập {len(documents)} tài liệu đã thu thập...")
        else:
            logger.info("Không có tài liệu nào được thu thập. Kết thúc.")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"❌ Lỗi trong quá trình thu thập: {e}")
        sys.exit(1)
    
    # Kiểm tra có tài liệu không
    if not documents:
        logger.warning("❌ Không thu thập được tài liệu nào. Kết thúc...")
        sys.exit(1)
    
    # Nhập vào database
    db = SessionLocal()
    try:
        imported_count = import_documents_to_db(documents, db)
        
        if imported_count > 0:
            logger.info(f"✅ Đã nhập thành công {imported_count} tài liệu vào database")
            
            # Đồng bộ Redis nếu có yêu cầu
            if args.sync_redis:
                logger.info("\n🔄 Đang đồng bộ vào Redis LSH index...")
                import subprocess
                try:
                    result = subprocess.run(
                        ['docker', 'restart', 'plagiarism-backend'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        logger.info("✅ Đã restart backend thành công")
                        logger.info("⏳ Đang chờ LSH index tải lại (15 giây)...")
                        import time
                        time.sleep(15)
                        logger.info("✅ Corpus đã sẵn sàng trong LSH index")
                    else:
                        logger.error(f"❌ Không thể restart backend: {result.stderr}")
                        sync_to_redis()
                except Exception as e:
                    logger.error(f"❌ Lỗi khi restart backend: {e}")
                    sync_to_redis()
            else:
                sync_to_redis()
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi nhập dữ liệu: {e}")
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()
    
    logger.info("\n✅ Hoàn tất!\n")


if __name__ == '__main__':
    main()