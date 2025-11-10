"""
데이터베이스 연결 관리

SQLAlchemy 비동기 엔진 및 세션 관리를 담당합니다.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

from src.infrastructure.database.models import (
    Base,
)


class DatabaseConnection:
    """
    데이터베이스 연결 관리 클래스

    비동기 SQLAlchemy 엔진과 세션을 관리합니다.
    """

    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
    ):
        """
        Args:
            database_url: 데이터베이스 URL
            echo: SQL 로깅 여부
            pool_size: 연결 풀 크기
            max_overflow: 최대 오버플로우
            pool_pre_ping: 연결 유효성 검사
        """
        self.database_url = database_url
        self.echo = echo

        # 비동기 엔진 생성
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=pool_pre_ping,
            future=True,
        )

        # 세션 팩토리
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def create_tables(self) -> None:
        """
        모든 테이블 생성

        개발 환경에서만 사용. 프로덕션에서는 Alembic 마이그레이션 사용
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """
        모든 테이블 삭제

        개발 및 테스트 환경에서만 사용
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        데이터베이스 세션 컨텍스트 매니저

        Yields:
            AsyncSession: 데이터베이스 세션

        Example:
            async with db.get_session() as session:
                result = await session.execute(query)
        """
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """엔진 종료"""
        await self.engine.dispose()


# 테스트용 인메모리 데이터베이스
class InMemoryDatabaseConnection(DatabaseConnection):
    """
    인메모리 데이터베이스 연결 (테스트용)

    SQLite 인메모리 데이터베이스를 사용합니다.
    """

    def __init__(self) -> None:
        # SQLite in-memory database with StaticPool to maintain single connection
        self.database_url = "sqlite+aiosqlite:///:memory:"
        self.echo = False

        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            echo=self.echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,  # StaticPool maintains a single connection
            future=True,
        )

        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
