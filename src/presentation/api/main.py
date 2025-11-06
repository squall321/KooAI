"""
FastAPI 애플리케이션

시뮬레이션 후처리 REST API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .exceptions import register_exception_handlers
from .routes import simulation_routes

# FastAPI 앱 생성
app = FastAPI(
    title="Simulation Post-Processing API",
    description="AI-powered simulation result analysis and processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 예외 핸들러 등록
register_exception_handlers(app)

# 라우터 등록
app.include_router(simulation_routes.router, prefix="/api/v1")


# 헬스 체크 엔드포인트
@app.get("/health", tags=["health"])
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "version": "1.0.0"}


# 루트 엔드포인트
@app.get("/", tags=["root"])
async def root():
    """API 루트"""
    return {
        "message": "Simulation Post-Processing API",
        "version": "1.0.0",
        "docs": "/docs",
    }
