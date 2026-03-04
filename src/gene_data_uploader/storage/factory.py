from gene_data_uploader.core.config import Settings
from gene_data_uploader.storage.base import AbstractStorage
from gene_data_uploader.storage.local import LocalFileStorage


def build_storage(settings: Settings) -> AbstractStorage:
    return LocalFileStorage(root_directory=settings.storage_root)
