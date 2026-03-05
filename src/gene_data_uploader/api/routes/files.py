from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from gene_data_uploader.core.config import Settings
from gene_data_uploader.db.models import UploadedFile
from gene_data_uploader.schemas.file import FileMetadata
from gene_data_uploader.services.csv_utils import analyze_csv
from gene_data_uploader.storage.base import AbstractStorage, StorageLimitExceeded

router = APIRouter(tags=["files"])


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db_session(request: Request):
    session_factory = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_storage(request: Request) -> AbstractStorage:
    return request.app.state.storage


def to_file_metadata(model: UploadedFile) -> FileMetadata:
    return FileMetadata.model_validate(model)


def safe_delete(storage: AbstractStorage, storage_path: str) -> None:
    try:
        storage.delete(storage_path)
    except Exception:
        pass


@router.post("/files/upload", response_model=FileMetadata, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    storage: AbstractStorage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> FileMetadata:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    file_id = str(uuid4())

    try:
        stored_file = await storage.save_upload(
            file_id=file_id,
            upload_file=file,
            max_size_bytes=settings.max_upload_size_bytes,
        )
    except StorageLimitExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Max size is {settings.max_upload_size_mb} MB",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to persist uploaded file") from exc

    # Defensive check for storage backends that do not enforce max_size_bytes.
    if stored_file.file_size_bytes > settings.max_upload_size_bytes:
        safe_delete(storage, stored_file.storage_path)
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File too large. Max size is {settings.max_upload_size_mb} MB",
        )

    try:
        summary = await run_in_threadpool(analyze_csv, storage.resolve_path(stored_file.storage_path))
    except Exception as exc:
        safe_delete(storage, stored_file.storage_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid CSV file: {exc}") from exc

    file_metadata = UploadedFile(
        id=file_id,
        original_filename=file.filename,
        storage_path=stored_file.storage_path,
        content_type=file.content_type,
        delimiter=summary.delimiter,
        file_size_bytes=stored_file.file_size_bytes,
        row_count=summary.row_count,
        column_count=summary.column_count,
        columns=summary.columns,
        sha256=stored_file.sha256,
    )

    try:
        db.add(file_metadata)
        db.commit()
        db.refresh(file_metadata)
    except SQLAlchemyError as exc:
        db.rollback()
        safe_delete(storage, stored_file.storage_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to persist file metadata") from exc

    return to_file_metadata(file_metadata)
