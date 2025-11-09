"""
API 예외 처리

FastAPI 예외 핸들러 정의.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.application.use_cases import (
    AlreadyExistsError,
    NotFoundError,
    UseCaseError,
    ValidationError as UseCaseValidationError,
)
from src.core.exceptions import (
    AIError,
    CacheError,
    ComputationError,
    ConfigurationError,
    DatabaseError,
    ExternalServiceError,
    FileSystemError,
    KooAIError,
    ParsingError,
    SimulationError,
)

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """요청 ID 생성 (디버깅용)"""
    return str(uuid.uuid4())


def create_error_response(
    error_type: str,
    message: str,
    status_code: int,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    구조화된 에러 응답 생성

    Args:
        error_type: 에러 타입 (예: "ValidationError")
        message: 에러 메시지
        status_code: HTTP 상태 코드
        error_code: 에러 코드 (예: "PARSE_001")
        details: 추가 상세 정보
        request_id: 요청 ID (디버깅용)

    Returns:
        에러 응답 딕셔너리
    """
    response: Dict[str, Any] = {
        "error": {
            "type": error_type,
            "message": message,
            "status_code": status_code,
        }
    }

    if error_code:
        response["error"]["code"] = error_code

    if details:
        response["error"]["details"] = details

    if request_id:
        response["request_id"] = request_id

    return response


# =============================================================================
# Use Case Exception Handlers (Application Layer)
# =============================================================================


async def validation_error_handler(request: Request, exc: UseCaseValidationError) -> JSONResponse:
    """ValidationError 핸들러"""
    request_id = generate_request_id()
    logger.warning(
        f"Validation error: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            error_type="ValidationError",
            message=str(exc),
            status_code=400,
            request_id=request_id,
        ),
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """NotFoundError 핸들러"""
    request_id = generate_request_id()
    logger.info(
        f"Resource not found: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response(
            error_type="NotFoundError",
            message=str(exc),
            status_code=404,
            request_id=request_id,
        ),
    )


async def already_exists_error_handler(request: Request, exc: AlreadyExistsError) -> JSONResponse:
    """AlreadyExistsError 핸들러"""
    request_id = generate_request_id()
    logger.warning(
        f"Resource already exists: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=create_error_response(
            error_type="AlreadyExistsError",
            message=str(exc),
            status_code=409,
            request_id=request_id,
        ),
    )


async def use_case_error_handler(request: Request, exc: UseCaseError) -> JSONResponse:
    """UseCaseError 핸들러"""
    request_id = generate_request_id()
    logger.error(
        f"Use case error: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error_type="UseCaseError",
            message=str(exc),
            status_code=500,
            request_id=request_id,
        ),
    )


# =============================================================================
# Core Domain Exception Handlers
# =============================================================================


async def kooai_error_handler(request: Request, exc: KooAIError) -> JSONResponse:
    """
    KooAI 커스텀 예외 핸들러

    모든 KooAIError의 기본 핸들러. to_dict() 메서드를 사용하여
    구조화된 에러 응답을 생성.
    """
    request_id = generate_request_id()

    # 에러 타입별 HTTP 상태 코드 매핑
    status_code_map = {
        # Parsing errors
        ParsingError: status.HTTP_400_BAD_REQUEST,
        # File system errors
        FileSystemError: status.HTTP_400_BAD_REQUEST,
        # Simulation errors
        SimulationError: status.HTTP_400_BAD_REQUEST,
        # Computation errors
        ComputationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        # Database errors
        DatabaseError: status.HTTP_503_SERVICE_UNAVAILABLE,
        # Cache errors
        CacheError: status.HTTP_503_SERVICE_UNAVAILABLE,
        # AI errors
        AIError: status.HTTP_503_SERVICE_UNAVAILABLE,
        # Configuration errors
        ConfigurationError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        # External service errors
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    }

    # 에러 타입에 따른 상태 코드 선택
    http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
    for error_class, error_status in status_code_map.items():
        if isinstance(exc, error_class):
            http_status = error_status
            break

    # 로그 레벨 결정 (4xx는 warning, 5xx는 error)
    if 400 <= http_status < 500:
        logger.warning(
            f"Client error: {exc}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "error_code": exc.error_code,
            },
        )
    else:
        logger.error(
            f"Server error: {exc}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "error_code": exc.error_code,
            },
            exc_info=True,
        )

    error_dict = exc.to_dict()
    return JSONResponse(
        status_code=http_status,
        content=create_error_response(
            error_type=error_dict["error_type"],
            message=error_dict["message"],
            status_code=http_status,
            error_code=error_dict.get("error_code"),
            details=error_dict.get("details"),
            request_id=request_id,
        ),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """FastAPI HTTPException 핸들러"""
    request_id = generate_request_id()
    logger.info(
        f"HTTP exception: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            error_type="HTTPException",
            message=exc.detail,
            status_code=exc.status_code,
            request_id=request_id,
        ),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    일반 예외 핸들러

    처리되지 않은 모든 예외를 캐치하여 500 응답 반환.
    디버그 모드에서만 상세 정보 노출.
    """
    request_id = generate_request_id()
    logger.exception(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id, "path": request.url.path},
    )

    # 디버그 모드에서만 상세 에러 정보 노출
    is_debug = getattr(request.app.state, "debug", False)
    details = None
    if is_debug:
        details = {
            "exception_type": exc.__class__.__name__,
            "exception_message": str(exc),
        }

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            error_type="InternalServerError",
            message="An unexpected error occurred. Please contact support with the request_id.",
            status_code=500,
            details=details,
            request_id=request_id,
        ),
    )


def register_exception_handlers(app: Any) -> None:
    """
    예외 핸들러 등록

    등록 순서가 중요합니다:
    1. 가장 구체적인 예외부터 등록 (Use Case errors)
    2. 도메인 예외 (KooAI errors)
    3. FastAPI 예외 (HTTPException)
    4. 일반 예외 (Exception)

    상속 관계를 고려하여 자식 클래스를 먼저 등록해야 합니다.
    """
    # Application Layer exceptions (Use Case)
    app.add_exception_handler(UseCaseValidationError, validation_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(AlreadyExistsError, already_exists_error_handler)
    app.add_exception_handler(UseCaseError, use_case_error_handler)

    # Core Domain exceptions (KooAI errors)
    # 모든 KooAIError 서브클래스를 한 번에 처리
    app.add_exception_handler(KooAIError, kooai_error_handler)

    # FastAPI built-in exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Catch-all for any unhandled exceptions
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Exception handlers registered successfully")
