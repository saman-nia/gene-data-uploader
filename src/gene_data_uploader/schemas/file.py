from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileMetadata(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    storage_path: str
    content_type: str | None = None
    delimiter: str
    file_size_bytes: int
    row_count: int
    column_count: int
    columns: list[str]
    sha256: str
    upload_timestamp: datetime
