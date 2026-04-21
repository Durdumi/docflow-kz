import io
import uuid
from minio import Minio
from minio.error import S3Error
from app.core.config import settings


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def upload_file(bucket: str, file_bytes: bytes, filename: str, content_type: str) -> str:
    client = get_minio_client()
    file_id = str(uuid.uuid4())
    object_name = f"{file_id}/{filename}"
    client.put_object(
        bucket,
        object_name,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )
    return f"/storage/{bucket}/{object_name}"


def get_presigned_url(bucket: str, object_name: str, expires_hours: int = 24) -> str:
    from datetime import timedelta
    client = get_minio_client()
    object_path = object_name.replace(f"/storage/{bucket}/", "")
    return client.presigned_get_object(bucket, object_path, expires=timedelta(hours=expires_hours))
