"""
LLM Streaming Support

Server-Sent Events (SSE) for streaming LLM responses.
"""

import json
from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class StreamChunk:
    """Streaming response chunk."""

    content: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_sse(self) -> str:
        """Convert to Server-Sent Event format."""
        data = asdict(self)
        return f"data: {json.dumps(data)}\n\n"


class ConversationContext:
    """
    Conversation context manager.

    Maintains conversation history for context-aware responses.
    """

    def __init__(self, max_turns: int = 10):
        """
        Initialize conversation context.

        Args:
            max_turns: Maximum number of conversation turns to keep
        """
        self.max_turns = max_turns
        self.messages: list[Dict[str, str]] = []

    def add_user_message(self, content: str) -> None:
        """Add user message to context."""
        self.messages.append({"role": "user", "content": content})
        self._trim_history()

    def add_assistant_message(self, content: str) -> None:
        """Add assistant message to context."""
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()

    def _trim_history(self) -> None:
        """Trim history to max_turns."""
        if len(self.messages) > self.max_turns * 2:  # user + assistant = 2 messages per turn
            self.messages = self.messages[-(self.max_turns * 2) :]

    def get_messages(self) -> list[Dict[str, str]]:
        """Get conversation messages."""
        return self.messages.copy()

    def clear(self) -> None:
        """Clear conversation history."""
        self.messages.clear()


class StreamingLLMService:
    """
    Streaming LLM service wrapper.

    Provides unified interface for streaming responses from different LLM providers.
    """

    async def stream_analysis(
        self,
        prompt: str,
        context: Optional[ConversationContext] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream analysis response from LLM.

        Args:
            prompt: User prompt
            context: Optional conversation context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Stream chunks

        Example:
            ```python
            service = StreamingLLMService()
            context = ConversationContext()

            async for chunk in service.stream_analysis(
                prompt="Analyze this simulation data...",
                context=context
            ):
                print(chunk.content, end="", flush=True)
            ```
        """
        # Build messages
        messages = []

        if context:
            messages.extend(context.get_messages())

        messages.append({"role": "user", "content": prompt})

        # Mock streaming response (replace with actual LLM API call)
        # In production, call OpenAI/Anthropic/local LLM API
        response_text = "Based on the simulation data provided, I observe the following key insights:\n\n1. Temperature distribution shows clear stratification\n2. Pressure gradients indicate potential flow separation\n3. Velocity profiles suggest turbulent behavior in region X"

        # Simulate streaming by chunks
        words = response_text.split()
        buffer = ""

        for i, word in enumerate(words):
            buffer += word + " "

            # Yield every few words
            if (i + 1) % 3 == 0 or i == len(words) - 1:
                yield StreamChunk(
                    content=buffer,
                    finish_reason="stop" if i == len(words) - 1 else None,
                    metadata={"token_count": i + 1},
                )
                buffer = ""

        # Add to context if provided
        if context:
            context.add_user_message(prompt)
            context.add_assistant_message(response_text)


class TokenUsageTracker:
    """
    Track token usage and costs.

    Monitors LLM API usage for billing and optimization.
    """

    def __init__(self) -> None:
        """Initialize usage tracker."""
        self.usage_history: list[Dict[str, Any]] = []

    def record_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_usd: Optional[float] = None,
    ) -> None:
        """
        Record token usage.

        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cost_usd: Estimated cost in USD
        """
        self.usage_history.append(
            {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "cost_usd": cost_usd,
            }
        )

    def get_total_tokens(self) -> int:
        """Get total tokens used."""
        return sum(record["total_tokens"] for record in self.usage_history)

    def get_total_cost(self) -> float:
        """Get total cost in USD."""
        return sum(record.get("cost_usd", 0) or 0 for record in self.usage_history)

    def get_usage_by_model(self) -> Dict[str, Dict[str, int]]:
        """Get usage statistics by model."""
        stats: Dict[str, Dict[str, int]] = {}

        for record in self.usage_history:
            model = record["model"]
            if model not in stats:
                stats[model] = {
                    "requests": 0,
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                }

            stats[model]["requests"] += 1
            stats[model]["total_tokens"] += record["total_tokens"]
            stats[model]["prompt_tokens"] += record["prompt_tokens"]
            stats[model]["completion_tokens"] += record["completion_tokens"]

        return stats
