"""
Cấu hình và khởi tạo kết nối cơ sở dữ liệu
Sử dụng SQLAlchemy với PostgreSQL (hoặc database tương thích)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Tạo engine đồng bộ (sử dụng psycopg2 driver)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Tạo factory để sinh session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class cho các model declarative
Base = declarative_base()


def get_db():
    """
    Dependency để cung cấp database session cho FastAPI
    
    Sử dụng trong các route bằng Depends(get_db)
    Đảm bảo session được đóng sau khi sử dụng
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Tạo tất cả các bảng trong cơ sở dữ liệu tự động.
    
    Hàm này nên được gọi khi ứng dụng khởi động (thường trong main.py hoặc lifespan).
    """
    # Import tất cả models để chúng được đăng ký với Base
    from app.db import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)
    print("✅ Các bảng cơ sở dữ liệu đã được tạo/kiểm tra thành công")