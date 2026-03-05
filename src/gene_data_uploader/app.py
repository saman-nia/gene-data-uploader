from contextlib import asynccontextmanager

from fastapi import FastAPI

from gene_data_uploader.api.routes.files import router as files_router
from gene_data_uploader.core.config import Settings, get_settings
from gene_data_uploader.db.base import Base
from gene_data_uploader.db.session import build_engine, build_session_factory
from gene_data_uploader.storage.factory import build_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=app.state.engine)
    yield
    app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()

    app = FastAPI(
        title=active_settings.app_name,
        version="1.0.0",
        description="Upload CSV files, store metadata in PostgreSQL, and retrieve file data.",
        lifespan=lifespan,
    )

    app.state.settings = active_settings
    app.state.engine = build_engine(active_settings.database_url)
    app.state.session_factory = build_session_factory(app.state.engine)
    app.state.storage = build_storage(active_settings)

    app.include_router(files_router)

    return app
