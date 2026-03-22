from minio import Minio
from minio.error import S3Error
from app.config import settings
import io
import logging

logger = logging.getLogger(__name__)


class S3Storage:
    """Dịch vụ lưu trữ file sử dụng MinIO (chuẩn S3)"""
    
    def __init__(self):
        """
        Khởi tạo kết nối tới MinIO/S3
        """
        endpoint_raw = settings.S3_ENDPOINT or ""
        
        # Xác định có sử dụng HTTPS hay không
        secure = False
        if endpoint_raw.startswith("https://"):
            secure = True
        
        # Chuẩn hóa endpoint (loại bỏ http/https và dấu '/')
        endpoint = endpoint_raw.replace("https://", "").replace("http://", "").rstrip('/')

        # Khởi tạo client MinIO
        self.client = Minio(
            endpoint,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=secure,
        )

        # Đảm bảo bucket tồn tại
        try:
            if not self.client.bucket_exists(settings.S3_BUCKET):
                self.client.make_bucket(settings.S3_BUCKET)
        except Exception as e:
            logger.warning(f"Lỗi khi kiểm tra/tạo bucket MinIO: {e}")

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """
        Upload dữ liệu dạng bytes lên MinIO
        
        Args:
            data: Dữ liệu dạng bytes
            object_name: Tên object (đường dẫn file trên bucket)
            content_type: Kiểu nội dung (MIME type)
        
        Returns:
            Đường dẫn object dưới dạng: bucket/object_name
        """
        try:
            # Chuyển bytes thành file-like object
            data_io = io.BytesIO(data)
            data_io.seek(0)
            
            # Upload lên MinIO
            self.client.put_object(
                settings.S3_BUCKET,
                object_name,
                data_io,
                length=len(data),
                content_type=content_type,
            )
            
            return f"{settings.S3_BUCKET}/{object_name}"
        
        except S3Error as e:
            logger.error(f"Lỗi upload MinIO: {e}")
            raise

    def download_to_path(self, object_name: str, local_path: str) -> None:
        """
        Tải file từ MinIO về máy local
        
        Args:
            object_name: Tên object trên bucket
            local_path: Đường dẫn lưu file trên máy local
        """
        try:
            self.client.fget_object(settings.S3_BUCKET, object_name, local_path)
        except Exception as e:
            logger.error(f"Lỗi download MinIO: {e}")
            raise