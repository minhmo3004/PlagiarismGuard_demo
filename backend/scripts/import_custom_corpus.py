#!/usr/bin/env python3
"""
Import Custom Corpus from Text Files

Usage:
    # Trong container:
    python scripts/import_custom_corpus.py /path/to/text/files
    
    # Từ host (copy files vào container trước):
    docker cp /my/corpus plagiarism-backend:/data/corpus
    docker exec plagiarism-backend python scripts/import_custom_corpus.py /data/corpus
    docker restart plagiarism-backend
"""
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Document
from app.services.preprocessing.vietnamese_nlp import preprocess_vietnamese
from app.services.preprocessing.text_normalizer import normalize_text

def import_corpus(folder_path: str, author='Unknown', university='Unknown', year=2024):
    """
    Import text files from folder into corpus database
    
    Args:
        folder_path: Path to folder containing .txt files
        author: Default author name
        university: Default university
        year: Default publication year
    """
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return
    
    db = SessionLocal()
    count = 0
    failed = 0
    
    print(f"\n{'='*70}")
    print(f"📥 IMPORTING CUSTOM CORPUS")
    print(f"{'='*70}")
    print(f"Source: {folder_path}\n")
    
    txt_files = list(Path(folder_path).glob('*.txt'))
    total = len(txt_files)
    
    if total == 0:
        print("❌ No .txt files found")
        db.close()
        return
    
    print(f"Found {total} text files\n")
    
    for txt_file in txt_files:
        try:
            # Read file
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            if not text:
                print(f"⚠️  [{count+1}/{total}] {txt_file.name} - Empty file, skipped")
                failed += 1
                continue
            
            # Normalize and tokenize
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            word_count = len(tokens)
            
            # Validate word count (500-1000 recommended)
            if word_count < 100:
                print(f"⚠️  [{count+1}/{total}] {txt_file.name} - Too short ({word_count} words), skipped")
                failed += 1
                continue
            
            # Create document
            doc = Document(
                id=uuid.uuid4(),
                title=txt_file.stem[:500],  # Use filename as title (max 500 chars)
                author=author,
                university=university,
                year=year,
                extracted_text=text,
                word_count=word_count,
                status='indexed',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.add(doc)
            count += 1
            
            # Show progress
            print(f"✅ [{count}/{total}] {txt_file.name} - {word_count} words")
            
            # Commit batch
            if count % 100 == 0:
                db.commit()
                print(f"   💾 Committed {count} documents...")
        
        except Exception as e:
            print(f"❌ [{count+1}/{total}] {txt_file.name} - Error: {e}")
            failed += 1
    
    # Final commit
    db.commit()
    db.close()
    
    # Summary
    print(f"\n{'='*70}")
    print(f"✅ Import completed:")
    print(f"   • Successfully imported: {count} documents")
    print(f"   • Failed/Skipped: {failed} files")
    print(f"   • Total processed: {total} files")
    print(f"{'='*70}")
    print(f"\n⚠️  IMPORTANT: Restart backend to sync to Redis LSH index:")
    print(f"   docker restart plagiarism-backend\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_custom_corpus.py <folder_path> [author] [university] [year]")
        print("\nExample:")
        print("  python import_custom_corpus.py /data/corpus")
        print("  python import_custom_corpus.py /data/corpus 'Nguyễn Văn A' 'ĐHBK HN' 2024")
        sys.exit(1)
    
    folder = sys.argv[1]
    author = sys.argv[2] if len(sys.argv) > 2 else 'Unknown'
    university = sys.argv[3] if len(sys.argv) > 3 else 'Unknown'
    year = int(sys.argv[4]) if len(sys.argv) > 4 else 2024
    
    import_corpus(folder, author, university, year)
