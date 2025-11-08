"""
데이터베이스 설정 관리

환경 변수를 통해 데이터베이스 연결 설정을 관리합니다.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse


@dataclass
class DatabaseConfig:
    """
    데이터베이스 설정

    환경 변수로부터 설정값을 읽습니다.
    """

    # PostgreSQL 설정
    host: str = "localhost"
    port: int = 5432
    database: str = "kooai"
    user: str = "kooai"
    password: str = "kooai"

    # 연결 풀 설정
    pool_size: int = 20
    max_overflow: int = 10
    pool_pre_ping: bool = True
    pool_recycle: int = 3600  # 1 hour

    # 일반 설정
    echo: bool = False
    echo_pool: bool = False

    # 테스트 모드
    use_test_db: bool = False

    @property
    def database_url(self) -> str:
        """
        데이터베이스 연결 URL 생성

        Returns:
            str: SQLAlchemy 연결 URL
        """
        if self.use_test_db:
            return "sqlite+aiosqlite:///:memory:"

        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def sync_database_url(self) -> str:
        """
        동기 데이터베이스 연결 URL (Alembic용)

        Returns:
            str: psycopg2 연결 URL
        """
        if self.use_test_db:
            return "sqlite:///:memory:"

        return (
            f"postgresql://{self.user}:{self.password}" f"@{self.host}:{self.port}/{self.database}"
        )

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        환경 변수로부터 설정 로드

        우선순위:
        1. DATABASE_URL (전체 URL, Docker/Apptainer용)
        2. DB_HOST, DB_PORT 등 (개별 변수, 로컬 개발용)

        Returns:
            DatabaseConfig: 설정 인스턴스
        """
        # 1. DATABASE_URL 우선 확인
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return cls._from_url(database_url)

        # 2. 개별 환경 변수 사용 (하위 호환)
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "kooai"),
            user=os.getenv("DB_USER", "kooai"),
            password=os.getenv("DB_PASSWORD", "kooai"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            echo_pool=os.getenv("DB_ECHO_POOL", "false").lower() == "true",
            use_test_db=os.getenv("USE_TEST_DB", "false").lower() == "true",
        )

    @classmethod
    def _from_url(cls, url: str) -> "DatabaseConfig":
        """
        DATABASE_URL 파싱하여 설정 생성

        Args:
            url: 데이터베이스 연결 URL
                 예: postgresql://user:pass@host:5432/dbname

        Returns:
            DatabaseConfig: 설정 인스턴스

        Raises:
            ValueError: 지원하지 않는 데이터베이스 스킴
        """
        parsed = urlparse(url)

        # PostgreSQL URL 파싱
        if parsed.scheme in ["postgresql", "postgres"]:
            return cls(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/") if parsed.path else "kooai",
                user=parsed.username or "kooai",
                password=parsed.password or "kooai",
                # 풀 설정은 환경 변수에서 가져오기 (선택사항)
                pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
                pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
                echo_pool=os.getenv("DB_ECHO_POOL", "false").lower() == "true",
            )

        # SQLite (테스트용)
        elif parsed.scheme == "sqlite":
            return cls(use_test_db=True)

        else:
            raise ValueError(
                f"Unsupported database scheme: {parsed.scheme}. "
                f"Supported: postgresql, postgres, sqlite"
            )


@lru_cache()
def get_database_config() -> DatabaseConfig:
    """
    데이터베이스 설정 가져오기 (캐시됨)

    Returns:
        DatabaseConfig: 설정 인스턴스
    """
    return DatabaseConfig.from_env()


# 편의 함수
def get_database_url() -> str:
    """
    데이터베이스 URL 가져오기

    Returns:
        str: 데이터베이스 연결 URL
    """
    config = get_database_config()
    return config.database_url


def get_sync_database_url() -> str:
    """
    동기 데이터베이스 URL 가져오기 (Alembic용)

    Returns:
        str: 동기 데이터베이스 연결 URL
    """
    config = get_database_config()
    return config.sync_database_url
