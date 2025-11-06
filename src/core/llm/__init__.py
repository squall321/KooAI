"""
LLM Integration Module

Provides LLM clients, prompt templates, and chains.
"""

from .clients import (
    ILLMClient,
    BaseLLMClient,
    LLMConfig,
    LLMResponse,
    Message,
    MessageRole,
    TokenUsage,
    LLMClientFactory,
)
from .clients.base import LLMProvider
from .prompts import PromptTemplate, PromptTemplateManager, FewShotExampleManager, Example
from .chains import SummaryChain, ComparisonChain, InsightChain, SequentialChain, ChainResult


def _register_clients():
    """Register LLM clients to factory"""
    # OpenAI
    try:
        from .clients.openai_client import OpenAIClient
        LLMClientFactory.register(LLMProvider.OPENAI, OpenAIClient)
    except ImportError:
        pass

    # Anthropic
    try:
        from .clients.anthropic_client import AnthropicClient
        LLMClientFactory.register(LLMProvider.ANTHROPIC, AnthropicClient)
    except ImportError:
        pass

    # Local
    try:
        from .clients.local_client import LocalLLMClient
        LLMClientFactory.register(LLMProvider.LOCAL, LocalLLMClient)
    except ImportError:
        pass


# Auto-register clients on module import
_register_clients()


__all__ = [
    # Clients
    "ILLMClient",
    "BaseLLMClient",
    "LLMConfig",
    "LLMResponse",
    "Message",
    "MessageRole",
    "TokenUsage",
    "LLMProvider",
    "LLMClientFactory",
    # Prompts
    "PromptTemplate",
    "PromptTemplateManager",
    "FewShotExampleManager",
    "Example",
    # Chains
    "SummaryChain",
    "ComparisonChain",
    "InsightChain",
    "SequentialChain",
    "ChainResult",
]
