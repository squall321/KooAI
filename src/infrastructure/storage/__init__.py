"""
Storage infrastructure package

Provides abstraction for file storage with support for multiple backends:
- Local file system
- S3 (AWS)
- MinIO
- Google Cloud Storage
- Azure Blob Storage
"""

from .base import StorageBackend, FileMetadata, UploadResult, PresignedUrl
from .config import StorageConfig, StorageType, get_storage_config
from .factory import create_storage, get_storage, reset_storage
from .local import LocalStorageBackend

__all__ = [
    # Base
    "StorageBackend",
    "FileMetadata",
    "UploadResult",
    "PresignedUrl",
    # Config
    "StorageConfig",
    "StorageType",
    "get_storage_config",
    # Factory
    "create_storage",
    "get_storage",
    "reset_storage",
    # Adapters
    "LocalStorageBackend",
]
