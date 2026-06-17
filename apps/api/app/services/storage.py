"""Pluggable document storage — local disk or S3 (SSE-S3 at rest)."""
from __future__ import annotations

import logging
import os
from typing import Protocol

from app.config import settings
from app.ids import new_id

logger = logging.getLogger("setu.storage")

_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


class StorageBackend(Protocol):
    def put(self, data: bytes, *, mime: str, doc_id: str | None = None) -> tuple[str, str | None]: ...
    def delete(self, path: str) -> bool: ...
    def read(self, path: str) -> bytes | None: ...


class LocalStorageBackend:
    def put(self, data: bytes, *, mime: str, doc_id: str | None = None) -> tuple[str, str | None]:
        doc_id = doc_id or new_id("doc")
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
        path = os.path.join(settings.STORAGE_PATH, f"{doc_id}{_EXT.get(mime, '')}")
        with open(path, "wb") as f:
            f.write(data)
        return path, None

    def delete(self, path: str) -> bool:
        try:
            if os.path.isfile(path):
                os.remove(path)
                return True
        except OSError as exc:
            logger.warning("local delete failed %s: %s", path, exc)
        return False

    def read(self, path: str) -> bytes | None:
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError:
            return None


class S3StorageBackend:
    def __init__(self) -> None:
        import boto3

        kwargs: dict = {"region_name": settings.S3_REGION}
        if settings.AWS_ACCESS_KEY_ID:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
        self._client = boto3.client("s3", **kwargs)
        self._bucket = settings.S3_BUCKET

    def put(self, data: bytes, *, mime: str, doc_id: str | None = None) -> tuple[str, str | None]:
        doc_id = doc_id or new_id("doc")
        key = f"uploads/{doc_id}{_EXT.get(mime, '')}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=mime,
            ServerSideEncryption="AES256",
        )
        return key, "aws:s3:sse"

    def delete(self, path: str) -> bool:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=path)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("s3 delete failed %s: %s", path, exc)
            return False

    def read(self, path: str) -> bytes | None:
        try:
            resp = self._client.get_object(Bucket=self._bucket, Key=path)
            return resp["Body"].read()
        except Exception:
            return None


def get_storage() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3" and settings.S3_BUCKET:
        return S3StorageBackend()
    return LocalStorageBackend()
