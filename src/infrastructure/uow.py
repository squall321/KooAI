"""
Unit of Work 패턴

트랜잭션을 관리하고 여러 Repository를 조율합니다.
"""

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repositories.sql_repository import (
    SimulationRepository,
    DatasetRepository,
    AnalysisRepository,
    AIModelRepository,
)


class UnitOfWork:
    """
    Unit of Work 패턴 구현

    여러 Repository의 작업을 하나의 트랜잭션으로 묶어 관리합니다.
    """

    def __init__(self, session: AsyncSession):
        """
        Args:
            session: SQLAlchemy 비동기 세션
        """
        self.session = session

        # Repository 인스턴스 생성
        self.simulations = SimulationRepository(session)
        self.datasets = DatasetRepository(session)
        self.analyses = AnalysisRepository(session)
        self.ai_models = AIModelRepository(session)

    async def commit(self) -> None:
        """
        모든 변경사항을 커밋합니다.

        Raises:
            Exception: 커밋 중 오류 발생 시
        """
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def rollback(self) -> None:
        """
        모든 변경사항을 롤백합니다.
        """
        await self.session.rollback()

    async def flush(self) -> None:
        """
        세션을 플러시합니다 (커밋하지 않고 SQL 실행).
        """
        await self.session.flush()

    async def close(self) -> None:
        """
        세션을 닫습니다.
        """
        await self.session.close()


@asynccontextmanager
async def get_uow(session: AsyncSession):
    """
    Unit of Work 컨텍스트 매니저

    Args:
        session: SQLAlchemy 비동기 세션

    Yields:
        UnitOfWork: Unit of Work 인스턴스

    Example:
        async with get_uow(session) as uow:
            simulation = SimulationResult(...)
            await uow.simulations.save(simulation)
            await uow.commit()
    """
    uow = UnitOfWork(session)
    try:
        yield uow
    except Exception:
        await uow.rollback()
        raise
    finally:
        await uow.close()
