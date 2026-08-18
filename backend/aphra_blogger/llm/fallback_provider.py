"""
FallbackProvider — chains multiple LLM providers.

Tries each provider in order. On failure (rate-limit, timeout, empty output,
any exception) it waits with a short backoff and moves to the next one. Only
raises if every provider in the chain fails.

Designed for free-tier upstreams (OpenRouter ':free' models) that return 429
under load, backed by a reliable paid/stable last resort (Gemini).
"""

from typing import List, Dict, Optional
import time

from .base import LLMProvider, LLMResponse, LLMConfig


class FallbackProvider(LLMProvider):
    """Wraps an ordered list of (label, provider) and fails over between them."""

    def __init__(
        self,
        providers: List[LLMProvider],
        labels: Optional[List[str]] = None,
        retries_per_provider: int = 2,
        backoff_seconds: float = 2.0,
    ):
        # Reuse the first provider's config so downstream code that reads
        # `.config` keeps working.
        base_config = providers[0].config if providers else LLMConfig()
        super().__init__(base_config)
        self.providers = providers
        self.labels = labels or [type(p).__name__ for p in providers]
        self.retries_per_provider = retries_per_provider
        self.backoff_seconds = backoff_seconds
        self.last_provider_used: Optional[str] = None

    def is_available(self) -> bool:
        return any(p.is_available() for p in self.providers)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        errors: List[str] = []
        for label, provider in zip(self.labels, self.providers):
            if not provider.is_available():
                errors.append(f"{label}: unavailable")
                continue
            for attempt in range(1, self.retries_per_provider + 1):
                try:
                    resp = provider.chat_completion(messages, temperature, max_tokens)
                    if resp and resp.content and resp.content.strip():
                        self.last_provider_used = label
                        print(f"[Fallback] OK via {label}"
                              + (f" (attempt {attempt})" if attempt > 1 else ""))
                        return resp
                    raise RuntimeError("empty response")
                except Exception as e:
                    msg = str(e)[:160]
                    errors.append(f"{label}#{attempt}: {msg}")
                    print(f"[Fallback] {label} attempt {attempt} failed: {msg}")
                    # backoff before retry / next provider
                    if attempt < self.retries_per_provider:
                        time.sleep(self.backoff_seconds * attempt)
            # move to next provider after exhausting retries
        raise RuntimeError("All providers failed: " + " | ".join(errors))
