"""
중앙 설정 관리 (Central Settings)

모든 환경 변수를 한 곳에서 관리하는 중앙 설정 클래스입니다.
Pydantic Settings를 사용하여 타입 안전성과 검증을 제공합니다.
"""

import os
import secrets
from typing import List, Optional
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    KooAI 애플리케이션 설정

    환경 변수에서 자동으로 설정을 로드합니다.
    .env 파일도 자동으로 읽습니다.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================
    # 애플리케이션 기본 설정
    # ============================================

    app_name: str = Field(default="KooAI", description="Application name")
    kooai_env: str = Field(
        default="development", description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # ============================================
    # API 설정
    # ============================================

    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of workers")

    # ============================================
    # 보안 설정
    # ============================================

    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT and encryption",
    )

    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="CORS allowed origins (comma-separated)",
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """CORS allowed origins as list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # ============================================
    # 데이터베이스 설정
    # ============================================

    database_url: Optional[str] = Field(
        default=None, description="Full database URL (overrides individual DB settings)"
    )

    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="kooai", description="Database name")
    db_user: str = Field(default="kooai", description="Database user")
    db_password: str = Field(default="kooai", description="Database password")

    db_pool_size: int = Field(default=20, description="Connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")
    db_pool_pre_ping: bool = Field(default=True, description="Pre-ping connections")
    db_pool_recycle: int = Field(default=3600, description="Pool recycle time (seconds)")

    db_echo: bool = Field(default=False, description="Echo SQL queries")
    db_echo_pool: bool = Field(default=False, description="Echo pool operations")

    use_test_db: bool = Field(default=False, description="Use SQLite in-memory for testing")

    @property
    def get_database_url(self) -> str:
        """Get database URL (computed or from env)"""
        if self.database_url:
            return self.database_url

        if self.use_test_db:
            return "sqlite:///:memory:"

        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def get_sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic"""
        if self.use_test_db:
            return "sqlite:///:memory:"

        if self.database_url:
            # Convert asyncpg to psycopg2
            return self.database_url.replace("postgresql+asyncpg://", "postgresql://")

        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ============================================
    # Redis/Cache 설정
    # ============================================

    redis_url: Optional[str] = Field(
        default=None, description="Full Redis URL (overrides individual Redis settings)"
    )

    cache_redis_host: str = Field(default="localhost", description="Redis host")
    cache_redis_port: int = Field(default=6379, description="Redis port")
    cache_redis_db: int = Field(default=1, description="Redis database number")
    cache_redis_password: Optional[str] = Field(default=None, description="Redis password")

    cache_default_ttl: int = Field(default=3600, description="Default cache TTL (seconds)")
    cache_analysis_ttl: int = Field(default=86400, description="Analysis cache TTL (seconds)")

    @property
    def get_redis_url(self) -> str:
        """Get Redis URL (computed or from env)"""
        if self.redis_url:
            return self.redis_url

        if self.cache_redis_password:
            return (
                f"redis://:{self.cache_redis_password}@{self.cache_redis_host}:"
                f"{self.cache_redis_port}/{self.cache_redis_db}"
            )

        return f"redis://{self.cache_redis_host}:{self.cache_redis_port}/{self.cache_redis_db}"

    # ============================================
    # 파일 저장 경로
    # ============================================

    data_dir: str = Field(default="./data", description="Data directory")
    upload_dir: str = Field(default="./data/uploads", description="Upload directory")
    model_dir: str = Field(default="./models", description="Model directory")

    # ============================================
    # AI/ML API Keys
    # ============================================

    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    huggingface_token: Optional[str] = Field(default=None, description="Hugging Face token")

    # ============================================
    # Celery/Task Queue 설정
    # ============================================

    celery_broker_url: Optional[str] = Field(
        default=None, description="Celery broker URL (defaults to Redis URL)"
    )

    celery_result_backend: Optional[str] = Field(
        default=None, description="Celery result backend (defaults to Redis URL)"
    )

    @property
    def get_celery_broker_url(self) -> str:
        """Get Celery broker URL"""
        return self.celery_broker_url or self.get_redis_url

    @property
    def get_celery_result_backend(self) -> str:
        """Get Celery result backend URL"""
        return self.celery_result_backend or self.get_redis_url

    # ============================================
    # AWS/S3 설정 (선택사항)
    # ============================================

    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret key")
    aws_region: str = Field(default="us-east-1", description="AWS region")
    s3_bucket_name: Optional[str] = Field(default=None, description="S3 bucket name")

    # ============================================
    # Validators
    # ============================================

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper

    @field_validator("kooai_env")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment"""
        allowed = ["development", "staging", "production", "test"]
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"kooai_env must be one of {allowed}")
        return v_lower

    # ============================================
    # Helper Properties
    # ============================================

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.kooai_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.kooai_env == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in test mode"""
        return (
            self.kooai_env == "test"
            or self.use_test_db
            or os.getenv("TESTING", "false").lower() == "true"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    설정 가져오기 (싱글톤)

    Returns:
        Settings: 애플리케이션 설정 인스턴스

    Example:
        from src.infrastructure.config.settings import get_settings

        settings = get_settings()
        print(settings.database_url)
    """
    return Settings()


# 편의 함수들
def get_database_url() -> str:
    """데이터베이스 URL 가져오기"""
    return get_settings().get_database_url


def get_redis_url() -> str:
    """Redis URL 가져오기"""
    return get_settings().get_redis_url


def is_production() -> bool:
    """프로덕션 모드 확인"""
    return get_settings().is_production


def is_development() -> bool:
    """개발 모드 확인"""
    return get_settings().is_development
