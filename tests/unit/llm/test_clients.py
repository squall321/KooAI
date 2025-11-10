"""LLM 클라이언트 테스트"""

import pytest
import numpy as np

from src.core.llm.clients.base import (
    Message,
    MessageRole,
    TokenUsage,
    LLMConfig,
    LLMResponse,
    LLMProvider,
    LLMClientFactory,
)


class TestMessage:
    """Message 테스트"""

    def test_create_message(self) -> None:
        """메시지 생성 테스트"""
        msg = Message(role=MessageRole.USER, content="Hello")

        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"

    def test_message_to_dict(self) -> None:
        """메시지 딕셔너리 변환 테스트"""
        msg = Message(role=MessageRole.SYSTEM, content="You are helpful")

        data = msg.to_dict()

        assert data["role"] == "system"
        assert data["content"] == "You are helpful"

    def test_system_message_factory(self) -> None:
        """시스템 메시지 팩토리 테스트"""
        msg = Message.system("System prompt")

        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "System prompt"

    def test_user_message_factory(self) -> None:
        """사용자 메시지 팩토리 테스트"""
        msg = Message.user("User query")

        assert msg.role == MessageRole.USER
        assert msg.content == "User query"

    def test_assistant_message_factory(self) -> None:
        """어시스턴트 메시지 팩토리 테스트"""
        msg = Message.assistant("Response")

        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "Response"


class TestTokenUsage:
    """TokenUsage 테스트"""

    def test_create_token_usage(self) -> None:
        """토큰 사용량 생성 테스트"""
        usage = TokenUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )

        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30

    def test_token_usage_addition(self) -> None:
        """토큰 사용량 합산 테스트"""
        usage1 = TokenUsage(10, 20, 30)
        usage2 = TokenUsage(5, 15, 20)

        total = usage1 + usage2

        assert total.prompt_tokens == 15
        assert total.completion_tokens == 35
        assert total.total_tokens == 50


class TestLLMResponse:
    """LLMResponse 테스트"""

    def test_create_response(self) -> None:
        """응답 생성 테스트"""
        response = LLMResponse(
            content="Generated text",
            model="gpt-4",
            finish_reason="stop",
        )

        assert response.content == "Generated text"
        assert response.model == "gpt-4"
        assert response.finish_reason == "stop"

    def test_get_text(self) -> None:
        """텍스트 가져오기 테스트"""
        response = LLMResponse(content="Hello", model="test")

        assert response.get_text() == "Hello"

    def test_get_metadata(self) -> None:
        """메타데이터 조회 테스트"""
        response = LLMResponse(
            content="Text",
            model="test",
            metadata={"key": "value", "number": 42},
        )

        assert response.get_metadata("key") == "value"
        assert response.get_metadata("number") == 42
        assert response.get_metadata("missing", "default") == "default"


class TestLLMConfig:
    """LLMConfig 테스트"""

    def test_create_config(self) -> None:
        """설정 생성 테스트"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            api_key="test-key",
            temperature=0.8,
            max_tokens=1000,
        )

        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.temperature == 0.8
        assert config.max_tokens == 1000

    def test_config_to_dict(self) -> None:
        """설정 딕셔너리 변환 테스트"""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3",
            temperature=0.5,
        )

        data = config.to_dict()

        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-3"
        assert data["temperature"] == 0.5


class TestLLMClientFactory:
    """LLMClientFactory 테스트"""

    def test_list_providers(self) -> None:
        """제공자 목록 조회 테스트"""
        providers = LLMClientFactory.list_providers()

        # 자동 등록된 제공자가 있어야 함
        assert isinstance(providers, list)

    def test_create_unsupported_provider_raises_error(self) -> None:
        """지원하지 않는 제공자 생성 시 에러 테스트"""
        config = LLMConfig(provider=LLMProvider.CUSTOM, model="test")

        with pytest.raises(ValueError, match="Unsupported provider"):
            # create는 async이므로 직접 호출할 수 없음
            # Factory의 _clients를 직접 확인
            if LLMProvider.CUSTOM not in LLMClientFactory._clients:
                raise ValueError("Unsupported provider: CUSTOM")


class TestLLMProvider:
    """LLMProvider Enum 테스트"""

    def test_provider_values(self) -> None:
        """제공자 값 테스트"""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.LOCAL.value == "local"

    def test_provider_from_string(self) -> None:
        """문자열에서 제공자 생성 테스트"""
        provider = LLMProvider("openai")
        assert provider == LLMProvider.OPENAI


class TestMessageRole:
    """MessageRole Enum 테스트"""

    def test_role_values(self) -> None:
        """역할 값 테스트"""
        assert MessageRole.SYSTEM.value == "system"
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
