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
