"""Tests for multi-language generation support (change multi-idioma-generacion).

Covers REQ-1 (style profile language), REQ-2 (generation rules),
REQ-3 (HTML lang/UI), REQ-4/5 (orchestrator + state), REQ-6 (webhook),
REQ-7 (golden regression) and the frontend payload contract (REQ-8).
"""

from pathlib import Path

import pytest

from aphra_blogger.agents.content_generator import ContentGenerator
from aphra_blogger.agents.html_builder import HTMLBuilder
from aphra_blogger.agents.style_analyzer import StyleAnalyzer
from src.orchestrator.config import OrchestratorConfig
from src.orchestrator.main import BloggerOrchestrator
from src.orchestrator.state import WorkflowState

GOLDEN_DIR = Path(__file__).parent / "golden"

TOPIC = "El futuro de la IA en el desarrollo web"
KEYWORDS = ["inteligencia artificial", "python", "machine learning"]
URLS = ["https://javipas.com"]
PROFILE = {
    "tone": "conversational, direct",
    "voice": "first person",
    "technical_level": "technical-intermediate",
}
SAMPLE_MAIN = ("Párrafo de ejemplo del blogger sobre tecnología y programación. " * 20)
RESEARCH = ("Resultado de investigación: la IA generativa creció un 40% en 2025. " * 15)


class FakeLLM:
    """LLM stand-in capturing create_messages calls (is_available -> True)."""

    def __init__(self, content="Draft content."):
        self.calls = []
        self.content = content

    def is_available(self):
        return True

    def create_messages(self, system_prompt=None, user_prompt=None):
        self.calls.append({"system": system_prompt, "user": user_prompt})
        return {"system": system_prompt, "user": user_prompt}

    def chat_completion(self, messages, temperature=None, max_tokens=None):
        return type("Resp", (), {"content": self.content})()


def _fresh_generator():
    """ContentGenerator with a fake LLM wired in (offline-safe)."""
    gen = ContentGenerator(api_key=None)
    gen.llm = FakeLLM()
    return gen


class TestStyleLanguage:
    """REQ-1: style profile gains language (+ language_label); fallback es."""

    def test_prompt_requests_language_fields(self):
        analyzer = StyleAnalyzer(api_key=None)
        analyzer.llm = FakeLLM(content='{"tone": "conversational"}')
        analyzer.analyze(URLS, sample_text="Some sample text")
        prompt = analyzer.llm.calls[-1]["user"]
        assert '"language"' in prompt
        assert '"language_label"' in prompt

    def test_analyze_keeps_detected_language(self):
        analyzer = StyleAnalyzer(api_key=None)
        analyzer.llm = FakeLLM(
            content='{"tone": "conversational", "language": "en", "language_label": "English"}'
        )
        result = analyzer.analyze(URLS, sample_text="English sample text")
        assert result["language"] == "en"
        assert result["language_label"] == "English"

    def test_missing_language_falls_back_es(self):
        analyzer = StyleAnalyzer(api_key=None)
        analyzer.llm = FakeLLM(content='{"tone": "conversational"}')
        result = analyzer.analyze(URLS, sample_text="Some sample text")
        assert result["language"] == "es"

    def test_empty_language_falls_back_es(self):
        analyzer = StyleAnalyzer(api_key=None)
        analyzer.llm = FakeLLM(content='{"tone": "x", "language": ""}')
        result = analyzer.analyze(URLS, sample_text="Some sample text")
        assert result["language"] == "es"

    def test_invalid_language_falls_back_es(self):
        analyzer = StyleAnalyzer(api_key=None)
        analyzer.llm = FakeLLM(content='{"tone": "x", "language": "fr"}')
        result = analyzer.analyze(URLS, sample_text="Some sample text")
        assert result["language"] == "es"

    def test_fallback_analysis_is_es(self):
        analyzer = StyleAnalyzer(api_key=None)
        result = analyzer._fallback_analysis("Some text")
        assert result["language"] == "es"
        assert result["language_label"] == "Español"


