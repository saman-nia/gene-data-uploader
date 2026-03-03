from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Gene Data Uploader API"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/gene_data_uploader"
    storage_root: Path = Path("storage/files")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
