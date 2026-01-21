"""
Bulk Import Script - Nạp hàng loạt documents vào corpus
Hỗ trợ: .txt, .pdf, .docx
"""
import os
import sys
import redis
import json
from pathlib import Path
from tqdm import tqdm
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.plagiarism_checker import PlagiarismChecker
from app.services.preprocessing.text_normalizer import normalize_text
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.algorithm.shingling import create_shingles
from app.services.algorithm.minhash import create_minhash_signature
from app.config import settings


def extract_text_from_file(file_path: str) -> str:
    """Extract text from file"""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    elif ext == '.pdf':
        from app.services.preprocessing.pdf_extractor import extract_text_from_pdf
        return extract_text_from_pdf(file_path)
    
    elif ext == '.docx':
        from docx import Document
        doc = Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def bulk_import_corpus(
    data_dir: str,
    redis_host: str = 'localhost',
    redis_port: int = 6379,
    batch_size: int = 100,
    clear_existing: bool = False
):
    """
    Nạp hàng loạt documents vào corpus
    
    Args:
        data_dir: Thư mục chứa files (.txt, .pdf, .docx)
        redis_host: Redis host
        redis_port: Redis port
        batch_size: Số documents xử lý cùng lúc (để tối ưu Redis)
        clear_existing: Xóa corpus cũ trước khi import
    """
    
    # Connect Redis
    print(f"🔌 Connecting to Redis at {redis_host}:{redis_port}...")
    r = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=False)
    
    try:
        r.ping()
        print("✅ Redis connected!")
    except:
        print("❌ Cannot connect to Redis. Make sure Redis is running.")
        return
    
    # Clear existing corpus if requested
    if clear_existing:
        print("🗑️  Clearing existing corpus...")
        keys = r.keys("doc:sig:*") + r.keys("doc:meta:*")
        if keys:
            r.delete(*keys)
        print(f"✅ Deleted {len(keys)} keys")
    
    # Find all supported files
    print(f"\n📂 Scanning directory: {data_dir}")
    supported_exts = ['.txt', '.pdf', '.docx']
    files = []
    
    for ext in supported_exts:
        files.extend(Path(data_dir).rglob(f'*{ext}'))
    
    print(f"📊 Found {len(files)} files to import")
    
    if len(files) == 0:
        print("⚠️  No files found!")
        return
    
    # Process files with progress bar
    success_count = 0
    error_count = 0
    
    print("\n🚀 Starting import...")
    
    for i, file_path in enumerate(tqdm(files, desc="Processing"), 1):
        try:
            # Extract text
            text = extract_text_from_file(str(file_path))
            
            if not text.strip():
                print(f"\n⚠️  Skipped (empty): {file_path.name}")
                continue
            
            # Preprocess
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            shingles = create_shingles(tokens, k=settings.SHINGLE_SIZE)
            
            if len(shingles) == 0:
                print(f"\n⚠️  Skipped (no shingles): {file_path.name}")
                continue
            
            # Create MinHash
            minhash = create_minhash_signature(
                shingles,
                num_perm=settings.MINHASH_PERMUTATIONS,
                seed=settings.MINHASH_SEED
            )
            
            # Generate doc_id
            doc_id = f"bulk_{i}_{int(time.time())}"
            
            # Save to Redis
            # 1. Save MinHash signature
            r.set(f"doc:sig:{doc_id}", minhash.serialize())
            
            # 2. Save metadata
            metadata = {
                "title": file_path.stem,
                "author": "Unknown",
                "university": "Bulk Import",
                "year": 2024,
                "filename": file_path.name,
                "path": str(file_path),
                "word_count": len(tokens)
            }
            r.hset(f"doc:meta:{doc_id}", mapping=metadata)
            
            success_count += 1
            
            # Batch commit every N documents
            if i % batch_size == 0:
                print(f"\n💾 Batch committed: {i}/{len(files)}")
        
        except Exception as e:
            error_count += 1
            print(f"\n❌ Error processing {file_path.name}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 IMPORT SUMMARY")
    print("="*60)
    print(f"✅ Success: {success_count}")
    print(f"❌ Errors:  {error_count}")
    print(f"📁 Total:   {len(files)}")
    print("="*60)
    
    print("\n🔄 Restart backend to load new corpus into LSH index!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk import documents into corpus')
    parser.add_argument('data_dir', help='Directory containing documents')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser.add_argument('--clear', action='store_true', help='Clear existing corpus')
    
    args = parser.parse_args()
    
    bulk_import_corpus(
        data_dir=args.data_dir,
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        batch_size=args.batch_size,
        clear_existing=args.clear
    )
