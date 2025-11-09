"""
Core Domain Exceptions

도메인 레벨의 예외 클래스들을 정의합니다.
Clean Architecture의 Core 레이어에 위치하며, 프레임워크에 독립적입니다.
"""

from typing import Any, Dict, Optional


class KooAIError(Exception):
    """
    KooAI 기본 예외 클래스

    모든 KooAI 커스텀 예외의 베이스 클래스.

    Attributes:
        message: 에러 메시지
        error_code: 에러 코드 (예: "PARSE_001")
        details: 추가 상세 정보
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self._default_error_code()
        self.details = details or {}
        super().__init__(self.message)

    def _default_error_code(self) -> str:
        """기본 에러 코드 생성"""
        return self.__class__.__name__.upper()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (API 응답용)"""
        result: Dict[str, Any] = {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


# =============================================================================
# 파싱 관련 예외
# =============================================================================


class ParsingError(KooAIError):
    """파일 파싱 중 발생하는 에러"""

    def _default_error_code(self) -> str:
        return "PARSE_ERROR"


class UnsupportedFormatError(ParsingError):
    """지원하지 않는 파일 형식"""

    def _default_error_code(self) -> str:
        return "PARSE_001"


class CorruptedFileError(ParsingError):
    """손상된 파일"""

    def _default_error_code(self) -> str:
        return "PARSE_002"


class InvalidDataError(ParsingError):
    """잘못된 데이터 형식"""

    def _default_error_code(self) -> str:
        return "PARSE_003"


class MissingFieldError(ParsingError):
    """필수 필드 누락"""

    def __init__(
        self,
        field_name: str,
        message: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.field_name = field_name
        msg = message or f"Required field missing: {field_name}"
        super().__init__(msg, details={"field_name": field_name}, **kwargs)

    def _default_error_code(self) -> str:
        return "PARSE_004"


# =============================================================================
# 파일 시스템 관련 예외
# =============================================================================


class FileSystemError(KooAIError):
    """파일 시스템 관련 에러"""

    def _default_error_code(self) -> str:
        return "FS_ERROR"


class FileNotFoundError(FileSystemError):
    """파일을 찾을 수 없음"""

    def __init__(self, file_path: str, **kwargs: Any) -> None:
        self.file_path = file_path
        super().__init__(
            f"File not found: {file_path}",
            details={"file_path": file_path},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "FS_001"


class FilePermissionError(FileSystemError):
    """파일 접근 권한 없음"""

    def __init__(self, file_path: str, operation: str = "read", **kwargs: Any) -> None:
        self.file_path = file_path
        self.operation = operation
        super().__init__(
            f"Permission denied: {operation} {file_path}",
            details={"file_path": file_path, "operation": operation},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "FS_002"


class FileTooLargeError(FileSystemError):
    """파일 크기 초과"""

    def __init__(self, file_path: str, size: int, max_size: int, **kwargs: Any) -> None:
        self.file_path = file_path
        self.size = size
        self.max_size = max_size
        super().__init__(
            f"File too large: {size} bytes (max: {max_size} bytes)",
            details={"file_path": file_path, "size": size, "max_size": max_size},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "FS_003"


# =============================================================================
# 시뮬레이션 데이터 관련 예외
# =============================================================================


class SimulationError(KooAIError):
    """시뮬레이션 데이터 관련 에러"""

    def _default_error_code(self) -> str:
        return "SIM_ERROR"


class InvalidTimestepError(SimulationError):
    """잘못된 타임스텝"""

    def __init__(self, timestep: int, **kwargs: Any) -> None:
        self.timestep = timestep
        super().__init__(
            f"Invalid timestep: {timestep}",
            details={"timestep": timestep},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "SIM_001"


class FieldNotFoundError(SimulationError):
    """필드를 찾을 수 없음"""

    def __init__(self, field_name: str, available_fields: Optional[list] = None, **kwargs: Any) -> None:
        self.field_name = field_name
        self.available_fields = available_fields
        details: Dict[str, Any] = {"field_name": field_name}
        if available_fields:
            details["available_fields"] = available_fields
        super().__init__(
            f"Field not found: {field_name}",
            details=details,
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "SIM_002"


class EmptyDataError(SimulationError):
    """빈 데이터"""

    def _default_error_code(self) -> str:
        return "SIM_003"


class IncompatibleDataError(SimulationError):
    """호환되지 않는 데이터 (예: 비교 불가능한 타임스텝)"""

    def _default_error_code(self) -> str:
        return "SIM_004"


# =============================================================================
# 계산 관련 예외
# =============================================================================


class ComputationError(KooAIError):
    """계산 중 발생하는 에러"""

    def _default_error_code(self) -> str:
        return "COMPUTE_ERROR"


class NumericalInstabilityError(ComputationError):
    """수치 불안정성 (NaN, Inf 등)"""

    def __init__(self, operation: str, **kwargs: Any) -> None:
        self.operation = operation
        super().__init__(
            f"Numerical instability detected in: {operation}",
            details={"operation": operation},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "COMPUTE_001"


class ConvergenceError(ComputationError):
    """수렴하지 않음"""

    def __init__(self, iterations: int, tolerance: float, **kwargs: Any) -> None:
        self.iterations = iterations
        self.tolerance = tolerance
        super().__init__(
            f"Failed to converge after {iterations} iterations (tolerance: {tolerance})",
            details={"iterations": iterations, "tolerance": tolerance},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "COMPUTE_002"


class InsufficientDataError(ComputationError):
    """데이터 부족 (통계 계산 등)"""

    def __init__(self, required: int, actual: int, **kwargs: Any) -> None:
        self.required = required
        self.actual = actual
        super().__init__(
            f"Insufficient data points: {actual} (required: {required})",
            details={"required": required, "actual": actual},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "COMPUTE_003"


# =============================================================================
# 데이터베이스 관련 예외
# =============================================================================


class DatabaseError(KooAIError):
    """데이터베이스 관련 에러"""

    def _default_error_code(self) -> str:
        return "DB_ERROR"


class ConnectionError(DatabaseError):
    """데이터베이스 연결 실패"""

    def _default_error_code(self) -> str:
        return "DB_001"


class TransactionError(DatabaseError):
    """트랜잭션 실패"""

    def _default_error_code(self) -> str:
        return "DB_002"


class IntegrityError(DatabaseError):
    """데이터 무결성 위반"""

    def _default_error_code(self) -> str:
        return "DB_003"


# =============================================================================
# 캐시 관련 예외
# =============================================================================


class CacheError(KooAIError):
    """캐시 관련 에러"""

    def _default_error_code(self) -> str:
        return "CACHE_ERROR"


class CacheConnectionError(CacheError):
    """캐시 연결 실패"""

    def _default_error_code(self) -> str:
        return "CACHE_001"


class CacheSerializationError(CacheError):
    """캐시 직렬화/역직렬화 실패"""

    def _default_error_code(self) -> str:
        return "CACHE_002"


# =============================================================================
# AI/ML 관련 예외
# =============================================================================


class AIError(KooAIError):
    """AI/ML 관련 에러"""

    def _default_error_code(self) -> str:
        return "AI_ERROR"


class ModelNotFoundError(AIError):
    """AI 모델을 찾을 수 없음"""

    def __init__(self, model_name: str, **kwargs: Any) -> None:
        self.model_name = model_name
        super().__init__(
            f"Model not found: {model_name}",
            details={"model_name": model_name},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "AI_001"


class ModelLoadError(AIError):
    """AI 모델 로드 실패"""

    def _default_error_code(self) -> str:
        return "AI_002"


class InferenceError(AIError):
    """AI 추론 실패"""

    def _default_error_code(self) -> str:
        return "AI_003"


# =============================================================================
# 설정 관련 예외
# =============================================================================


class ConfigurationError(KooAIError):
    """설정 관련 에러"""

    def _default_error_code(self) -> str:
        return "CONFIG_ERROR"


class MissingConfigError(ConfigurationError):
    """필수 설정 누락"""

    def __init__(self, config_key: str, **kwargs: Any) -> None:
        self.config_key = config_key
        super().__init__(
            f"Missing required configuration: {config_key}",
            details={"config_key": config_key},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "CONFIG_001"


class InvalidConfigError(ConfigurationError):
    """잘못된 설정 값"""

    def __init__(self, config_key: str, value: Any, reason: str, **kwargs: Any) -> None:
        self.config_key = config_key
        self.value = value
        self.reason = reason
        super().__init__(
            f"Invalid configuration {config_key}={value}: {reason}",
            details={"config_key": config_key, "value": str(value), "reason": reason},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "CONFIG_002"


# =============================================================================
# 외부 서비스 관련 예외
# =============================================================================


class ExternalServiceError(KooAIError):
    """외부 서비스 연동 에러"""

    def _default_error_code(self) -> str:
        return "EXTERNAL_ERROR"


class APIConnectionError(ExternalServiceError):
    """외부 API 연결 실패"""

    def __init__(self, service_name: str, **kwargs: Any) -> None:
        self.service_name = service_name
        super().__init__(
            f"Failed to connect to external service: {service_name}",
            details={"service_name": service_name},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "EXTERNAL_001"


class APITimeoutError(ExternalServiceError):
    """외부 API 타임아웃"""

    def __init__(self, service_name: str, timeout: float, **kwargs: Any) -> None:
        self.service_name = service_name
        self.timeout = timeout
        super().__init__(
            f"Timeout connecting to {service_name} ({timeout}s)",
            details={"service_name": service_name, "timeout": timeout},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "EXTERNAL_002"


class APIRateLimitError(ExternalServiceError):
    """외부 API rate limit 초과"""

    def __init__(self, service_name: str, retry_after: Optional[int] = None, **kwargs: Any) -> None:
        self.service_name = service_name
        self.retry_after = retry_after
        msg = f"Rate limit exceeded for {service_name}"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(
            msg,
            details={"service_name": service_name, "retry_after": retry_after},
            **kwargs,
        )

    def _default_error_code(self) -> str:
        return "EXTERNAL_003"
