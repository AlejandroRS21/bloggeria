"""Tests for language-aware fallback drafts in ContentGenerator.generate_draft.

Covers the exception path: when the LLM raises during draft generation, the
fallback must honor the resolved language instead of defaulting to Spanish.
"""

from aphra_blogger.agents.content_generator import ContentGenerator


class FailingLLM:
    """LLM stand-in whose chat_completion always raises (is_available -> True)."""

    def is_available(self):
        return True

    def create_messages(self, system_prompt=None, user_prompt=None):
        return {"system": system_prompt, "user": user_prompt}

    def chat_completion(self, messages, temperature=None, max_tokens=None):
        raise RuntimeError("LLM unavailable (simulated failure)")


def _fresh_generator():
    """ContentGenerator with a failing fake LLM wired in (offline-safe)."""
    gen = ContentGenerator(api_key=None)
    gen.llm = FailingLLM()
    return gen


class TestFallbackLanguage:
    """Exception path in generate_draft honors the resolved language."""

    def test_fallback_english_when_explicit_en(self):
        gen = _fresh_generator()
        draft = gen.generate_draft(topic="AI Trends", language="en")
        assert "Exploring the implications of AI Trends" in draft
        assert "Explorando" not in draft

    def test_fallback_spanish_when_explicit_es(self):
        gen = _fresh_generator()
        draft = gen.generate_draft(topic="Tendencias AI", language="es")
        assert "Explorando a fondo las implicaciones de Tendencias AI" in draft

    def test_fallback_english_when_auto_and_profile_en(self):
        gen = _fresh_generator()
        draft = gen.generate_draft(
            topic="AI Trends", language="auto", style_profile={"language": "en"}
        )
        assert "Exploring the implications of AI Trends" in draft
        assert "Explorando" not in draft
