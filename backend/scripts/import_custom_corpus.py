#!/usr/bin/env python3
"""
Import Corpus Tùy Chỉnh từ các file Text

Script này dùng để nhập các file văn bản (.txt) vào corpus của hệ thống.

Cách sử dụng:
    # Bên trong container:
    python scripts/import_custom_corpus.py /path/to/text/files
    
    # Từ máy host (copy file vào container trước):
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
    Nhập các file văn bản từ thư mục vào cơ sở dữ liệu corpus
    
    Args:
        folder_path: Đường dẫn đến thư mục chứa các file .txt
        author: Tên tác giả mặc định
        university: Tên trường đại học / tổ chức mặc định
        year: Năm xuất bản mặc định
    """
    if not os.path.exists(folder_path):
        print(f"❌ Không tìm thấy thư mục: {folder_path}")
        return
    
    db = SessionLocal()
    count = 0
    failed = 0
    
    print(f"\n{'='*70}")
    print(f"📥 ĐANG NHẬP CORPUS TÙY CHỈNH")
    print(f"{'='*70}")
    print(f"Nguồn: {folder_path}\n")
    
    txt_files = list(Path(folder_path).glob('*.txt'))
    total = len(txt_files)
    
    if total == 0:
        print("❌ Không tìm thấy file .txt nào trong thư mục")
        db.close()
        return
    
    print(f"Tìm thấy {total} file văn bản\n")
    
    for txt_file in txt_files:
        try:
            # Đọc nội dung file
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            if not text:
                print(f"⚠️  [{count+1}/{total}] {txt_file.name} - File rỗng, bỏ qua")
                failed += 1
                continue
            
            # Chuẩn hóa và tokenize văn bản
            normalized = normalize_text(text)
            tokens = preprocess_vietnamese(normalized)
            word_count = len(tokens)
            
            # Kiểm tra độ dài (khuyến nghị tối thiểu 100 từ)
            if word_count < 100:
                print(f"⚠️  [{count+1}/{total}] {txt_file.name} - Quá ngắn ({word_count} từ), bỏ qua")
                failed += 1
                continue
            
            # Tạo bản ghi Document
            doc = Document(
                id=uuid.uuid4(),
                title=txt_file.stem[:500],   # Dùng tên file làm tiêu đề (tối đa 500 ký tự)
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
            
            # Hiển thị tiến độ
            print(f"✅ [{count}/{total}] {txt_file.name} - {word_count} từ")
            
            # Commit theo batch
            if count % 100 == 0:
                db.commit()
                print(f"   💾 Đã lưu {count} tài liệu...")
        
        except Exception as e:
            print(f"❌ [{count+1}/{total}] {txt_file.name} - Lỗi: {e}")
            failed += 1
    
    # Commit lần cuối
    db.commit()
    db.close()
    
    # Tóm tắt kết quả
    print(f"\n{'='*70}")
    print(f"✅ Hoàn tất nhập corpus:")
    print(f"   • Nhập thành công: {count} tài liệu")
    print(f"   • Bỏ qua / Lỗi: {failed} file")
    print(f"   • Tổng số file đã xử lý: {total} file")
    print(f"{'='*70}")
    print(f"\n⚠️  QUAN TRỌNG: Hãy restart backend để đồng bộ vào Redis LSH index:")
    print(f"   docker restart plagiarism-backend\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Cách dùng: python import_custom_corpus.py <đường_dẫn_thư_mục> [tác_giả] [trường] [năm]")
        print("\nVí dụ:")
        print("  python import_custom_corpus.py /data/corpus")
        print("  python import_custom_corpus.py /data/corpus 'Nguyễn Văn A' 'ĐHBK HN' 2024")
        sys.exit(1)
    
    folder = sys.argv[1]
    author = sys.argv[2] if len(sys.argv) > 2 else 'Unknown'
    university = sys.argv[3] if len(sys.argv) > 3 else 'Unknown'
    year = int(sys.argv[4]) if len(sys.argv) > 4 else 2024
    
    import_corpus(folder, author, university, year)