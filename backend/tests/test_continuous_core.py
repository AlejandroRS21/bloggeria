"""Unit tests for backend core: TopicSelector, DraftValidator, and SafetyAgent."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

from src.orchestrator.continuous.topic_selector import TopicSelector, TopicCandidate
from src.orchestrator.continuous.validation import DraftValidator
from src.orchestrator.safety import SafetyAgent
from src.orchestrator.config import OrchestratorConfig


class TestOrchestratorConfigTomlAndQwen:
    """Test suite for TOML config parsing and Qwen default overrides."""

    def test_default_config_qwen_defaults(self):
        config = OrchestratorConfig.default()
        assert config.default_model == "Qwen/Qwen2.5-72B-Instruct"

    def test_from_toml_parsing(self, tmp_path):
        toml_content = """
[models]
provider = "huggingface"
default_model = "Qwen/Qwen2.5-72B-Instruct"

[workflow]
enable_critic = false
max_iterations = 4
verbose = false

[content]
min_word_count = 500
max_word_count = 1500
"""
        config_file = tmp_path / "test_config.toml"
        config_file.write_text(toml_content)

        config = OrchestratorConfig.from_toml(str(config_file))

        assert config.provider == "huggingface"
        assert config.default_model == "Qwen/Qwen2.5-72B-Instruct"
        assert config.enable_critique is False
        assert config.max_critique_iterations == 4
        assert config.verbose is False
        assert config.min_word_count == 500
        assert config.max_word_count == 1500

    def test_from_toml_fallback_defaults(self, tmp_path):
        toml_content = """
[models]
"""
        config_file = tmp_path / "empty_config.toml"
        config_file.write_text(toml_content)

        config = OrchestratorConfig.from_toml(str(config_file))

        assert config.default_model == "Qwen/Qwen2.5-72B-Instruct"
        assert config.enable_critique is True
        assert config.min_word_count == 800


class TestTopicSelector:
    """Tests for TopicSelector."""

    def test_select_empty_candidates_returns_none(self):
        selector = TopicSelector()
        assert selector.select([]) is None

    def test_select_scores_recency_and_diversity(self):
        selector = TopicSelector(recency_window_hours=24)
        now = datetime.now(timezone.utc)
        recent_candidate = TopicCandidate(
            title="AI News",
            category="AI",
            source="tech",
            published_at=now - timedelta(hours=2),
        )
        old_candidate = TopicCandidate(
            title="Old Tech",
            category="Legacy",
            source="tech",
            published_at=now - timedelta(hours=20),
        )
        selected = selector.select([old_candidate, recent_candidate])
        assert selected is not None
        assert selected.title == "AI News"


class TestDraftValidator:
    """Tests for DraftValidator."""

    def test_validate_minimum_fields_empty(self):
        validator = DraftValidator()
        assert not validator.validate_minimum_fields("", "excerpt", "body", "2026-08-08")
        assert not validator.validate_minimum_fields("title", "", "body", "2026-08-08")
        assert not validator.validate_minimum_fields("title", "excerpt", "", "2026-08-08")
        assert not validator.validate_minimum_fields("title", "excerpt", "body", "   ")

    def test_validate_minimum_fields_valid(self):
        validator = DraftValidator()
        assert validator.validate_minimum_fields("Title", "Excerpt", "Body content", "2026-08-08T00:00:00Z")

    def test_is_redundant(self):
        validator = DraftValidator(redundancy_threshold=0.8)
        existing = ["This is a blog post about artificial intelligence in 2026."]
        assert validator.is_redundant("This is a blog post about artificial intelligence in 2026.", existing)
        assert not validator.is_redundant("Completely different post topic about cooking.", existing)


class TestSafetyAgent:
    """Tests for SafetyAgent."""

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_validate_topic_safe_json(self, mock_create):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"safe": true, "reason": "OK"}'
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="test-key", provider="huggingface")
        res = agent.validate_topic("Inteligencia Artificial en Medicina")
        assert res["safe"] is True
        assert res["reason"] == "OK"

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_validate_topic_unsafe_json(self, mock_create):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"safe": false, "reason": "Contenido inapropiado"}'
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="test-key", provider="huggingface")
        res = agent.validate_topic("Tema prohibido")
        assert res["safe"] is False
        assert res["reason"] == "Contenido inapropiado"

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_validate_topic_exception_fails_safe(self, mock_create):
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = Exception("API error")
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="test-key", provider="huggingface")
        res = agent.validate_topic("Cualquier tema")
        assert res["safe"] is False
        assert "Error técnico" in res["reason"]
