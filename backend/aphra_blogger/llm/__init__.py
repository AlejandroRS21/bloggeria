"""
LLM provider abstraction module.

Supports multiple LLM providers: OpenAI, HuggingFace, Anthropic.
"""

from .base import LLMProvider, LLMResponse, LLMConfig
from .factory import create_llm_provider
from .openrouter_provider import OpenRouterProvider
from .fallback_provider import FallbackProvider

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMConfig",
    "create_llm_provider",
    "OpenRouterProvider",
    "FallbackProvider",
]
