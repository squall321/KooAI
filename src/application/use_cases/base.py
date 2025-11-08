"""
Application Use Cases

비즈니스 로직을 캡슐화한 Use Case 구현.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class UseCase(ABC, Generic[TRequest, TResponse]):
    """
    Use Case 기본 클래스

    모든 Use Case는 이 클래스를 상속하여 구현.
    단일 책임 원칙을 따라 하나의 비즈니스 로직만 처리.
    """

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """
        Use Case 실행

        Args:
            request: 요청 데이터

        Returns:
            응답 데이터
        """
        pass


class UseCaseError(Exception):
    """Use Case 실행 중 발생하는 에러"""

    pass


class ValidationError(UseCaseError):
    """입력 검증 에러"""

    pass


class NotFoundError(UseCaseError):
    """리소스를 찾을 수 없음"""

    pass


class AlreadyExistsError(UseCaseError):
    """이미 존재하는 리소스"""

    pass
