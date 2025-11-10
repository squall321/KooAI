"""
Anthropic 클라이언트

Anthropic Claude API를 사용한 LLM 클라이언트 구현.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

import numpy as np

from .base import (
    BaseLLMClient,
    LLMResponse,
    Message,
    MessageRole,
    TokenUsage,
)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API 클라이언트"""

    async def initialize(self) -> None:
        """Anthropic 클라이언트 초기화"""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        # API 키 설정
        if not self.config.api_key:
            raise ValueError("Anthropic API key is required")

        # 비동기 클라이언트 생성
        self._client = anthropic.AsyncAnthropic(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )

        self._is_initialized = True

    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        텍스트 생성

        Args:
            prompt: 프롬프트
            context: 추가 컨텍스트 (system prompt로 사용)
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 생성 결과
        """
        self._ensure_initialized()

        # 메시지 구성
        messages = [Message.user(prompt)]

        # 시스템 프롬프트 (context)
        system_prompt = None
        if context:
            system_prompt = self._format_context(context)

        return await self.chat(messages, system=system_prompt, **kwargs)

    async def chat(
        self,
        messages: List[Message],
        **kwargs: Any,
    ) -> LLMResponse:
        """
        채팅 대화

        Args:
            messages: 메시지 리스트
            **kwargs: 추가 파라미터
                - system: 시스템 프롬프트 (선택적)

        Returns:
            LLMResponse: 응답 메시지
        """
        self._ensure_initialized()

        # 생성 파라미터
        params = self._build_generation_params(**kwargs)

        # Anthropic은 system 메시지를 별도로 처리
        system_prompt = kwargs.get("system")
        anthropic_messages = []

        for msg in messages:
            # system 메시지는 별도 처리
            if msg.role == MessageRole.SYSTEM:
                if system_prompt is None:
                    system_prompt = msg.content
                else:
                    system_prompt = f"{system_prompt}\n\n{msg.content}"
            else:
                anthropic_messages.append(
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                    }
                )

        try:
            # API 호출
            call_params = {
                "model": self.config.model,
                "messages": anthropic_messages,
                **params,
            }

            # 시스템 프롬프트 추가 (있으면)
            if system_prompt:
                call_params["system"] = system_prompt

            response = await self._client.messages.create(**call_params)

            # 응답 파싱
            content = response.content[0].text

            # 토큰 사용량
            usage = TokenUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            )

            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=response.stop_reason,
                token_usage=usage,
                metadata={
                    "id": response.id,
                    "type": response.type,
                },
                raw_response=response,
            )

        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")

    async def embed(self, text: str, **kwargs: Any) -> np.ndarray:
        """
        텍스트 임베딩

        Note: Anthropic은 현재 임베딩 API를 제공하지 않음.

        Raises:
            NotImplementedError: 항상 발생
        """
        raise NotImplementedError(
            "Anthropic does not provide embedding API. " "Use OpenAI or other embedding services."
        )

    async def stream_generate(  # type: ignore[override]
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
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
        self._ensure_initialized()

        # 메시지 구성
        messages = [{"role": "user", "content": prompt}]

        # 시스템 프롬프트
        system_prompt = None
        if context:
            system_prompt = self._format_context(context)

        # 생성 파라미터
        params = self._build_generation_params(**kwargs)

        try:
            # 스트리밍 API 호출
            call_params = {
                "model": self.config.model,
                "messages": messages,
                **params,
            }

            if system_prompt:
                call_params["system"] = system_prompt

            async with self._client.messages.stream(**call_params) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            raise RuntimeError(f"Anthropic streaming failed: {str(e)}")

    def _format_context(self, context: Dict[str, Any]) -> str:
        """컨텍스트를 문자열로 포맷"""
        if isinstance(context, dict):
            parts = []
            for key, value in context.items():
                parts.append(f"{key}: {value}")
            return "\n".join(parts)
        return str(context)

    def _build_generation_params(self, **kwargs: Any) -> Dict[str, Any]:
        """생성 파라미터 구성"""
        params = super()._build_generation_params(**kwargs)

        # max_tokens는 Anthropic에서 필수
        if "max_tokens" not in params or params["max_tokens"] is None:
            params["max_tokens"] = 4096

        return params
