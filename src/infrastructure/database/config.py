"""
데이터베이스 설정 관리

환경 변수를 통해 데이터베이스 연결 설정을 관리합니다.
"""

import os
from dataclasses import dataclass
from typing import Optional
from functools import lru_cache


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
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """
        환경 변수로부터 설정 로드
        
        Returns:
            DatabaseConfig: 설정 인스턴스
        """
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
