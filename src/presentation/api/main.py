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
from .routes import simulation_routes, health_routes, metrics_routes
from .middleware.security import SecurityHeadersMiddleware

# Rate limiter 초기화
limiter = Limiter(key_func=get_remote_address)

# OpenAPI Tags (문서화용 카테고리)
tags_metadata = [
    {
        "name": "simulations",
        "description": "시뮬레이션 관리 - 업로드, 조회, 분석, 삭제",
    },
    {
        "name": "files",
        "description": "파일 작업 - 업로드, 다운로드, 메타데이터",
    },
    {
        "name": "analysis",
        "description": "AI 분석 - 필드 분석, 수렴성, 공간 분석, LLM 통합",
    },
    {
        "name": "health",
        "description": "헬스 체크 - Kubernetes 호환 프로브",
    },
    {
        "name": "metrics",
        "description": "메트릭 - Prometheus 모니터링 엔드포인트",
    },
    {
        "name": "root",
        "description": "루트 엔드포인트 - API 정보 및 버전",
    },
]

# FastAPI 앱 생성
app = FastAPI(
    title="KooAI - Simulation Post-Processing API",
    description="""
## AI 기반 시뮬레이션 후처리 플랫폼

KooAI는 CFD, FEA 등 시뮬레이션 결과를 분석하는 엔터프라이즈급 REST API입니다.

### 주요 기능

* **다양한 파일 형식**: CSV, VTK, VTU, HDF5
* **고급 분석**: 통계, 극값, 이상치, 수렴성, 공간 분석
* **AI 통합**: LLM 기반 자동 인사이트 생성
* **비동기 처리**: Celery 백그라운드 태스크
* **프로덕션 준비**: 모니터링, 로깅, 헬스 체크

### 인증

현재 버전은 API 키 인증을 사용합니다. 향후 JWT 인증이 추가될 예정입니다.

### Rate Limiting

* **Anonymous**: 10 req/min
* **Authenticated**: 100 req/min
* **Premium**: 1000 req/min

### 문서

* [Production Guide](https://github.com/yourusername/kooai/blob/main/docs/PRODUCTION_GUIDE.md)
* [API Guide](https://github.com/yourusername/kooai/blob/main/docs/API_GUIDE.md)
* [Monitoring Guide](https://github.com/yourusername/kooai/blob/main/docs/MONITORING_GUIDE.md)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "KooAI Support",
        "url": "https://github.com/yourusername/kooai/issues",
        "email": "support@kooai.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
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

# Health check routes (detailed with dependency checks)
app.include_router(health_routes.router, prefix="/api/v1")

# Prometheus metrics endpoint
app.include_router(metrics_routes.router, prefix="/api/v1")


# 헬스 체크 엔드포인트
@app.get(
    "/health/simple",
    tags=["health"],
    summary="Simple Health Check",
    description="빠른 헬스 체크 (외부 의존성 확인 없음)",
    response_description="서버 상태 및 버전",
)
@limiter.limit("100/minute")  # Rate limiting: 분당 100회
async def health_check(request: Request):
    """
    ## Simple Health Check

    외부 의존성(DB, Redis)을 확인하지 않는 빠른 헬스 체크입니다.

    ### Returns
    - **status**: 서버 상태 ("healthy")
    - **version**: API 버전

    ### Rate Limit
    - 100 requests/minute
    """
    return {"status": "healthy", "version": "1.0.0"}


# 루트 엔드포인트
@app.get(
    "/",
    tags=["root"],
    summary="API Root",
    description="API 정보 및 문서 링크",
    response_description="API 메타데이터",
)
@limiter.limit("60/minute")  # Rate limiting: 분당 60회
async def root(request: Request):
    """
    ## API Root Endpoint

    KooAI API의 루트 엔드포인트입니다.

    ### Returns
    - **message**: API 이름
    - **version**: API 버전
    - **docs**: Swagger UI 문서 경로
    - **health**: 헬스 체크 경로

    ### Example Response
    ```json
    {
        "message": "Simulation Post-Processing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
    ```

    ### Rate Limit
    - 60 requests/minute
    """
    return {
        "message": "Simulation Post-Processing API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health/simple",
        "metrics": "/api/v1/metrics",
    }
