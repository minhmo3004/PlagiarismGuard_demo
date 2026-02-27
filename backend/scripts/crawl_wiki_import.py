#!/usr/bin/env python3
"""
Crawl Wikipedia and Import to Corpus

Crawl Vietnamese Wikipedia articles and import directly to database.

Usage:
    # Crawl 100 random articles
    python scripts/crawl_wiki_import.py --random 100
    
    # Crawl from tech categories (20 articles per category)
    python scripts/crawl_wiki_import.py --tech-categories 20
    
    # Crawl specific category
    python scripts/crawl_wiki_import.py --category "Khoa_học_máy_tính" --limit 50
    
    # Crawl and sync to Redis immediately
    python scripts/crawl_wiki_import.py --random 100 --sync-redis

Examples:
    # Quick test
    python scripts/crawl_wiki_import.py --random 10
    
    # Large batch from tech categories
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def import_documents_to_db(documents: list, db_session) -> int:
    """
    Import crawled documents to PostgreSQL database
    
    Args:
        documents: List of document dicts from crawler
        db_session: SQLAlchemy database session
        
    Returns:
        Number of successfully imported documents
    """
    imported = 0
    skipped = 0
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📥 IMPORTING {len(documents)} DOCUMENTS TO DATABASE")
    logger.info(f"{'='*70}\n")
    
    # Track hashes we've seen in this session to avoid in-batch duplicates
    seen_hashes = set()
    
    for i, doc_data in enumerate(documents, 1):
        try:
            # Normalize and tokenize
            text = doc_data['content']
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            word_count = len(tokens)
            
            # Skip if too short (minimum 50 words for Wikipedia stubs)
            if word_count < 50:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Too short ({word_count} words), skipped")
                skipped += 1
                continue
            
            # Check duplicate by hash (in-memory + database)
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            if text_hash in seen_hashes:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Duplicate in batch, skipped")
                skipped += 1
                continue
            
            existing = db_session.query(Document).filter(
                Document.file_hash_sha256 == text_hash
            ).first()
            
            if existing:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Duplicate in DB, skipped")
                seen_hashes.add(text_hash)
                skipped += 1
                continue
            
            # Create document record
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
                is_corpus=1,  # Mark as corpus document
                status='indexed',
                indexed_at=datetime.now()
            )
            
            # Commit each document individually to prevent cascade failures
            db_session.add(doc)
            try:
                db_session.commit()
                seen_hashes.add(text_hash)
                imported += 1
                logger.info(f"✅ [{imported}/{len(documents)}] {doc_data['title'][:50]}... - {word_count} words")
            except Exception as commit_err:
                db_session.rollback()
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - DB error, skipped: {str(commit_err)[:80]}")
                seen_hashes.add(text_hash)
                skipped += 1
        
        except Exception as e:
            logger.error(f"❌ [{i}/{len(documents)}] Error: {e}")
            try:
                db_session.rollback()
            except Exception:
                pass
            skipped += 1
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ Import Summary:")
    logger.info(f"   • Successfully imported: {imported} documents")
    logger.info(f"   • Skipped/Failed: {skipped} documents")
    logger.info(f"   • Total processed: {len(documents)} documents")
    logger.info(f"{'='*70}\n")
    
    return imported


def sync_to_redis():
    """
    Sync corpus to Redis LSH index by restarting backend
    """
    logger.info("\n⚠️  TO SYNC TO REDIS LSH INDEX:")
    logger.info("   Run: docker restart plagiarism-backend")
    logger.info("   Or use --sync-redis flag next time\n")


def main():
    parser = argparse.ArgumentParser(
        description='Crawl Vietnamese Wikipedia and import to corpus database'
    )
    
    # Crawl mode selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--random', type=int, metavar='N',
                      help='Crawl N random articles')
    group.add_argument('--tech-categories', type=int, metavar='N',
                      help='Crawl N articles from each tech category')
    group.add_argument('--category', type=str,
                      help='Crawl from specific category (requires --limit)')
    
    # Options
    parser.add_argument('--limit', type=int, default=50,
                       help='Limit for category crawl (default: 50)')
    parser.add_argument('--sync-redis', action='store_true',
                       help='Sync to Redis immediately after import (requires Docker)')
    parser.add_argument('--delay', type=float, default=1.5,
                       help='Delay between requests in seconds (default: 1.5)')
    
    args = parser.parse_args()
    
    # Initialize crawler
    logger.info("\n🚀 Starting Wikipedia Crawler...")
    crawler = ViWikiCrawler(delay_seconds=args.delay)
    
    # Crawl based on mode
    documents = []
    
    try:
        if args.random:
            logger.info(f"Mode: Random articles (n={args.random})")
            documents = crawler.crawl(limit=args.random)
        
        elif args.tech_categories:
            logger.info(f"Mode: Tech categories ({args.tech_categories} per category)")
            documents = crawler.crawl_tech_categories(limit_per_category=args.tech_categories)
        
        elif args.category:
            logger.info(f"Mode: Specific category '{args.category}' (limit={args.limit})")
            documents = crawler.crawl_category(args.category, limit=args.limit)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Crawling interrupted by user")
        if documents:
            logger.info(f"Proceeding to import {len(documents)} crawled documents...")
        else:
            logger.info("No documents crawled. Exiting...")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"❌ Crawling error: {e}")
        sys.exit(1)
    
    # Check if we got documents
    if not documents:
        logger.warning("❌ No documents crawled. Exiting...")
        sys.exit(1)
    
    # Import to database
    db = SessionLocal()
    try:
        imported_count = import_documents_to_db(documents, db)
        
        if imported_count > 0:
            logger.info(f"✅ Successfully imported {imported_count} documents to database")
            
            # Sync to Redis if requested
            if args.sync_redis:
                logger.info("\n🔄 Syncing to Redis LSH index...")
                import subprocess
                try:
                    result = subprocess.run(
                        ['docker', 'restart', 'plagiarism-backend'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        logger.info("✅ Backend restarted successfully")
                        logger.info("⏳ Waiting for LSH index to load (15 seconds)...")
                        import time
                        time.sleep(15)
                        logger.info("✅ Corpus should now be available in LSH index")
                    else:
                        logger.error(f"❌ Failed to restart backend: {result.stderr}")
                        sync_to_redis()
                except Exception as e:
                    logger.error(f"❌ Error restarting backend: {e}")
                    sync_to_redis()
            else:
                sync_to_redis()
        
    except Exception as e:
        logger.error(f"❌ Import error: {e}")
        db.rollback()
        sys.exit(1)
    
    finally:
        db.close()
    
    logger.info("\n✅ Done!\n")


if __name__ == '__main__':
    main()
