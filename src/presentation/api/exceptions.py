"""
API 예외 처리

FastAPI 예외 핸들러 정의.
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.application.use_cases import (
    AlreadyExistsError,
    NotFoundError,
    UseCaseError,
    ValidationError,
)


def create_error_response(error_type: str, message: str, detail=None) -> dict:
    """에러 응답 생성"""
    response = {"error": error_type, "message": message}
    if detail:
        response["detail"] = detail
    return response


async def validation_error_handler(request: Request, exc: ValidationError):
    """ValidationError 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response("ValidationError", str(exc)),
    )


async def not_found_error_handler(request: Request, exc: NotFoundError):
    """NotFoundError 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=create_error_response("NotFoundError", str(exc)),
    )


async def already_exists_error_handler(request: Request, exc: AlreadyExistsError):
    """AlreadyExistsError 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=create_error_response("AlreadyExistsError", str(exc)),
    )


async def use_case_error_handler(request: Request, exc: UseCaseError):
    """UseCaseError 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response("UseCaseError", str(exc)),
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            "InternalServerError",
            "An unexpected error occurred",
            detail=str(exc) if request.app.debug else None,
        ),
    )


def register_exception_handlers(app):
    """예외 핸들러 등록"""
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(AlreadyExistsError, already_exists_error_handler)
    app.add_exception_handler(UseCaseError, use_case_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
