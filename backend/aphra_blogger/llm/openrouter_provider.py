"""
OpenRouter provider — OpenAI-compatible API gateway.

Gives access to many models (DeepSeek, Qwen, GLM, Nemotron, ...) through a
single key. Free-tier models (slug ending in ':free') are rate-limited, so
this provider is meant to sit behind FallbackProvider.
"""

from typing import List, Dict, Optional
import os

try:
    from openai import OpenAI
    _OPENAI_SDK = True
except ImportError:
    _OPENAI_SDK = False

from .base import LLMProvider, LLMResponse, LLMConfig

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(LLMProvider):
    """OpenRouter (OpenAI-compatible) provider."""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not _OPENAI_SDK:
            raise ImportError("openai package not installed (needed for OpenRouter).")
        api_key = config.api_key or os.getenv("OPENROUTER_API_KEY")
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                base_url=OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": "https://bloggeria-cf0iyl2bv-alejandrors21s-projects.vercel.app",
                    "X-Title": "BloggerIA",
                },
            )
        else:
            self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("OpenRouter client not available. Check OPENROUTER_API_KEY.")

        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=temp,
            max_tokens=tokens,
            timeout=self.config.timeout,
        )
        choice = response.choices[0]
        usage = None
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model or self.config.model,
            provider="openrouter",
            finish_reason=choice.finish_reason or "stop",
            usage=usage,
        )
