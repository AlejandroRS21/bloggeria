"""Tests for generation quality fixes: BUG 1a, BUG 1b, BUG 1c."""

import pytest
from aphra_blogger.agents.content_generator import ContentGenerator
from aphra_blogger.agents.html_builder import HTMLBuilder
from src.orchestrator.safety import check_niche_divergence, normalize_niche
from modal_app import _map_to_supabase


class TestBug1aDisplayNameConsistency:
    """BUG 1a: Consistent display names for bloggers across presets, domains, and profile lookup."""

    def test_simon_willison_domain_formatting(self):
        name = ContentGenerator._extract_blogger_name(["https://simonwillison.net"])
        assert name == "Simon Willison"

    def test_dan_luu_domain_formatting(self):
        name = ContentGenerator._extract_blogger_name(["https://danluu.com"])
        assert name == "Dan Luu"

    def test_julia_evans_domain_formatting(self):
        name = ContentGenerator._extract_blogger_name(["https://jvns.ca"])
        assert name == "Julia Evans"

    def test_dan_abramov_domain_formatting(self):
        name = ContentGenerator._extract_blogger_name(["https://overreacted.io"])
        assert name == "Dan Abramov"

    def test_ezra_klein_domain_formatting(self):
        name = ContentGenerator._extract_blogger_name(["https://ezraklein.nytimes.com"])
        assert name == "Ezra Klein"

    def test_map_to_supabase_uses_consistent_name(self):
        result = {
            "workflow_id": "w_test",
            "title": "Post de prueba",
            "blogger_urls": ["https://simonwillison.net"],
            "preset_id": "simon_willison",
            "html_structure": {"metadata": {"slug": "post"}},
        }
        mapped = _map_to_supabase(result)
        assert mapped["style_source"] == "Simon Willison"


class TestBug1bStopwordsExtraction:
    """BUG 1b: Filtering ES+EN stopwords from extracted tags/keywords."""

    def test_filters_long_spanish_and_english_stopwords(self):
        builder = HTMLBuilder(api_key=None)
        content = (
            "cuando donde parece hasta estos about might these often "
            "python javascript typescript desarrollo backend frontend"
        )
        keywords = builder._extract_keywords_for_meta(content, language="es")
        # None of the long stopwords should be present in the top extracted keywords
        stop_list = {"cuando", "donde", "parece", "hasta", "estos", "about", "might", "these", "often"}
        assert not any(sw in keywords for sw in stop_list)
        # Meaningful tech terms should be captured
        assert any(term in keywords for term in ["python", "javascript", "typescript", "desarrollo", "backend", "frontend"])

    def test_prefers_style_profile_topics_or_keywords(self):
        builder = HTMLBuilder(api_key=None)
        profile = {
            "topics": ["AI and LLMs", "Datasette", "Python"],
            "keywords": ["LLM", "Prompt Engineering"],
        }
        content = "cuando donde parece hasta estos sobre entre"
        keywords = builder._extract_keywords_for_meta(content, style_profile=profile, language="es")
        assert "LLM" in keywords or "AI and LLMs" in keywords


class TestBug1cNicheMismatchDetection:
    """BUG 1c: Niche resolution from URL/preset and topic divergence warning."""

    def test_detects_food_topic_on_tech_blogger(self):
        profile = {"niche": "technology", "alias": "Simon Willison"}
        warning = check_niche_divergence("pumpkin puree healthy breakfast recipe", profile)
        assert warning is not None
        assert "food/cooking" in warning or "tech" in warning

    def test_no_warning_when_niche_matches(self):
        profile = {"niche": "technology", "alias": "Simon Willison"}
        warning = check_niche_divergence("Python LLM and prompt engineering", profile)
        assert warning is None

    def test_niche_normalization_handles_aliases(self):
        assert normalize_niche("comida") == "food"
        assert normalize_niche("tecnologia") == "tech"
        assert normalize_niche("salsa_rosa") == "gossip"
