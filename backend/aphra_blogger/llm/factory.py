"""
Factory for creating LLM providers.
"""

from typing import Optional
import os

from .base import LLMProvider, LLMConfig
from .openai_provider import OpenAIProvider
from .huggingface_provider import HuggingFaceProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider
from .fallback_provider import FallbackProvider

# Default fallback chain: best free prose model first, reliable last resort last.
OPENROUTER_PRIMARY_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
OPENROUTER_SECONDARY_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
GEMINI_FALLBACK_MODEL = "gemini-2.5-flash"


def _build_fallback_chain(
    temperature: float, max_tokens: int, **kwargs
) -> Optional[LLMProvider]:
    """Build OpenRouter->OpenRouter->Gemini chain if keys allow, else None.

    Returns None when no OpenRouter key is set, so callers fall back to the
    original single-provider behaviour (zero regression).
    """
    or_key = os.getenv("OPENROUTER_API_KEY")
    gem_key = os.getenv("GEMINI_API_KEY")
    if not or_key:
        return None

    providers: list = []
    labels: list = []
    for model in (OPENROUTER_PRIMARY_MODEL, OPENROUTER_SECONDARY_MODEL):
        try:
            p = OpenRouterProvider(
                LLMConfig(api_key=or_key, model=model, temperature=temperature,
                          max_tokens=max_tokens, **kwargs)
            )
            if p.is_available():
                providers.append(p)
                labels.append(f"openrouter:{model.split('/')[-1]}")
        except Exception:
            pass
    if gem_key:
        try:
            g = GeminiProvider(
                LLMConfig(api_key=gem_key, model=GEMINI_FALLBACK_MODEL,
                          temperature=temperature, max_tokens=max_tokens, **kwargs)
            )
            if g.is_available():
                providers.append(g)
                labels.append("gemini:2.5-flash")
        except Exception:
            pass

    if not providers:
        return None
    return FallbackProvider(providers, labels=labels)


def create_llm_provider(
    provider: str = "auto",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs,
) -> LLMProvider:
    """
    Create an LLM provider instance.

    Args:
        provider: Provider name ("openai", "huggingface", "auto")
                 "auto" will try HuggingFace first, then OpenAI
        api_key: API key for the provider
        model: Model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        **kwargs: Additional provider-specific config

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is invalid or not available
    """
    # Default model based on provider
    if model is None or "/" not in model:
        if provider == "openai":
            model = "gpt-4-turbo-preview"
        elif provider == "huggingface":
            model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
        elif provider == "gemini":
            model = "gemini-2.5-flash"
        else:  # auto
            model = "gpt-4-turbo-preview"  # Will be overridden per provider

    config = LLMConfig(
        api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
    )

    # Auto mode: try fallback chain (OpenRouter->Gemini) first, then Gemini, HF
    if provider == "auto":
        chain = _build_fallback_chain(temperature, max_tokens, **kwargs)
        if chain is not None and chain.is_available():
            return chain

        # Check for Gemini API key
        gemini_key = api_key or os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                gemini_config = LLMConfig(
                    api_key=gemini_key,
                    model="gemini-2.5-flash",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                llm = GeminiProvider(gemini_config)
                if llm.is_available():
                    return llm
            except Exception:
                pass

        # Check for HF token
        hf_token = api_key or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        if hf_token:
            try:
                hf_config = LLMConfig(
                    api_key=hf_token,
                    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                llm = HuggingFaceProvider(hf_config)
                if llm.is_available():
                    return llm
            except Exception:
                pass

        raise ValueError(
            "No LLM provider available (Gemini, HuggingFace). "
            "Set GEMINI_API_KEY or HF_TOKEN environment variable."
        )

    # Specific provider requested
    elif provider == "huggingface":
        llm = HuggingFaceProvider(config)
        if not llm.is_available():
            raise ValueError(
                "HuggingFace provider not available. "
                "Set HF_TOKEN or HUGGINGFACE_TOKEN environment variable."
            )
        return llm

    elif provider == "openai":
        llm = OpenAIProvider(config)
        if not llm.is_available():
            raise ValueError(
                "OpenAI provider not available. Set OPENAI_API_KEY environment variable."
            )
        return llm

    elif provider == "gemini":
        # Prefer the OpenRouter->Gemini fallback chain when an OpenRouter key is
        # present; otherwise use plain Gemini (original behaviour).
        chain = _build_fallback_chain(temperature, max_tokens, **kwargs)
        if chain is not None and chain.is_available():
            return chain
        llm = GeminiProvider(config)
        if not llm.is_available():
            raise ValueError(
                "Gemini provider not available. Set GEMINI_API_KEY environment variable."
            )
        return llm

    else:
        raise ValueError(
            f"Unknown provider: {provider}. Valid options: 'openai', 'huggingface', 'gemini', 'auto'"
        )
