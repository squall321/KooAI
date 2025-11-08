"""
Storage factory

Creates storage backend instances based on configuration.
"""

from typing import Optional

from .base import StorageBackend
from .config import StorageConfig, StorageType, get_storage_config
from .local import LocalStorageBackend


def create_storage(config: Optional[StorageConfig] = None) -> StorageBackend:
    """
    Create storage backend based on configuration

    Args:
        config: Storage configuration (uses default if None)

    Returns:
        StorageBackend instance

    Raises:
        ValueError: If storage type is not supported or dependencies are missing
    """
    if config is None:
        config = get_storage_config()

    if config.storage_type == StorageType.LOCAL:
        return LocalStorageBackend(base_path=config.local_base_path)

    elif config.storage_type == StorageType.S3:
        try:
            from .s3 import S3StorageBackend
        except ImportError as e:
            raise ImportError(
                "S3 storage requires aioboto3. " "Install it with: pip install 'kooai[storage]'"
            ) from e

        return S3StorageBackend(
            bucket_name=config.s3_bucket_name,
            region=config.s3_region,
            endpoint_url=config.s3_endpoint_url,
            access_key_id=config.s3_access_key_id,
            secret_access_key=config.s3_secret_access_key,
            use_ssl=config.s3_use_ssl,
        )

    elif config.storage_type == StorageType.MINIO:
        try:
            from .s3 import MinIOStorageBackend
        except ImportError as e:
            raise ImportError(
                "MinIO storage requires aioboto3. " "Install it with: pip install 'kooai[storage]'"
            ) from e

        # MinIO는 S3 호환이지만 endpoint_url이 필수
        if not config.s3_endpoint_url:
            raise ValueError("MinIO requires s3_endpoint_url to be configured")

        return MinIOStorageBackend(
            bucket_name=config.s3_bucket_name,
            region=config.s3_region,
            endpoint_url=config.s3_endpoint_url,
            access_key_id=config.s3_access_key_id,
            secret_access_key=config.s3_secret_access_key,
            use_ssl=config.s3_use_ssl,
        )

    elif config.storage_type == StorageType.GCS:
        raise NotImplementedError(
            "Google Cloud Storage support is not yet implemented. " "Contributions welcome!"
        )

    elif config.storage_type == StorageType.AZURE:
        raise NotImplementedError(
            "Azure Blob Storage support is not yet implemented. " "Contributions welcome!"
        )

    else:
        raise ValueError(f"Unsupported storage type: {config.storage_type}")


# Singleton instance
_storage_instance: Optional[StorageBackend] = None


def get_storage() -> StorageBackend:
    """Get storage backend singleton"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = create_storage()
    return _storage_instance


def reset_storage() -> None:
    """Reset storage singleton (useful for testing)"""
    global _storage_instance
    _storage_instance = None
