"""
FastAPI 의존성 주입

리포지토리, 서비스 등의 의존성을 제공.
"""

from functools import lru_cache
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from src.application.services import SimulationService
from src.core.repositories.interfaces import SimulationResultRepository
from src.infrastructure.database.database import SessionLocal
from src.infrastructure.repositories.memory_simulation_repository import (
    InMemorySimulationResultRepository,
)


# ============================================================================
# Database Dependencies
# ============================================================================


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성

    FastAPI 엔드포인트에서 SQLAlchemy Session을 제공하고,
    요청 완료 후 자동으로 세션을 닫습니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Repository Dependencies
# ============================================================================


@lru_cache()
def get_simulation_repository() -> SimulationResultRepository:
    """
    시뮬레이션 리포지토리 의존성

    싱글톤 패턴으로 리포지토리 인스턴스 제공.
    """
    return InMemorySimulationResultRepository()


# ============================================================================
# Service Dependencies
# ============================================================================


def get_simulation_service(
    repository: SimulationResultRepository = Depends(get_simulation_repository),
) -> SimulationService:
    """
    시뮬레이션 서비스 의존성

    리포지토리를 주입받아 서비스 인스턴스 생성.
    """
    return SimulationService(repository)