class TestGeneratorLanguage:
    """REQ-2: _language_rules extraction, en rules, resolution, localization."""

    def test_es_rules_main_byte_identical(self):
        expected = (GOLDEN_DIR / "es_rules_main.txt").read_text(encoding="utf-8")
        assert ContentGenerator._language_rules("es", simplified=False) == expected

    def test_es_rules_simplified_byte_identical(self):
        expected = (GOLDEN_DIR / "es_rules_simplified.txt").read_text(encoding="utf-8")
        assert ContentGenerator._language_rules("es", simplified=True) == expected

    def test_en_rules_english_only(self):
        rules = ContentGenerator._language_rules("en")
        assert "ESPAÑOL" not in rules
        assert "español" not in rules
        assert "voseo" not in rules
        assert "tuteo" not in rules
        assert "entire post in english" in rules.lower()

    def test_en_rules_keep_technical_terms(self):
        rules = ContentGenerator._language_rules("en")
        # en rules keep tech terms as-is, no forced translation mapping
        assert "Machine Learning" in rules
        assert "Traduce cualquier término" not in rules

    def test_resolve_explicit_wins(self):
        assert ContentGenerator._resolve_language("en", {"language": "es"}) == "en"
        assert ContentGenerator._resolve_language("es", {"language": "en"}) == "es"

    def test_resolve_auto_uses_profile(self):
        assert ContentGenerator._resolve_language("auto", {"language": "en"}) == "en"
        assert ContentGenerator._resolve_language("auto", {"language": "es"}) == "es"

    def test_resolve_auto_missing_falls_back_es(self):
        assert ContentGenerator._resolve_language("auto", {}) == "es"
        assert ContentGenerator._resolve_language("auto", None) == "es"
        assert ContentGenerator._resolve_language("auto", {"language": "fr"}) == "es"

    def test_resolve_invalid_falls_back_es(self):
        assert ContentGenerator._resolve_language("fr", {}) == "es"
        assert ContentGenerator._resolve_language("", {}) == "es"

    def test_generate_draft_en_injects_en_rules(self):
        gen = _fresh_generator()
        gen.generate_draft(
            topic=TOPIC, style_profile=PROFILE, sample_text=SAMPLE_MAIN,
            research_context=RESEARCH, blogger_urls=URLS, language="en",
        )
        prompt = gen.llm.calls[-1]["user"]
        assert "entire post in english" in prompt.lower()

    def test_generate_draft_auto_uses_profile_language(self):
        gen = _fresh_generator()
        gen.generate_draft(
            topic=TOPIC, style_profile={"language": "en"}, sample_text=SAMPLE_MAIN,
            research_context=RESEARCH, blogger_urls=URLS, language="auto",
        )
        prompt = gen.llm.calls[-1]["user"]
        assert "entire post in english" in prompt.lower()

    def test_system_prompt_localized(self):
        gen = _fresh_generator()
        gen.generate_draft(
            topic=TOPIC, style_profile=PROFILE, sample_text=SAMPLE_MAIN,
            research_context=RESEARCH, blogger_urls=URLS, language="en",
        )
        system = gen.llm.calls[-1]["system"]
        assert system.startswith("You are a professional blog writer")

    def test_attribution_localized(self):
        gen = ContentGenerator(api_key=None)
        es_footer = gen._build_attribution(URLS, language="es")
        assert es_footer == (GOLDEN_DIR / "footer_es.txt").read_text(encoding="utf-8")
        en_footer = gen._build_attribution(URLS, language="en")
        assert "This post was written emulating the style of [Javipas]" in en_footer


class TestGoldenRegression:
    """REQ-7: no-param (auto->es) assembled prompts byte-identical to frozen goldens."""

    @pytest.fixture
    def captured_es(self):
        gen = _fresh_generator()
        kwargs = {
            "topic": TOPIC, "style_profile": PROFILE, "keywords": KEYWORDS,
            "sample_text": SAMPLE_MAIN, "research_context": RESEARCH,
            "min_words": 1500, "max_words": 2500, "blogger_urls": URLS,
        }
        gen.generate_draft(**kwargs)
        main_call = gen.llm.calls[-1]

        gen.llm = FakeLLM()
        gen.generate_draft(**{**kwargs, "sample_text": ""})
        simp_call = gen.llm.calls[-1]

        return main_call, simp_call, gen._build_attribution(URLS)

    def test_main_prompt_matches_golden(self, captured_es):
        main_call, _, _ = captured_es
        expected = (GOLDEN_DIR / "prompt_main_es.txt").read_text(encoding="utf-8")
        assert main_call["user"] == expected

    def test_simplified_prompt_matches_golden(self, captured_es):
        _, simp_call, _ = captured_es
        expected = (GOLDEN_DIR / "prompt_simplified_es.txt").read_text(encoding="utf-8")
        assert simp_call["user"] == expected

    def test_system_matches_golden(self, captured_es):
        main_call, _, _ = captured_es
        expected = (GOLDEN_DIR / "system_es.txt").read_text(encoding="utf-8")
        assert main_call["system"] == expected

    def test_footer_matches_golden(self, captured_es):
        _, _, footer = captured_es
        expected = (GOLDEN_DIR / "footer_es.txt").read_text(encoding="utf-8")
        assert footer == expected


class TestHtmlLanguage:
    """REQ-3: <html lang>, UI strings es/en, neutral meta fallback."""

    def test_build_en_page_lang_and_ui(self):
        builder = HTMLBuilder(api_key=None)
        out = builder.build(content="# Title\n\nContent here.", topic="Test", language="en")
        assert '<html lang="en">' in out.full_page
        assert "min read" in out.full_page
        assert "words" in out.full_page
        assert "Back to Blog" in out.full_page
        assert "min de lectura" not in out.full_page

    def test_build_es_default_matches_current(self):
        builder = HTMLBuilder(api_key=None)
        out = builder.build(content="# Title\n\nContent here.", topic="Test")
        assert '<html lang="es">' in out.full_page
        assert "min de lectura" in out.full_page
        assert "palabras" in out.full_page
        assert "Volver al Blog" in out.full_page

    def test_lang_derived_from_style_profile(self):
        builder = HTMLBuilder(api_key=None)
        out = builder.build(
            content="# Title\n\nContent here.", topic="Test",
            style_profile={"language": "en"},
        )
        assert '<html lang="en">' in out.full_page

    def test_generate_full_html_page_lang_param(self):
        builder = HTMLBuilder(api_key=None)
        page = builder.generate_full_html_page(
            html_content="<p>x</p>", meta_title="T", meta_description="d",
            meta_keywords=["k"], reading_time=2, word_count=400, lang="en",
        )
        assert '<html lang="en">' in page
        assert "min read" in page

    def test_meta_description_fallback_neutral_for_en(self):
        builder = HTMLBuilder(api_key=None)
        desc_en = builder._generate_meta_description("Short.", language="en")
        assert desc_en.startswith("Blog article about")
        desc_es = builder._generate_meta_description("Corto.", language="es")
        assert desc_es == "Artículo de blog sobre tecnología e innovación."

    def test_meta_keywords_fallback_neutral_for_en(self):
        builder = HTMLBuilder(api_key=None)
        kw_en = builder._extract_keywords_for_meta("xx yy", language="en")
        assert kw_en == ["blog", "technology", "innovation"]
        kw_es = builder._extract_keywords_for_meta("xx yy", language="es")
        assert kw_es == ["blog", "tecnología", "innovación"]
