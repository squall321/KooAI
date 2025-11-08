"""
OpenAI 클라이언트

OpenAI API를 사용한 LLM 클라이언트 구현.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

import numpy as np

from .base import (
    BaseLLMClient,
    LLMResponse,
    Message,
    TokenUsage,
)


class OpenAIClient(BaseLLMClient):
    """OpenAI API 클라이언트"""

    async def initialize(self) -> None:
        """OpenAI 클라이언트 초기화"""
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")

        # API 키 설정
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")

        # 비동기 클라이언트 생성
        self._client = openai.AsyncOpenAI(
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
        **kwargs,
    ) -> LLMResponse:
        """
        텍스트 생성

        Args:
            prompt: 프롬프트
            context: 추가 컨텍스트 (system message로 사용)
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 생성 결과
        """
        self._ensure_initialized()

        # 메시지 구성
        messages = []

        # 컨텍스트를 시스템 메시지로 추가
        if context:
            system_content = self._format_context(context)
            messages.append(Message.system(system_content))

        messages.append(Message.user(prompt))

        return await self.chat(messages, **kwargs)

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
        self._ensure_initialized()

        # 생성 파라미터 구성
        params = self._build_generation_params(**kwargs)

        # 메시지를 OpenAI 형식으로 변환
        openai_messages = [msg.to_dict() for msg in messages]

        try:
            # API 호출
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                **params,
            )

            # 응답 파싱
            choice = response.choices[0]
            content = choice.message.content

            # 토큰 사용량
            usage = None
            if response.usage:
                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )

            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=choice.finish_reason,
                token_usage=usage,
                metadata={
                    "id": response.id,
                    "created": response.created,
                },
                raw_response=response,
            )

        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")

    async def embed(self, text: str, **kwargs) -> np.ndarray:
        """
        텍스트 임베딩

        Args:
            text: 임베딩할 텍스트
            **kwargs: 추가 파라미터

        Returns:
            np.ndarray: 임베딩 벡터
        """
        self._ensure_initialized()

        # 임베딩 모델 결정
        embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")

        try:
            # API 호출
            response = await self._client.embeddings.create(
                model=embedding_model,
                input=text,
            )

            # 임베딩 추출
            embedding = response.data[0].embedding

            return np.array(embedding)

        except Exception as e:
            raise RuntimeError(f"OpenAI embedding failed: {str(e)}")

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
        self._ensure_initialized()

        # 메시지 구성
        messages = []
        if context:
            system_content = self._format_context(context)
            messages.append(Message.system(system_content))
        messages.append(Message.user(prompt))

        # 생성 파라미터
        params = self._build_generation_params(**kwargs)
        openai_messages = [msg.to_dict() for msg in messages]

        try:
            # 스트리밍 API 호출
            stream = await self._client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                stream=True,
                **params,
            )

            # 청크 스트리밍
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise RuntimeError(f"OpenAI streaming failed: {str(e)}")

    def _format_context(self, context: Dict[str, Any]) -> str:
        """컨텍스트를 문자열로 포맷"""
        if isinstance(context, dict):
            parts = []
            for key, value in context.items():
                parts.append(f"{key}: {value}")
            return "\n".join(parts)
        return str(context)
