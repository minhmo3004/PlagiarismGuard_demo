#!/usr/bin/env python3
"""
Script nhanh để kiểm tra số lượng và chất lượng bài viết Wikipedia trong corpus
"""

import sys
sys.path.insert(0, '/app')

from app.db.database import SessionLocal
from app.db.models import Document
from sqlalchemy import func

db = SessionLocal()

# Tổng số tài liệu trong corpus
total = db.query(func.count(Document.id)).filter(Document.is_corpus == 1).scalar()

# Bài viết từ Wikipedia
wiki = db.query(func.count(Document.id)).filter(
    Document.extraction_method == 'wikipedia_crawler'
).scalar()

# Bài báo từ ArXiv
arxiv = db.query(func.count(Document.id)).filter(
    Document.extraction_method == 'arxiv_crawler'
).scalar()

# Tài liệu tổng hợp (synthetic)
synthetic = total - wiki - arxiv

print(f"\n📊 THỐNG KÊ CORPUS")
print(f"{'='*50}")
print(f"Tổng số tài liệu trong corpus: {total:,}")
print(f"  • Bài viết Wikipedia: {wiki:,} ({wiki/total*100:.1f}%)")
print(f"  • Bài báo ArXiv: {arxiv:,} ({arxiv/total*100:.1f}%)")
print(f"  • Tài liệu tổng hợp: {synthetic:,} ({synthetic/total*100:.1f}%)")
print(f"{'='*50}\n")

# 10 bài viết Wikipedia gần đây nhất
recent = db.query(Document.title, Document.word_count).filter(
    Document.extraction_method == 'wikipedia_crawler'
).order_by(Document.created_at.desc()).limit(10).all()

if recent:
    print(f"📝 10 bài viết Wikipedia gần đây nhất:")
    print(f"{'-'*50}")
    for i, (title, wc) in enumerate(recent, 1):
        print(f"{i:2}. {title[:42]:42} ({wc:4} từ)")
    print()

# 10 bài báo ArXiv gần đây nhất
recent_arxiv = db.query(Document.title, Document.word_count).filter(
    Document.extraction_method == 'arxiv_crawler'
).order_by(Document.created_at.desc()).limit(10).all()

if recent_arxiv:
    print(f"📄 10 bài báo ArXiv gần đây nhất:")
    print(f"{'-'*50}")
    for i, (title, wc) in enumerate(recent_arxiv, 1):
        print(f"{i:2}. {title[:42]:42} ({wc:4} từ)")
    print()

db.close()