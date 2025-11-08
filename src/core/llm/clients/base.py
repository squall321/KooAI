"""
LLM 클라이언트 기본 인터페이스

다양한 LLM 제공자를 통합하기 위한 추상화 계층.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Protocol
import numpy as np


class MessageRole(str, Enum):
    """메시지 역할"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class LLMProvider(str, Enum):
    """LLM 제공자"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class Message:
    """채팅 메시지"""

    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = {"role": self.role.value, "content": self.content}
        if self.name:
            data["name"] = self.name
        if self.function_call:
            data["function_call"] = self.function_call
        return data

    @classmethod
    def system(cls, content: str) -> "Message":
        """시스템 메시지 생성"""
        return cls(role=MessageRole.SYSTEM, content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        """사용자 메시지 생성"""
        return cls(role=MessageRole.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> "Message":
        """어시스턴트 메시지 생성"""
        return cls(role=MessageRole.ASSISTANT, content=content)


@dataclass
class TokenUsage:
    """토큰 사용량"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """토큰 사용량 합산"""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


@dataclass
class LLMResponse:
    """LLM 응답"""

    content: str
    model: str
    finish_reason: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_response: Optional[Any] = None

    def get_text(self) -> str:
        """텍스트 내용 반환"""
        return self.content

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 조회"""
        return self.metadata.get(key, default)


@dataclass
class LLMConfig:
    """LLM 설정"""

    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: float = 60.0
    max_retries: int = 3
    streaming: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            **self.extra_params,
        }


class ILLMClient(Protocol):
    """
    LLM 클라이언트 인터페이스

    다양한 LLM 제공자를 통일된 방식으로 사용하기 위한 프로토콜.
    """

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        텍스트 생성

        Args:
            prompt: 프롬프트
            context: 추가 컨텍스트 (optional)
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 생성 결과
        """
        ...

    async def chat(
        self,
        messages: List[Message],
        **kwargs,
    ) -> LLMResponse:
        """
        채팅 대화

        Args:
            messages: 메시지 리스트
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 응답 메시지
        """
        ...

    async def embed(self, text: str, **kwargs) -> np.ndarray:
        """
        텍스트 임베딩

        Args:
            text: 임베딩할 텍스트
            **kwargs: 추가 파라미터

        Returns:
            np.ndarray: 임베딩 벡터
        """
        ...

    async def stream_generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        스트리밍 텍스트 생성

        Args:
            prompt: 프롬프트
            context: 추가 컨텍스트
            **kwargs: 추가 파라미터

        Yields:
            str: 생성된 텍스트 청크
        """
        ...


class BaseLLMClient(ABC):
    """
    LLM 클라이언트 기본 추상 클래스

    공통 기능을 제공하는 추상 클래스.
    """

    def __init__(self, config: LLMConfig):
        """
        Args:
            config: LLM 설정
        """
        self.config = config
        self._client: Optional[Any] = None
        self._is_initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """클라이언트 초기화 (서브클래스에서 구현)"""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> LLMResponse:
        """텍스트 생성 (서브클래스에서 구현)"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        **kwargs,
    ) -> LLMResponse:
        """채팅 대화 (서브클래스에서 구현)"""
        pass

    async def embed(self, text: str, **kwargs) -> np.ndarray:
        """
        텍스트 임베딩 기본 구현

        서브클래스에서 오버라이드 가능.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support embeddings")

    async def stream_generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        스트리밍 생성 기본 구현

        서브클래스에서 오버라이드 가능.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support streaming")

    async def close(self) -> None:
        """클라이언트 종료"""
        if self._client is not None:
            if hasattr(self._client, "close"):
                await self._client.close()
            self._client = None
            self._is_initialized = False

    def _ensure_initialized(self) -> None:
        """초기화 확인"""
        if not self._is_initialized:
            raise RuntimeError(
                f"{self.__class__.__name__} not initialized. Call initialize() first."
            )

    def _build_generation_params(self, **kwargs) -> Dict[str, Any]:
        """생성 파라미터 구성"""
        params = {
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "top_p": kwargs.get("top_p", self.config.top_p),
        }

        # None 값 제거
        params = {k: v for k, v in params.items() if v is not None}

        return params


class LLMClientFactory:
    """
    LLM 클라이언트 팩토리

    제공자에 따라 적절한 클라이언트를 생성합니다.
    """

    _clients: Dict[LLMProvider, type[BaseLLMClient]] = {}

    @classmethod
    def register(cls, provider: LLMProvider, client_class: type[BaseLLMClient]) -> None:
        """
        클라이언트 등록

        Args:
            provider: LLM 제공자
            client_class: 클라이언트 클래스
        """
        cls._clients[provider] = client_class

    @classmethod
    async def create(cls, provider: LLMProvider, config: LLMConfig) -> BaseLLMClient:
        """
        클라이언트 생성 및 초기화

        Args:
            provider: LLM 제공자
            config: LLM 설정

        Returns:
            BaseLLMClient: 초기화된 클라이언트

        Raises:
            ValueError: 지원하지 않는 제공자일 때
        """
        if provider not in cls._clients:
            raise ValueError(
                f"Unsupported provider: {provider}. " f"Available: {list(cls._clients.keys())}"
            )

        client = cls._clients[provider](config)
        await client.initialize()
        return client

    @classmethod
    def list_providers(cls) -> List[LLMProvider]:
        """등록된 제공자 목록 반환"""
        return list(cls._clients.keys())
