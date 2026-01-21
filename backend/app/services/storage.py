from minio import Minio
from minio.error import S3Error
from app.config import settings
import io
import logging

logger = logging.getLogger(__name__)


class S3Storage:
    def __init__(self):
        endpoint_raw = settings.S3_ENDPOINT or ""
        secure = False
        if endpoint_raw.startswith("https://"):
            secure = True
        endpoint = endpoint_raw.replace("https://", "").replace("http://", "").rstrip('/')

        self.client = Minio(
            endpoint,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=secure,
        )

        # Ensure bucket exists
        try:
            if not self.client.bucket_exists(settings.S3_BUCKET):
                self.client.make_bucket(settings.S3_BUCKET)
        except Exception as e:
            logger.warning(f"MinIO bucket check/create failed: {e}")

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """Upload raw bytes to MinIO. Returns object path (bucket/object_name)."""
        try:
            data_io = io.BytesIO(data)
            data_io.seek(0)
            self.client.put_object(
                settings.S3_BUCKET,
                object_name,
                data_io,
                length=len(data),
                content_type=content_type,
            )
            return f"{settings.S3_BUCKET}/{object_name}"
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise

    def download_to_path(self, object_name: str, local_path: str) -> None:
        """Download object from MinIO to local path"""
        try:
            self.client.fget_object(settings.S3_BUCKET, object_name, local_path)
        except Exception as e:
            logger.error(f"MinIO download error: {e}")
            raise
