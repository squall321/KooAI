"""
Local LLM 클라이언트

로컬 LLM 서버를 위한 클라이언트 구현.
Ollama, llama.cpp, vLLM 등 OpenAI 호환 API를 지원.
"""

from typing import Any, AsyncIterator, Dict, List, Optional

import numpy as np
import httpx

from .base import (
    BaseLLMClient,
    LLMResponse,
    Message,
    TokenUsage,
)


class LocalLLMClient(BaseLLMClient):
    """
    로컬 LLM 클라이언트

    OpenAI 호환 API를 제공하는 로컬 서버 지원:
    - Ollama
    - llama.cpp server
    - vLLM
    - LocalAI
    """

    async def initialize(self) -> None:
        """로컬 LLM 클라이언트 초기화"""
        # API 베이스 URL 확인
        if not self.config.api_base:
            raise ValueError("Local LLM requires api_base URL (e.g., http://localhost:11434)")

        # HTTP 클라이언트 생성
        self._client = httpx.AsyncClient(
            base_url=self.config.api_base,
            timeout=self.config.timeout,
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
            context: 추가 컨텍스트
            **kwargs: 추가 파라미터

        Returns:
            LLMResponse: 생성 결과
        """
        self._ensure_initialized()

        # 메시지 구성
        messages = []
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

        # 생성 파라미터
        params = self._build_generation_params(**kwargs)

        # 메시지 변환
        formatted_messages = [msg.to_dict() for msg in messages]

        # API 요청 데이터
        request_data = {
            "model": self.config.model,
            "messages": formatted_messages,
            **params,
        }

        try:
            # POST 요청
            response = await self._client.post(
                "/v1/chat/completions",
                json=request_data,
            )
            response.raise_for_status()

            data = response.json()

            # 응답 파싱
            choice = data["choices"][0]
            content = choice["message"]["content"]

            # 토큰 사용량 (있으면)
            usage = None
            if "usage" in data:
                usage_data = data["usage"]
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )

            return LLMResponse(
                content=content,
                model=data.get("model", self.config.model),
                finish_reason=choice.get("finish_reason"),
                token_usage=usage,
                metadata={
                    "id": data.get("id"),
                    "created": data.get("created"),
                },
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Local LLM API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Local LLM API call failed: {str(e)}")

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

        # 임베딩 모델 (설정 또는 kwargs에서)
        embedding_model = kwargs.get(
            "embedding_model", self.config.extra_params.get("embedding_model")
        )

        if not embedding_model:
            raise ValueError(
                "Embedding model not specified. "
                "Set embedding_model in config.extra_params or pass as kwarg."
            )

        try:
            # API 요청
            response = await self._client.post(
                "/v1/embeddings",
                json={
                    "model": embedding_model,
                    "input": text,
                },
            )
            response.raise_for_status()

            data = response.json()

            # 임베딩 추출
            embedding = data["data"][0]["embedding"]

            return np.array(embedding)

        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Local LLM embedding error: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            raise RuntimeError(f"Local LLM embedding failed: {str(e)}")

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

        # 파라미터
        params = self._build_generation_params(**kwargs)
        formatted_messages = [msg.to_dict() for msg in messages]

        request_data = {
            "model": self.config.model,
            "messages": formatted_messages,
            "stream": True,
            **params,
        }

        try:
            # 스트리밍 요청
            async with self._client.stream(
                "POST",
                "/v1/chat/completions",
                json=request_data,
            ) as response:
                response.raise_for_status()

                # SSE 스트림 파싱
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # "data: " 제거

                        if data_str == "[DONE]":
                            break

                        try:
                            import json

                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"]

                            if "content" in delta:
                                yield delta["content"]

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Local LLM streaming error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Local LLM streaming failed: {str(e)}")

    async def close(self) -> None:
        """클라이언트 종료"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self._is_initialized = False

    def _format_context(self, context: Dict[str, Any]) -> str:
        """컨텍스트를 문자열로 포맷"""
        if isinstance(context, dict):
            parts = []
            for key, value in context.items():
                parts.append(f"{key}: {value}")
            return "\n".join(parts)
        return str(context)
