"""
동기 데이터베이스 세션 관리

FastAPI 의존성 주입을 위한 동기 SQLAlchemy 세션을 제공합니다.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import get_sync_database_url, get_database_config

# 데이터베이스 설정 가져오기
config = get_database_config()

# 동기 엔진 생성 (테스트 모드면 SQLite 사용)
if config.use_test_db or os.getenv("TESTING", "false").lower() == "true":
    # SQLite (테스트용)
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL (프로덕션용)
    try:
        engine = create_engine(
            get_sync_database_url(),
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=5,
        )
    except Exception:
        # psycopg2 없으면 SQLite fallback
        engine = create_engine(
            "sqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
        )

# 동기 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_session() -> Session:
    """
    동기 데이터베이스 세션 가져오기

    Returns:
        Session: SQLAlchemy Session 인스턴스
    """
    return SessionLocal()
