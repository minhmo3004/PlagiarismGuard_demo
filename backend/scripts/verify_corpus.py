#!/usr/bin/env python3
"""
Verify Corpus - Check corpus meets requirements
Kiểm tra corpus có đủ 3000+ documents, mỗi doc 500-1000 words
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Document
from sqlalchemy import func

def main():
    db = SessionLocal()
    
    # Total documents
    total = db.query(Document).filter(Document.status == 'indexed').count()
    
    print(f"\n{'='*70}")
    print(f"📊 CORPUS VERIFICATION REPORT")
    print(f"{'='*70}\n")
    print(f"✅ Total documents: {total:,}")
    
    # Word count ranges
    ranges = [
        ('< 500 từ', 0, 499),
        ('500-1000 từ (MỤC TIÊU)', 500, 1000),
        ('> 1000 từ', 1001, 10000)
    ]
    
    print(f"\n📈 Word Count Distribution:")
    print(f"{'-'*70}")
    
    range_counts = {}
    for label, min_w, max_w in ranges:
        count = db.query(Document).filter(
            Document.status == 'indexed',
            Document.word_count >= min_w,
            Document.word_count <= max_w
        ).count()
        pct = (count / total * 100) if total > 0 else 0
        range_counts[label] = count
        print(f"  {label:30} {count:6,} docs ({pct:5.1f}%)")
    
    # Statistics
    stats = db.query(
        func.min(Document.word_count).label('min'),
        func.max(Document.word_count).label('max'),
        func.avg(Document.word_count).label('avg')
    ).filter(Document.status == 'indexed').first()
    
    print(f"\n📊 Word Count Statistics:")
    print(f"{'-'*70}")
    print(f"  Minimum:  {stats.min:4} words")
    print(f"  Maximum:  {stats.max:4} words")
    print(f"  Average:  {int(stats.avg):4} words")
    
    # Check target
    target_count = range_counts['500-1000 từ (MỤC TIÊU)']
    
    print(f"\n{'='*70}")
    print(f"🎯 TARGET VERIFICATION:")
    print(f"{'-'*70}")
    
    # Check requirements
    req_total = total >= 3000
    req_range = target_count >= 3000
    
    print(f"  Requirement 1: ≥ 3000 documents")
    print(f"    Status: {'✅ PASS' if req_total else '❌ FAIL'} ({total:,} docs)")
    print()
    print(f"  Requirement 2: ≥ 3000 docs in 500-1000 word range")  
    print(f"    Status: {'✅ PASS' if req_range else '❌ FAIL'} ({target_count:,} docs)")
    print()
    
    if req_total and req_range:
        print(f"✅ ALL REQUIREMENTS MET!")
        print(f"   • {total:,} total documents")
        print(f"   • {target_count:,} docs in target range (500-1000 words)")
    elif req_total:
        print(f"⚠️  PARTIAL: {total:,} docs total, but only {target_count:,} in 500-1000 range")
        missing = 3000 - target_count
        print(f"   • Need {missing:,} more docs in 500-1000 word range")
    else:
        print(f"❌ NOT MET: Only {total:,} documents (need 3000+)")
        missing = 3000 - total
        print(f"   • Need {missing:,} more documents")
    
    print(f"{'='*70}\n")
    
    db.close()
    
    # Exit code: 0 if all requirements met, 1 otherwise
    sys.exit(0 if (req_total and req_range) else 1)

if __name__ == '__main__':
    main()
