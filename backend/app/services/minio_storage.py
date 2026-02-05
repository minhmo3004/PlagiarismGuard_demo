"""
MinIO Storage Service
Handles file upload/download to MinIO S3-compatible object storage
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
    MinIO Storage Service for handling file uploads and downloads.
    
    Uses S3-compatible API to store:
    - Uploaded documents for plagiarism checking
    - Corpus documents for comparison
    
    Best Practices Applied:
    - Pre-signed URLs for secure downloads
    - Bucket separation (uploads vs corpus)
    - Automatic bucket creation if not exists
    """
    
    def __init__(self):
        if not MINIO_AVAILABLE:
            logger.warning("MinIO not available - file storage disabled")
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
            logger.info(f"MinIO connected to {settings.MINIO_ENDPOINT}")
        except Exception as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            self.client = None
    
    def _ensure_buckets_exist(self):
        """Create buckets if they don't exist"""
        if not self.client:
            return
            
        buckets = [settings.MINIO_BUCKET_UPLOADS, settings.MINIO_BUCKET_CORPUS]
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Error creating bucket {bucket}: {e}")
    
    def upload_file(
        self, 
        file_path: str, 
        bucket: Optional[str] = None,
        object_name: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        Upload a file to MinIO
        
        Args:
            file_path: Local path to the file
            bucket: Target bucket (defaults to uploads bucket)
            object_name: Object name in MinIO (defaults to UUID + filename)
            content_type: MIME type of the file
            
        Returns:
            Object name if successful, None otherwise
        """
        if not self.client:
            logger.warning("MinIO client not available")
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
            logger.info(f"Uploaded {file_path} to {bucket}/{object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        bucket: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> Optional[str]:
        """
        Upload bytes data to MinIO
        
        Args:
            data: Bytes to upload
            object_name: Object name in MinIO
            bucket: Target bucket
            content_type: MIME type
            
        Returns:
            Object name if successful, None otherwise
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
            logger.error(f"Error uploading bytes: {e}")
            return None
    
    def download_file(
        self, 
        object_name: str, 
        bucket: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Download a file from MinIO
        
        Args:
            object_name: Object name in MinIO
            bucket: Source bucket
            
        Returns:
            File contents as bytes, None if error
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
            logger.error(f"Error downloading file: {e}")
            return None
    
    def get_presigned_url(
        self, 
        object_name: str, 
        bucket: Optional[str] = None,
        expires: int = 3600
    ) -> Optional[str]:
        """
        Generate a pre-signed URL for secure download
        
        Args:
            object_name: Object name in MinIO
            bucket: Source bucket
            expires: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Pre-signed URL string, None if error
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
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def delete_file(
        self, 
        object_name: str, 
        bucket: Optional[str] = None
    ) -> bool:
        """
        Delete a file from MinIO
        
        Args:
            object_name: Object name to delete
            bucket: Source bucket
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def list_objects(
        self, 
        bucket: Optional[str] = None,
        prefix: str = ""
    ) -> list:
        """
        List objects in a bucket
        
        Args:
            bucket: Bucket to list
            prefix: Optional prefix filter
            
        Returns:
            List of object names
        """
        if not self.client:
            return []
            
        bucket = bucket or settings.MINIO_BUCKET_UPLOADS
        
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing objects: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if MinIO is available and connected"""
        return self.client is not None


# Global instance
_minio_storage: Optional[MinIOStorage] = None


def get_minio_storage() -> MinIOStorage:
    """Get or create MinIO storage instance"""
    global _minio_storage
    if _minio_storage is None:
        _minio_storage = MinIOStorage()
    return _minio_storage
