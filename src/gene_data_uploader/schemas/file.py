from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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


class FileListResponse(BaseModel):
    items: list[FileMetadata]
    total: int
    offset: int
    limit: int | None


class FileDataResponse(BaseModel):
    file_id: str
    original_filename: str
    delimiter: str
    columns: list[str]
    row_count: int
    returned_rows: int
    offset: int = 0
    limit: int = 100
    rows: list[dict[str, str]] = Field(default_factory=list)
