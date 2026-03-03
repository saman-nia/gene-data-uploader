from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile


@dataclass(frozen=True)
class StoredFile:
    storage_path: str
    file_size_bytes: int
    sha256: str


class StorageLimitExceeded(Exception):
    """Raised when upload exceeds configured maximum size."""


class AbstractStorage(ABC):
    @abstractmethod
    async def save_upload(
        self,
        file_id: str,
        upload_file: UploadFile,
        max_size_bytes: int | None = None,
    ) -> StoredFile:
        """Persist an uploaded file and return storage metadata."""
