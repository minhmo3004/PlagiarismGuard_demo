#!/usr/bin/env python3
"""
XÁC THỰC CORPUS - Kiểm tra corpus có đạt yêu cầu không

Kiểm tra corpus có đủ 3000+ tài liệu, mỗi tài liệu từ 500-1000 từ.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import Document
from sqlalchemy import func


def main():
    db = SessionLocal()
    
    # Tổng số tài liệu đã lập chỉ mục
    total = db.query(Document).filter(Document.status == 'indexed').count()
    
    print(f"\n{'='*70}")
    print(f"📊 BÁO CÁO XÁC THỰC CORPUS")
    print(f"{'='*70}\n")
    print(f"✅ Tổng số tài liệu: {total:,}")
    
    # Phân bố theo số từ
    ranges = [
        ('< 500 từ', 0, 499),
        ('500-1000 từ (MỤC TIÊU)', 500, 1000),
        ('> 1000 từ', 1001, 10000)
    ]
    
    print(f"\n📈 Phân bố số từ:")
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
        print(f"  {label:30} {count:6,} tài liệu ({pct:5.1f}%)")
    
    # Thống kê số từ
    stats = db.query(
        func.min(Document.word_count).label('min'),
        func.max(Document.word_count).label('max'),
        func.avg(Document.word_count).label('avg')
    ).filter(Document.status == 'indexed').first()
    
    print(f"\n📊 Thống kê số từ:")
    print(f"{'-'*70}")
    print(f"  Nhỏ nhất:  {stats.min:4} từ")
    print(f"  Lớn nhất:  {stats.max:4} từ")
    print(f"  Trung bình: {int(stats.avg):4} từ")
    
    # Kiểm tra yêu cầu mục tiêu
    target_count = range_counts['500-1000 từ (MỤC TIÊU)']
    
    print(f"\n{'='*70}")
    print(f"🎯 KIỂM TRA YÊU CẦU:")
    print(f"{'-'*70}")
    
    # Kiểm tra các tiêu chí
    req_total = total >= 3000
    req_range = target_count >= 3000
    
    print(f"  Yêu cầu 1: ≥ 3000 tài liệu")
    print(f"    Trạng thái: {'✅ ĐẠT' if req_total else '❌ CHƯA ĐẠT'} ({total:,} tài liệu)")
    print()
    print(f"  Yêu cầu 2: ≥ 3000 tài liệu trong khoảng 500-1000 từ")  
    print(f"    Trạng thái: {'✅ ĐẠT' if req_range else '❌ CHƯA ĐẠT'} ({target_count:,} tài liệu)")
    print()
    
    if req_total and req_range:
        print(f"✅ ĐÃ ĐẠT TOÀN BỘ YÊU CẦU!")
        print(f"   • Tổng số tài liệu: {total:,}")
        print(f"   • Số tài liệu trong khoảng mục tiêu (500-1000 từ): {target_count:,}")
    elif req_total:
        print(f"⚠️  ĐẠT MỘT PHẦN: Có {total:,} tài liệu, nhưng chỉ có {target_count:,} tài liệu trong khoảng 500-1000 từ")
        missing = 3000 - target_count
        print(f"   • Cần thêm {missing:,} tài liệu trong khoảng 500-1000 từ")
    else:
        print(f"❌ CHƯA ĐẠT: Chỉ có {total:,} tài liệu (cần ít nhất 3000)")
        missing = 3000 - total
        print(f"   • Cần thêm {missing:,} tài liệu")
    
    print(f"{'='*70}\n")
    
    db.close()
    
    # Exit code: 0 nếu đạt tất cả yêu cầu, 1 nếu chưa đạt
    sys.exit(0 if (req_total and req_range) else 1)


if __name__ == '__main__':
    main()