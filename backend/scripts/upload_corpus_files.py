#!/usr/bin/env python3
"""
Upload Corpus Files to MinIO + PostgreSQL + Redis

Upload .txt, .docx, .pdf files from a local directory directly into the system.

Usage:
    # Upload all files from a folder
    python scripts/upload_corpus_files.py --dir /path/to/corpus/files

    # Upload with custom metadata
    python scripts/upload_corpus_files.py --dir /path/to/files --author "Nguyen Van A" --university "DH CNTT"

    # Upload and sync to Redis immediately
    python scripts/upload_corpus_files.py --dir /path/to/files --sync-redis

    # Limit to 100 files
    python scripts/upload_corpus_files.py --dir /path/to/files --limit 100

Examples:
    # Quick: upload 100 txt files
    python scripts/upload_corpus_files.py --dir /app/corpus_data --limit 100 --sync-redis
"""
import os
import sys
import uuid
import hashlib
import argparse
from datetime import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.db.database import SessionLocal
from app.db.models import Document
from app.services.minio_storage import get_minio_storage
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.preprocessing.text_normalizer import normalize_text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.txt', '.docx', '.pdf', '.doc'}


def extract_text_from_file(filepath: str) -> str:
    """Extract text content from a file"""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    elif ext == '.docx':
        try:
            import docx
            doc = docx.Document(filepath)
            return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            logger.warning("python-docx not installed. Run: pip install python-docx")
            return ""
    
    elif ext == '.pdf':
        try:
            import PyPDF2
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                return '\n'.join(page.extract_text() or '' for page in reader.pages)
        except ImportError:
            logger.warning("PyPDF2 not installed. Run: pip install PyPDF2")
            return ""
    
    return ""


def upload_corpus(args):
    """Upload corpus files from directory"""
    directory = args.dir
    if not os.path.isdir(directory):
        logger.error(f"❌ Directory not found: {directory}")
        sys.exit(1)
    
    # Collect files
    files = []
    for f in sorted(os.listdir(directory)):
        ext = os.path.splitext(f)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            files.append(os.path.join(directory, f))
    
    if args.limit:
        files = files[:args.limit]
    
    if not files:
        logger.error(f"❌ No supported files found in {directory}")
        sys.exit(1)
    
    logger.info(f"\n{'='*70}")
    logger.info(f"📤 UPLOADING {len(files)} CORPUS FILES")
    logger.info(f"   Source: {directory}")
    logger.info(f"{'='*70}\n")
    
    db = SessionLocal()
    minio = get_minio_storage()
    minio_available = minio.is_available()
    
    if not minio_available:
        logger.warning("⚠️  MinIO not available. Files will be saved to PostgreSQL only.")
    
    uploaded = 0
    skipped = 0
    seen_hashes = set()
    
    for i, filepath in enumerate(files, 1):
        filename = os.path.basename(filepath)
        try:
            # Extract text
            text = extract_text_from_file(filepath)
            if not text or len(text.strip()) < 50:
                logger.warning(f"⚠️  [{i}/{len(files)}] {filename} - Too short or empty, skipped")
                skipped += 1
                continue
            
            # Check duplicate
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            if text_hash in seen_hashes:
                logger.warning(f"⚠️  [{i}/{len(files)}] {filename} - Duplicate in batch, skipped")
                skipped += 1
                continue
            
            existing = db.query(Document).filter(Document.file_hash_sha256 == text_hash).first()
            if existing:
                logger.warning(f"⚠️  [{i}/{len(files)}] {filename} - Already in DB, skipped")
                seen_hashes.add(text_hash)
                skipped += 1
                continue
            
            # Process text
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            word_count = len(tokens)
            
            # Derive title from filename
            title = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ')
            doc_id = uuid.uuid4()
            year = args.year or datetime.now().year
            
            # Save to PostgreSQL
            doc = Document(
                id=doc_id,
                title=title[:500],
                author=args.author or 'Unknown',
                university=args.university or 'Unknown',
                year=year,
                original_filename=filename,
                file_hash_sha256=text_hash,
                file_size_bytes=os.path.getsize(filepath),
                word_count=word_count,
                language='vi',
                extraction_method='file_upload',
                extracted_text=text,
                is_corpus=1,
                status='indexed',
                indexed_at=datetime.now()
            )
            
            db.add(doc)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"⚠️  [{i}/{len(files)}] {filename} - DB error: {str(e)[:60]}")
                skipped += 1
                continue
            
            # Upload to MinIO
            if minio_available:
                minio.upload_corpus_document(
                    doc_id=str(doc_id),
                    title=title,
                    text=text,
                    author=args.author or 'Unknown',
                    university=args.university or 'Unknown',
                    year=year
                )
            
            seen_hashes.add(text_hash)
            uploaded += 1
            logger.info(f"✅ [{uploaded}/{len(files)}] {filename} - {word_count} words")
        
        except Exception as e:
            logger.error(f"❌ [{i}/{len(files)}] {filename} - Error: {e}")
            try:
                db.rollback()
            except Exception:
                pass
            skipped += 1
    
    db.close()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ Upload Summary:")
    logger.info(f"   • Uploaded: {uploaded}")
    logger.info(f"   • Skipped: {skipped}")
    logger.info(f"   • MinIO: {'✅' if minio_available else '❌ Not available'}")
    logger.info(f"{'='*70}\n")
    
    # Sync to Redis
    if args.sync_redis and uploaded > 0:
        logger.info("🔄 Restarting backend to sync Redis LSH index...")
        import subprocess
        try:
            subprocess.run(['docker', 'restart', 'plagiarism-backend'], check=True, timeout=30)
            logger.info("✅ Backend restarted. Redis will sync on startup.")
        except Exception:
            logger.info("⚠️  Could not restart. Run manually: docker restart plagiarism-backend")


def main():
    parser = argparse.ArgumentParser(description='Upload corpus files to MinIO + PostgreSQL')
    parser.add_argument('--dir', required=True, help='Directory containing corpus files (.txt, .docx, .pdf)')
    parser.add_argument('--limit', type=int, help='Max number of files to upload')
    parser.add_argument('--author', type=str, help='Author name for all files')
    parser.add_argument('--university', type=str, help='University name for all files')
    parser.add_argument('--year', type=int, help='Publication year')
    parser.add_argument('--sync-redis', action='store_true', help='Sync to Redis after upload')
    args = parser.parse_args()
    upload_corpus(args)


if __name__ == '__main__':
    main()
