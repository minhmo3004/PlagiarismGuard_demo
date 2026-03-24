"""
Điểm vào (Entry Point) của ứng dụng FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Xử lý sự kiện khởi động và tắt ứng dụng
    
    - Khởi động: Tạo các bảng trong database
    - Tắt ứng dụng: Dọn dẹp nếu cần (hiện tại chưa có)
    """
    # Khởi động ứng dụng
    init_db()
    yield
    # Tắt ứng dụng - dọn dẹp nếu cần
    pass


# Tạo ứng dụng FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware - cho phép localhost trong quá trình phát triển
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint kiểm tra sức khỏe cơ bản (health check)"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Endpoint kiểm tra sức khỏe chi tiết"""
    return {
        "status": "healthy",
        "database": "connected",   # TODO: Thực hiện kiểm tra kết nối DB thật
        "redis": "connected",      # TODO: Thực hiện kiểm tra kết nối Redis thật
    }


# Đăng ký các router API
from app.api.routes import auth, check, plagiarism

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(check.router, prefix=settings.API_V1_PREFIX)
app.include_router(plagiarism.router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )