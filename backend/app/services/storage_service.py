import io
import uuid

from minio import Minio

from app.core.config import settings


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def upload_file(bucket: str, file_bytes: bytes, filename: str, content_type: str) -> str:
    """Загружает файл в MinIO. Возвращает object_name (ключ внутри бакета)."""
    client = get_minio_client()
    object_name = f"{uuid.uuid4()}/{filename}"
    client.put_object(
        bucket,
        object_name,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )
    return object_name


