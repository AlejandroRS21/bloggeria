"""
Factory for creating LLM providers.
"""

from typing import Optional
import os

from .base import LLMProvider, LLMConfig
from .openai_provider import OpenAIProvider
from .huggingface_provider import HuggingFaceProvider
from .modal_provider import ModalProvider
from .gemini_provider import GeminiProvider


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
        elif provider == "modal":
            # Default Modal function name
            model = "blogger-agent-models/LlamaModel.generate"
        else:  # auto
            model = "gpt-4-turbo-preview"  # Will be overridden per provider

    config = LLMConfig(
        api_key=api_key, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
    )

    # Auto mode: try Modal first if configured, then Gemini, then HuggingFace, then OpenAI
    if provider == "auto":
        # Check for Modal config
        modal_ready = (
            os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET")
        ) or os.getenv("MODAL_API_KEY")
        if modal_ready:
            try:
                modal_config = LLMConfig(
                    api_key=api_key or os.getenv("MODAL_API_KEY"),
                    model="blogger-agent-models/LlamaModel.generate",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                llm = ModalProvider(modal_config)
                if llm.is_available():
                    return llm
            except Exception:
                pass

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
            "No LLM provider available (Modal, Gemini, HuggingFace). "
            "Set MODAL_TOKEN_ID/SECRET, GEMINI_API_KEY, or HF_TOKEN environment variable."
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

    elif provider == "modal":
        llm = ModalProvider(config)
        if not llm.is_available():
            raise ValueError(
                "Modal provider not available. "
                "Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET environment variables."
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
