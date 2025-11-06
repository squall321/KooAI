"""
Cache configuration
"""

from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class CacheConfig(BaseSettings):
    """
    Cache 설정

    Environment variables나 .env 파일에서 설정을 읽어옵니다.
    """

    # Redis connection
    redis_url: str = Field(
        default="redis://localhost:6379/1",
        description="Redis connection URL",
    )
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=1, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_ssl: bool = Field(default=False, description="Use SSL for Redis")

    # Connection pool
    redis_max_connections: int = Field(
        default=50, description="Maximum Redis connections"
    )
    redis_socket_timeout: int = Field(
        default=5, description="Socket timeout (seconds)"
    )
    redis_socket_connect_timeout: int = Field(
        default=5, description="Socket connect timeout (seconds)"
    )

    # Cache TTL (Time To Live) settings
    default_ttl: int = Field(
        default=3600, description="Default cache TTL (seconds, 1 hour)"
    )
    analysis_ttl: int = Field(
        default=86400, description="Analysis result TTL (seconds, 24 hours)"
    )
    query_ttl: int = Field(
        default=600, description="Query result TTL (seconds, 10 minutes)"
    )
    session_ttl: int = Field(
        default=7200, description="Session TTL (seconds, 2 hours)"
    )
    short_ttl: int = Field(
        default=60, description="Short-lived cache TTL (seconds, 1 minute)"
    )

    # Cache key prefixes
    key_prefix: str = Field(default="kooai:", description="Global key prefix")
    analysis_prefix: str = Field(
        default="analysis:", description="Analysis cache prefix"
    )
    query_prefix: str = Field(default="query:", description="Query cache prefix")
    session_prefix: str = Field(default="session:", description="Session cache prefix")

    # Cache behavior
    cache_enabled: bool = Field(default=True, description="Enable caching globally")
    cache_compression: bool = Field(
        default=True, description="Enable cache value compression"
    )
    cache_serialization: str = Field(
        default="json", description="Serialization format (json, pickle, msgpack)"
    )

    # Performance
    batch_size: int = Field(
        default=100, description="Batch size for multi-get/set operations"
    )
    pipeline_enabled: bool = Field(
        default=True, description="Enable Redis pipelining"
    )

    model_config = ConfigDict(
        env_prefix="CACHE_",
        case_sensitive=False,
    )


# Singleton instance
_cache_config: Optional[CacheConfig] = None


def get_cache_config() -> CacheConfig:
    """Get cache configuration singleton"""
    global _cache_config
    if _cache_config is None:
        _cache_config = CacheConfig()
    return _cache_config
