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

    @abstractmethod
    def resolve_path(self, storage_path: str) -> Path:
        """Resolve a stored file path into a local file path."""

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        """Delete a stored file if it exists."""
