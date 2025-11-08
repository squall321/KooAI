"""
Storage configuration
"""

from enum import Enum
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class StorageType(str, Enum):
    """Storage backend 타입"""

    LOCAL = "local"
    S3 = "s3"
    MINIO = "minio"
    GCS = "gcs"  # Google Cloud Storage
    AZURE = "azure"  # Azure Blob Storage


class StorageConfig(BaseSettings):
    """
    Storage 설정

    Environment variables나 .env 파일에서 설정을 읽어옵니다.
    """

    # Storage type
    storage_type: StorageType = Field(default=StorageType.LOCAL, description="Storage backend type")

    # Local filesystem
    local_base_path: str = Field(default="./data/storage", description="Local storage path")

    # S3 / MinIO
    s3_endpoint_url: Optional[str] = Field(
        default=None, description="S3 endpoint URL (for MinIO or custom S3)"
    )
    s3_region: str = Field(default="us-east-1", description="AWS region")
    s3_bucket_name: str = Field(default="kooai-storage", description="S3 bucket name")
    s3_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    s3_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    s3_use_ssl: bool = Field(default=True, description="Use SSL for S3")

    # Google Cloud Storage
    gcs_bucket_name: str = Field(default="kooai-storage", description="GCS bucket name")
    gcs_project_id: Optional[str] = Field(default=None, description="GCP project ID")
    gcs_credentials_path: Optional[str] = Field(
        default=None, description="Path to GCS credentials JSON"
    )

    # Azure Blob Storage
    azure_account_name: Optional[str] = Field(
        default=None, description="Azure storage account name"
    )
    azure_account_key: Optional[str] = Field(default=None, description="Azure storage account key")
    azure_container_name: str = Field(default="kooai-storage", description="Azure container name")
    azure_connection_string: Optional[str] = Field(
        default=None, description="Azure connection string"
    )

    # Common settings
    max_file_size: int = Field(
        default=1024 * 1024 * 1024,  # 1GB
        description="Maximum file size in bytes",
    )
    multipart_threshold: int = Field(
        default=50 * 1024 * 1024,  # 50MB
        description="File size threshold for multipart upload",
    )
    multipart_part_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Part size for multipart upload",
    )
    presigned_url_expiration: int = Field(
        default=3600, description="Presigned URL expiration in seconds"
    )

    model_config = ConfigDict(
        env_prefix="STORAGE_",
        case_sensitive=False,
    )


# Singleton instance
_storage_config: Optional[StorageConfig] = None


def get_storage_config() -> StorageConfig:
    """Get storage configuration singleton"""
    global _storage_config
    if _storage_config is None:
        _storage_config = StorageConfig()
    return _storage_config
