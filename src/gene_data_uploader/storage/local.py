import hashlib
from pathlib import Path

from fastapi import UploadFile

from gene_data_uploader.storage.base import AbstractStorage, StorageLimitExceeded, StoredFile


class LocalFileStorage(AbstractStorage):
    def __init__(self, root_directory: Path):
        self.root_directory = root_directory
        self.root_directory.mkdir(parents=True, exist_ok=True)

    async def save_upload(
        self,
        file_id: str,
        upload_file: UploadFile,
        max_size_bytes: int | None = None,
    ) -> StoredFile:
        extension = Path(upload_file.filename or "").suffix.lower() or ".csv"
        target_name = f"{file_id}{extension}"
        target_path = self.root_directory / target_name

        digest = hashlib.sha256()
        total_size = 0

        try:
            with target_path.open("wb") as handle:
                while True:
                    chunk = await upload_file.read(1024 * 1024)
                    if not chunk:
                        break

                    next_size = total_size + len(chunk)
                    if max_size_bytes is not None and next_size > max_size_bytes:
                        raise StorageLimitExceeded(f"Upload exceeds maximum size of {max_size_bytes} bytes")

                    handle.write(chunk)
                    digest.update(chunk)
                    total_size = next_size
        except Exception:
            if target_path.exists():
                target_path.unlink()
            raise
        finally:
            await upload_file.seek(0)

        return StoredFile(
            storage_path=target_name,
            file_size_bytes=total_size,
            sha256=digest.hexdigest(),
        )

    def resolve_path(self, storage_path: str) -> Path:
        path = (self.root_directory / storage_path).resolve()
        root = self.root_directory.resolve()
        if root not in path.parents and path != root:
            raise ValueError("Invalid storage path")
        return path

    def delete(self, storage_path: str) -> None:
        path = self.resolve_path(storage_path)
        if path.exists():
            path.unlink()
