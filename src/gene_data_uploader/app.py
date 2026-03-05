from contextlib import asynccontextmanager

from fastapi import FastAPI

from gene_data_uploader.core.config import Settings, get_settings
from gene_data_uploader.db.base import Base
from gene_data_uploader.db.session import build_engine, build_session_factory
from gene_data_uploader.storage.factory import build_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=app.state.engine)
    yield
    app.state.engine.dispose()
