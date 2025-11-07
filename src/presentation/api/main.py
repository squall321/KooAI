"""
FastAPI 애플리케이션

시뮬레이션 후처리 REST API.
"""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .exceptions import register_exception_handlers
from .routes import simulation_routes
from .middleware.security import SecurityHeadersMiddleware

# Rate limiter 초기화
limiter = Limiter(key_func=get_remote_address)

# FastAPI 앱 생성
app = FastAPI(
    title="Simulation Post-Processing API",
    description="AI-powered simulation result analysis and processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiter 등록
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 설정 (환경 변수 기반)
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# 프로덕션 환경 체크
is_production = os.getenv("KOOAI_ENV", "development") == "production"

if is_production and "*" in allowed_origins:
    raise ValueError(
        "Security Error: CORS allow_origins=['*'] is not allowed in production. "
        "Set ALLOWED_ORIGINS environment variable to specific domains."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,  # Preflight cache 1시간
)

# 보안 헤더 미들웨어
app.add_middleware(SecurityHeadersMiddleware)

# Gzip 압축 (응답 > 1KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 예외 핸들러 등록
register_exception_handlers(app)

# 라우터 등록
app.include_router(simulation_routes.router, prefix="/api/v1")


# 헬스 체크 엔드포인트
@app.get("/health", tags=["health"])
@limiter.limit("100/minute")  # Rate limiting: 분당 100회
async def health_check(request: Request):
    """헬스 체크"""
    return {"status": "healthy", "version": "1.0.0"}


# 루트 엔드포인트
@app.get("/", tags=["root"])
@limiter.limit("60/minute")  # Rate limiting: 분당 60회
async def root(request: Request):
    """API 루트"""
    return {
        "message": "Simulation Post-Processing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
