"""
FastAPI 데이터베이스 의존성

FastAPI 라우트에서 사용할 데이터베이스 세션 의존성을 제공합니다.
"""

from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.config import get_database_config
from src.infrastructure.repositories.sql_repository import (
    SimulationRepository,
    DatasetRepository,
    AnalysisRepository,
    AIModelRepository,
)


# 전역 데이터베이스 연결 (애플리케이션 시작 시 초기화)
_db_connection: DatabaseConnection | None = None


def init_database() -> DatabaseConnection:
    """
    데이터베이스 연결 초기화

    애플리케이션 시작 시 한 번 호출됩니다.

    Returns:
        DatabaseConnection: 데이터베이스 연결 인스턴스
    """
    global _db_connection

    if _db_connection is not None:
        return _db_connection

    config = get_database_config()

    _db_connection = DatabaseConnection(
        database_url=config.database_url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=config.pool_pre_ping,
    )

    return _db_connection


def get_database_connection() -> DatabaseConnection:
    """
    데이터베이스 연결 가져오기

    Returns:
        DatabaseConnection: 데이터베이스 연결 인스턴스

    Raises:
        RuntimeError: 데이터베이스가 초기화되지 않은 경우
    """
    if _db_connection is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_connection


async def close_database() -> None:
    """
    데이터베이스 연결 종료

    애플리케이션 종료 시 호출됩니다.
    """
    global _db_connection

    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None


# FastAPI 의존성


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    데이터베이스 세션 의존성

    FastAPI 라우트에서 Depends(get_db_session)로 사용합니다.

    Yields:
        AsyncSession: 데이터베이스 세션

    Example:
        @app.get("/simulations/{id}")
        async def get_simulation(
            id: UUID,
            session: AsyncSession = Depends(get_db_session)
        ):
            repo = SimulationRepository(session)
            return await repo.find_by_id(id)
    """
    db = get_database_connection()

    async with db.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Repository 의존성 (선택적 - 더 높은 수준의 추상화)


async def get_simulation_repository(
    session: Optional[AsyncSession] = None,
) -> AsyncGenerator[SimulationRepository, None]:
    """
    시뮬레이션 리포지토리 의존성

    Yields:
        SimulationRepository: 시뮬레이션 리포지토리

    Example:
        @app.get("/simulations/{id}")
        async def get_simulation(
            id: UUID,
            repo: SimulationRepository = Depends(get_simulation_repository)
        ):
            return await repo.find_by_id(id)
    """
    if session is None:
        async for session in get_db_session():
            yield SimulationRepository(session)
    else:
        yield SimulationRepository(session)


async def get_dataset_repository(
    session: Optional[AsyncSession] = None,
) -> AsyncGenerator[DatasetRepository, None]:
    """
    데이터셋 리포지토리 의존성

    Yields:
        DatasetRepository: 데이터셋 리포지토리
    """
    if session is None:
        async for session in get_db_session():
            yield DatasetRepository(session)
    else:
        yield DatasetRepository(session)


async def get_analysis_repository(
    session: Optional[AsyncSession] = None,
) -> AsyncGenerator[AnalysisRepository, None]:
    """
    분석 리포지토리 의존성

    Yields:
        AnalysisRepository: 분석 리포지토리
    """
    if session is None:
        async for session in get_db_session():
            yield AnalysisRepository(session)
    else:
        yield AnalysisRepository(session)


async def get_ai_model_repository(
    session: Optional[AsyncSession] = None,
) -> AsyncGenerator[AIModelRepository, None]:
    """
    AI 모델 리포지토리 의존성

    Yields:
        AIModelRepository: AI 모델 리포지토리
    """
    if session is None:
        async for session in get_db_session():
            yield AIModelRepository(session)
    else:
        yield AIModelRepository(session)


# 애플리케이션 수명 주기 관리


@asynccontextmanager
async def database_lifespan() -> AsyncGenerator[None, None]:
    """
    데이터베이스 수명 주기 관리

    FastAPI 앱의 lifespan 컨텍스트 매니저로 사용합니다.

    Example:
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with database_lifespan():
                yield

        app = FastAPI(lifespan=lifespan)
    """
    # 시작
    init_database()

    try:
        yield
    finally:
        # 종료
        await close_database()
