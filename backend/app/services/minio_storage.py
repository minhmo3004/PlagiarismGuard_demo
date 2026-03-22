"""
Dịch vụ lưu trữ MinIO
Xử lý việc upload/download file lên MinIO (hệ thống lưu trữ tương thích S3)
"""
import os
import uuid
from typing import Optional
from datetime import timedelta
import logging

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    Minio = None
    S3Error = Exception

from app.config import settings

logger = logging.getLogger(__name__)


class MinIOStorage:
    """
    Dịch vụ lưu trữ MinIO để xử lý upload và download file.
    
    Sử dụng API tương thích S3 để lưu trữ:
    - Tài liệu người dùng upload để kiểm tra đạo văn
    - Tài liệu trong corpus để so sánh
    
    Các thực hành tốt đã áp dụng:
    - Sử dụng pre-signed URL để download an toàn
    - Tách biệt bucket (uploads và corpus)
    - Tự động tạo bucket nếu chưa tồn tại
    """
    
    def __init__(self):
        if not MINIO_AVAILABLE:
            logger.warning("MinIO không khả dụng - chức năng lưu trữ file bị tắt")
            self.client = None
            return
            
        try:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self._ensure_buckets_exist()
            logger.info(f"Đã kết nối MinIO tới {settings.MINIO_ENDPOINT}")
        except Exception as e:
            logger.error(f"Kết nối MinIO thất bại: {e}")
            self.client = None
    
    def _ensure_buckets_exist(self):
        """Tạo các bucket nếu chưa tồn tại"""
        if not self.client:
            return
            
        buckets = [settings.MINIO_BUCKET_UPLOADS, settings.MINIO_BUCKET_CORPUS]
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Đã tạo bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Lỗi khi tạo bucket {bucket}: {e}")
    
    def upload_file(
        self, 
        file_path: str, 
        bucket: Optional[str] = None,
        object_name: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        Upload file từ đường dẫn local lên MinIO
        
        Args:
            file_path: Đường dẫn file trên máy local
            bucket: Bucket đích (mặc định là bucket uploads)
            object_name: Tên object trong MinIO (mặc định: UUID + tên file gốc)
            content_type: MIME type của file
            
        Returns:
            Tên object nếu thành công, None nếu thất bại
        """
        if not self.client:
            logger.warning("Client MinIO không khả dụng")
            return None
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        if not object_name:
            filename = os.path.basename(file_path)
            object_name = f"{uuid.uuid4()}/{filename}"
        
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as file_data:
                self.client.put_object(
                    bucket,
                    object_name,
                    file_data,
                    file_size,
                    content_type=content_type
                )
            logger.info(f"Đã upload {file_path} lên {bucket}/{object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Lỗi khi upload file: {e}")
            return None
    
    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        bucket: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        Upload dữ liệu dạng bytes lên MinIO
        
        Args:
            data: Dữ liệu bytes cần upload
            object_name: Tên object trong MinIO
            bucket: Bucket đích
            content_type: MIME type
            
        Returns:
            Tên object nếu thành công, None nếu thất bại
        """
        if not self.client:
            return None
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        try:
            from io import BytesIO
            data_stream = BytesIO(data)
            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                len(data),
                content_type=content_type
            )
            return object_name
        except S3Error as e:
            logger.error(f"Lỗi khi upload bytes: {e}")
            return None
    
    def download_file(
        self, 
        object_name: str, 
        bucket: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Download nội dung file từ MinIO
        
        Args:
            object_name: Tên object trong MinIO
            bucket: Bucket nguồn
            
        Returns:
            Nội dung file dạng bytes, None nếu lỗi
        """
        if not self.client:
            return None
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Lỗi khi download file: {e}")
            return None
    
    def get_presigned_url(
        self, 
        object_name: str, 
        bucket: Optional[str] = None,
        expires: int = 3600
    ) -> Optional[str]:
        """
        Tạo URL tạm thời (pre-signed) để download an toàn
        
        Args:
            object_name: Tên object trong MinIO
            bucket: Bucket nguồn
            expires: Thời gian hết hạn của URL (giây) - mặc định 1 giờ
            
        Returns:
            Chuỗi URL pre-signed, None nếu lỗi
        """
        if not self.client:
            return None
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        try:
            url = self.client.presigned_get_object(
                bucket,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Lỗi khi tạo pre-signed URL: {e}")
            return None
    
    def delete_file(
        self, 
        object_name: str, 
        bucket: Optional[str] = None
    ) -> bool:
        """
        Xóa file khỏi MinIO
        
        Args:
            object_name: Tên object cần xóa
            bucket: Bucket nguồn
            
        Returns:
            True nếu xóa thành công, False nếu thất bại
        """
        if not self.client:
            return False
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Đã xóa {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Lỗi khi xóa file: {e}")
            return False
    
    def list_objects(
        self, 
        bucket: Optional[str] = None,
        prefix: str = ""
    ) -> list:
        """
        Liệt kê các object trong bucket
        
        Args:
            bucket: Bucket cần liệt kê
            prefix: Bộ lọc tiền tố (nếu có)
            
        Returns:
            Danh sách tên các object
        """
        if not self.client:
            return []
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Lỗi khi liệt kê object: {e}")
            return []
    
    def is_available(self) -> bool:
        """Kiểm tra xem MinIO có khả dụng và đã kết nối hay không"""
        return self.client is not None
    
    def upload_corpus_document(
        self,
        doc_id: str,
        title: str,
        text: str,
        author: str = "",
        university: str = "",
        year: int = 2024
    ) -> Optional[str]:
        """
        Upload tài liệu corpus lên MinIO để xem sau này
        
        Args:
            doc_id: ID của tài liệu (UUID)
            title: Tiêu đề tài liệu
            text: Nội dung tài liệu
            author: Tên tác giả
            university: Tên trường đại học
            year: Năm xuất bản
            
        Returns:
            Đường dẫn object nếu thành công, None nếu thất bại
        """
        if not self.client:
            return None
        
        # Tạo tên file an toàn từ tiêu đề (giới hạn 50 ký tự)
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title[:50])
        filename = f"{safe_title}_{doc_id[:8]}.txt"
        object_name = f"corpus/{year}/{filename}"
        
        # Tạo nội dung với phần header metadata
        content = f"""# {title}
# Tác giả: {author}
# Trường: {university}
# Năm: {year}
# ID tài liệu: {doc_id}
# ================================================

{text}
"""
        
        try:
            return self.upload_bytes(
                data=content.encode('utf-8'),
                object_name=object_name,
                bucket=settings.MINIO_BUCKET_CORPUS,
                content_type="text/plain; charset=utf-8"
            )
        except Exception as e:
            logger.error(f"Lỗi khi upload tài liệu corpus {doc_id}: {e}")
            return None


# Instance toàn cục
_minio_storage: Optional[MinIOStorage] = None


def get_minio_storage() -> MinIOStorage:
    """Lấy hoặc tạo instance MinIO storage"""
    global _minio_storage
    if _minio_storage is None:
        _minio_storage = MinIOStorage()
    return _minio_storage