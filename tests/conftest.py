from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gene_data_uploader.app import create_app
from gene_data_uploader.core.config import Settings


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    db_path = tmp_path / "test.db"
    storage_path = tmp_path / "storage"

    return Settings(
        database_url=f"sqlite:///{db_path}",
        storage_root=storage_path,
        max_upload_size_mb=20,
    )


@pytest.fixture()
def client(test_settings: Settings):
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
