#!/usr/bin/env python3
"""Quick script to check Wikipedia articles in corpus"""
import sys
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.db.models import Document
from sqlalchemy import func

db = SessionLocal()

# Total corpus
total = db.query(func.count(Document.id)).filter(Document.is_corpus == 1).scalar()

# Wikipedia articles
wiki = db.query(func.count(Document.id)).filter(
    Document.extraction_method == 'wikipedia_crawler'
).scalar()

# ArXiv papers
arxiv = db.query(func.count(Document.id)).filter(
    Document.extraction_method == 'arxiv_crawler'
).scalar()

# Synthetic articles
synthetic = total - wiki - arxiv

print(f"\n📊 CORPUS STATISTICS")
print(f"{'='*50}")
print(f"Total corpus documents: {total:,}")
print(f"  • Wikipedia articles: {wiki:,} ({wiki/total*100:.1f}%)")
print(f"  • ArXiv papers: {arxiv:,} ({arxiv/total*100:.1f}%)")
print(f"  • Synthetic documents: {synthetic:,} ({synthetic/total*100:.1f}%)")
print(f"{'='*50}\n")

# Recent Wikipedia articles
recent = db.query(Document.title, Document.word_count).filter(
    Document.extraction_method == 'wikipedia_crawler'
).order_by(Document.created_at.desc()).limit(10).all()

if recent:
    print(f"📝 Recent Wikipedia Articles (last 10):")
    print(f"{'-'*50}")
    for i, (title, wc) in enumerate(recent, 1):
        print(f"{i:2}. {title[:42]:42} ({wc:4} words)")
    print()

# Recent ArXiv papers
recent_arxiv = db.query(Document.title, Document.word_count).filter(
    Document.extraction_method == 'arxiv_crawler'
).order_by(Document.created_at.desc()).limit(10).all()

if recent_arxiv:
    print(f"📄 Recent ArXiv Papers (last 10):")
    print(f"{'-'*50}")
    for i, (title, wc) in enumerate(recent_arxiv, 1):
        print(f"{i:2}. {title[:42]:42} ({wc:4} words)")
    print()

db.close()
