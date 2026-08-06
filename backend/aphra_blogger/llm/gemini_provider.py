"""
Google Gemini Provider — uses google-genai (new SDK).

Migration from deprecated google-generativeai:
  pip install google-genai
"""

from typing import List, Dict, Optional
import os

try:
    from google import genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .base import LLMProvider, LLMConfig, LLMResponse


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini API (new google-genai SDK)."""

    def __init__(self, config: LLMConfig):
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai not installed. Install with: pip install google-genai"
            )

        self.config = config
        self.api_key = config.api_key or os.environ.get("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")

        self.client = genai.Client(api_key=self.api_key)

        # Default model — gemini-2.0-flash is the current stable free-tier model
        self.model_name = config.model or "gemini-2.5-flash"
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens

    def is_available(self) -> bool:
        """Check if the Gemini API key is configured."""
        return bool(self.api_key)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate completion using Gemini."""

        system_parts: list[str] = []
        user_parts: list[str] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_parts.append(content)
            else:
                user_parts.append(content)

        # Build prompt: prepend system context to user message
        combined = "\n\n".join(system_parts + user_parts)

        config = genai_types.GenerateContentConfig(
            temperature=temperature if temperature is not None else self.temperature,
            max_output_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            # Disable thinking mode — consumes tokens before text in 2.5-flash.
            # Enable only for complex reasoning tasks if needed.
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=combined,
                config=config,
            )

            text = ""
            # gemini-2.5-flash uses thinking mode — .text may be empty if
            # the response is structured in candidates/parts
            try:
                text = response.text or ""
            except Exception:
                pass
            if not text and hasattr(response, "candidates"):
                for cand in response.candidates or []:
                    for part in getattr(getattr(cand, "content", None), "parts", None) or []:
                        if hasattr(part, "text") and part.text:
                            text += part.text
            return LLMResponse(
                content=text,
                model=self.model_name,
                provider="gemini",
                finish_reason="stop",
                usage=None,
            )

        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

    def create_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """Create message list for Gemini."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def get_model_name(self) -> str:
        return self.model_name
