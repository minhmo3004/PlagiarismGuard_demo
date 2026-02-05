#!/usr/bin/env python3
"""
Crawl ArXiv and Import to Corpus

Crawl academic papers from ArXiv preprint server and import to database.

Usage:
    # Crawl AI papers
    python scripts/crawl_arxiv_import.py --ai 50
    
    # Crawl machine learning papers
    python scripts/crawl_arxiv_import.py --ml 50
    
    # Crawl computer vision papers
    python scripts/crawl_arxiv_import.py --cv 30
    
    # Crawl Vietnamese-related papers
    python scripts/crawl_arxiv_import.py --vietnamese 100
    
    # Crawl and sync to Redis
    python scripts/crawl_arxiv_import.py --ai 50 --sync-redis

Examples:
    # Quick test
    python scripts/crawl_arxiv_import.py --ai 10
    
    # Large batch across categories
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
    
    for i, doc_data in enumerate(documents, 1):
        try:
            # Normalize and tokenize
            text = doc_data['content']
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            word_count = len(tokens)
            
            # Skip if too short (ArXiv papers should be substantial)
            if word_count < 100:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Too short ({word_count} words), skipped")
                skipped += 1
                continue
            
            # Check duplicate by hash
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            existing = db_session.query(Document).filter(
                Document.file_hash_sha256 == text_hash
            ).first()
            
            if existing:
                logger.warning(f"⚠️  [{i}/{len(documents)}] {doc_data['title'][:40]}... - Duplicate, skipped")
                skipped += 1
                continue
            
            # Create document record
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
                language='en',  # ArXiv is mostly English
                extraction_method='arxiv_crawler',
                extracted_text=text,
                is_corpus=1,  # Mark as corpus document
                status='indexed',
                indexed_at=datetime.now()
            )
            
            db_session.add(doc)
            imported += 1
            
            logger.info(f"✅ [{imported}/{len(documents)}] {doc_data['title'][:50]}... - {word_count} words")
            
            # Commit in batches
            if imported % 50 == 0:
                db_session.commit()
                logger.info(f"   💾 Committed {imported} documents...")
        
        except Exception as e:
            logger.error(f"❌ [{i}/{len(documents)}] Error: {e}")
            skipped += 1
    
    # Final commit
    db_session.commit()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ Import Summary:")
    logger.info(f"   • Successfully imported: {imported} documents")
    logger.info(f"   • Skipped/Failed: {skipped} documents")
    logger.info(f"   • Total processed: {len(documents)} documents")
    logger.info(f"{'='*70}\n")
    
    return imported


def sync_to_redis():
    """Sync corpus to Redis LSH index by restarting backend"""
    logger.info("\n⚠️  TO SYNC TO REDIS LSH INDEX:")
    logger.info("   Run: docker restart plagiarism-backend")
    logger.info("   Or use --sync-redis flag next time\n")


def main():
    parser = argparse.ArgumentParser(
        description='Crawl ArXiv papers and import to corpus database'
    )
    
    # Crawl mode selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ai', type=int, metavar='N',
                      help='Crawl N AI papers (cs.AI)')
    group.add_argument('--ml', type=int, metavar='N',
                      help='Crawl N machine learning papers (cs.LG)')
    group.add_argument('--cv', type=int, metavar='N',
                      help='Crawl N computer vision papers (cs.CV)')
    group.add_argument('--nlp', type=int, metavar='N',
                      help='Crawl N NLP papers (cs.CL)')
    group.add_argument('--vietnamese', type=int, metavar='N',
                      help='Crawl N Vietnamese-related papers')
    group.add_argument('--multi-category', type=int, metavar='N',
                      help='Crawl N papers from each major category')
    
    # Options
    parser.add_argument('--sync-redis', action='store_true',
                       help='Sync to Redis immediately after import (requires Docker)')
    
    args = parser.parse_args()
    
    # Initialize crawler
    crawler = ArxivCrawler(delay_seconds=3.0)
    
    logger.info("\n🚀 Starting ArXiv Crawler...")
    
    # Determine crawl mode and execute
    documents = []
    
    if args.ai:
        logger.info(f"Mode: AI papers (cs.AI, n={args.ai})")
        documents = crawler.crawl(query='', category='cs.AI', limit=args.ai)
        
    elif args.ml:
        logger.info(f"Mode: Machine Learning papers (cs.LG, n={args.ml})")
        documents = crawler.crawl(query='', category='cs.LG', limit=args.ml)
        
    elif args.cv:
        logger.info(f"Mode: Computer Vision papers (cs.CV, n={args.cv})")
        documents = crawler.crawl(query='', category='cs.CV', limit=args.cv)
        
    elif args.nlp:
        logger.info(f"Mode: NLP papers (cs.CL, n={args.nlp})")
        documents = crawler.crawl(query='', category='cs.CL', limit=args.nlp)
        
    elif args.vietnamese:
        logger.info(f"Mode: Vietnamese-related papers (n={args.vietnamese})")
        documents = crawler.search_vietnamese_ai(limit=args.vietnamese)
        
    elif args.multi_category:
        logger.info(f"Mode: Multi-category ({args.multi_category} per category)")
        categories = ['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.CR']
        documents = crawler.search_by_categories(
            query='',
            categories=categories,
            limit_per_cat=args.multi_category
        )
    
    # Import to database
    if documents:
        db = SessionLocal()
        try:
            imported = import_documents_to_db(documents, db)
            logger.info(f"✅ Successfully imported {imported} documents to database")
            
            # Sync to Redis if requested
            if args.sync_redis:
                logger.info("\n🔄 Syncing to Redis...")
                import subprocess
                try:
                    subprocess.run(['docker', 'restart', 'plagiarism-backend'], check=True)
                    logger.info("✅ Backend restarted - Redis will sync on startup")
                except Exception as e:
                    logger.error(f"❌ Failed to restart backend: {e}")
                    sync_to_redis()
            else:
                sync_to_redis()
                
        finally:
            db.close()
    else:
        logger.warning("❌ No documents crawled. Exiting...")
    
    logger.info("\n✅ Done!")


if __name__ == '__main__':
    main()
