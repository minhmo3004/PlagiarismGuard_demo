#!/usr/bin/env python3
"""
Script sửa chữa schema cơ sở dữ liệu
Kiểm tra và tự động thêm các cột bị thiếu trong bảng documents
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Thêm đường dẫn backend vào Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


def fix_db_schema():
    print("🚀 Đang kiểm tra schema cơ sở dữ liệu để bổ sung các cột bị thiếu...")
    
    # Tạo engine trực tiếp từ settings
    engine = create_engine(settings.DATABASE_URL)
    
    # Danh sách các cột cần kiểm tra và thêm (Tên cột, Kiểu dữ liệu)
    columns_to_add = [
        ("page_count", "INTEGER"),
        ("error_message", "TEXT"),
        ("topic", "VARCHAR(255)"),
        ("owner_id", "UUID"),
        ("s3_path", "VARCHAR(500)")
    ]
    
    try:
        with engine.connect() as conn:
            # Kiểm tra bảng documents có tồn tại không
            res = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'documents');"))
            if not res.scalar():
                print("❌ Bảng 'documents' chưa tồn tại. Vui lòng chạy migration ban đầu trước.")
                return
            
            for col_name, col_type in columns_to_add:
                # Kiểm tra cột đã tồn tại chưa
                check_sql = text(f"""
                    SELECT count(*) 
                    FROM information_schema.columns 
                    WHERE table_name='documents' AND column_name='{col_name}';
                """)
                exists = conn.execute(check_sql).scalar()
                
                if exists == 0:
                    print(f"➕ Đang thêm cột bị thiếu: {col_name} ({col_type})")
                    try:
                        # Thêm cột (đối với owner_id tạm thời không thêm ràng buộc foreign key)
                        alter_sql = text(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type};")
                        conn.execute(alter_sql)
                        conn.commit()  # Commit để đảm bảo an toàn với một số driver
                        print(f"✅ Đã thêm cột {col_name} thành công.")
                    except Exception as e:
                        print(f"⚠️  Lỗi khi thêm cột {col_name}: {e}")
                else:
                    print(f"ℹ️  Cột {col_name} đã tồn tại.")
            
            print("\n🎉 Hoàn tất cập nhật schema cơ sở dữ liệu!")
            
    except Exception as e:
        print(f"❌ Lỗi kết nối cơ sở dữ liệu: {e}")


if __name__ == "__main__":
    fix_db_schema()