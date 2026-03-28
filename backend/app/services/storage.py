from app.services.minio_storage import get_minio_storage
import logging

logger = logging.getLogger(__name__)


class S3Storage:
    """
    Legacy wrapper for MinIO storage.
    Points to the modern MinIOStorage implementation to avoid code duplication.
    """
    def __init__(self):
        self.storage = get_minio_storage()

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """Upload raw bytes to MinIO. Returns object path (bucket/object_name)."""
        result = self.storage.upload_bytes(data, object_name, content_type=content_type)
        if result:
            from app.config import settings
            return f"{settings.MINIO_BUCKET_UPLOADS}/{object_name}"
        raise Exception("Upload failed via MinIOStorage wrapper")

    def download_to_path(self, object_name: str, local_path: str) -> None:
        """Download object from MinIO to local path"""
        data = self.storage.download_file(object_name)
        if data is None:
            raise Exception(f"Failed to download {object_name} from MinIO")
        
        with open(local_path, 'wb') as f:
            f.write(data)
