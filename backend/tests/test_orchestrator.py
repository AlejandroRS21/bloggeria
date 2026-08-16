"""Tests for the Blogger Orchestrator."""

import pytest
import json
from pathlib import Path
from src.orchestrator.main import BloggerOrchestrator
from src.orchestrator.config import OrchestratorConfig
from src.orchestrator.state import StateManager, WorkflowState, PhaseStatus


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig."""
    
    def test_default_config(self):
        """Test default configuration creation."""
        config = OrchestratorConfig.default()
        assert config.default_model == "Qwen/Qwen2.5-72B-Instruct"
        assert config.max_retries == 3
        assert config.verbose == True
    
    def test_config_validation_missing_keys(self):
        """Test validation fails without API keys."""
        config = OrchestratorConfig(
            openai_api_key=None,
            gemini_api_key=None
        )
        with pytest.raises(ValueError, match="At least one API key"):
            config.validate()
    
    def test_config_validation_invalid_retries(self):
        """Test validation fails with negative retries."""
        config = OrchestratorConfig(
            openai_api_key="test-key",
            max_retries=-1
        )
        with pytest.raises(ValueError, match="max_retries"):
            config.validate()
    
    def test_config_to_dict(self):
        """Test config serialization."""
        config = OrchestratorConfig.default()
        data = config.to_dict()
        assert isinstance(data, dict)
        assert 'default_model' in data
        assert 'max_retries' in data


class TestWorklowState:
    """Tests for WorkflowState."""
    
    def test_state_initialization(self):
        """Test state initialization."""
        state = WorkflowState(
            workflow_id="test-123",
            topic="Test Topic",
            blogger_urls=["https://example.com"]
        )
        assert state.workflow_id == "test-123"
        assert state.topic == "Test Topic"
        assert len(state.blogger_urls) == 1
        assert len(state.errors) == 0
    
    def test_state_to_dict(self):
        """Test state serialization."""
        state = WorkflowState(
            workflow_id="test-123",
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        data = state.to_dict()
        assert isinstance(data, dict)
        assert data['workflow_id'] == "test-123"
        assert data['topic'] == "Test"
    
    def test_state_to_json(self):
        """Test JSON serialization."""
        state = WorkflowState(
            workflow_id="test-123",
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        json_str = state.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data['workflow_id'] == "test-123"


class TestStateManager:
    """Tests for StateManager."""
    
    def test_start_phase(self):
        """Test starting a phase."""
        state = WorkflowState(
            workflow_id="test",
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        manager = StateManager(state)
        
        manager.start_phase("test_phase", "TestAgent")
        assert "test_phase" in state.phases
        assert state.phases["test_phase"].status == PhaseStatus.RUNNING
        assert state.current_phase == "test_phase"
    
    def test_complete_phase(self):
        """Test completing a phase."""
        state = WorkflowState(
            workflow_id="test",
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        manager = StateManager(state)
        
        manager.start_phase("test_phase")
        manager.complete_phase("test_phase", output="result")
        
        assert state.phases["test_phase"].status == PhaseStatus.COMPLETED
        assert state.phases["test_phase"].output == "result"
        assert state.phases["test_phase"].duration is not None
    
    def test_fail_phase(self):
        """Test failing a phase."""
        state = WorkflowState(
            workflow_id="test",
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        manager = StateManager(state)
        
        manager.start_phase("test_phase")
        manager.fail_phase("test_phase", "Test error")
        
        assert state.phases["test_phase"].status == PhaseStatus.FAILED
        assert state.phases["test_phase"].error == "Test error"
        assert len(state.errors) == 1
    
    def test_skip_phase(self):
        """Test skipping a phase."""
        state = WorkflowState(
            workflow_id="test",
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        manager = StateManager(state)
        
        manager.skip_phase("test_phase", "Not needed")
        
        assert state.phases["test_phase"].status == PhaseStatus.SKIPPED
        assert len(state.warnings) == 1
    
    def test_get_summary(self):
        """Test getting execution summary."""
        state = WorkflowState(
            workflow_id="test",
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        manager = StateManager(state)
        
        manager.start_phase("phase1")
        manager.complete_phase("phase1")
        manager.start_phase("phase2")
        manager.fail_phase("phase2", "error")
        
        summary = manager.get_summary()
        assert summary['phases_completed'] == 1
        assert summary['phases_failed'] == 1
        assert summary['total_phases'] == 2


class TestBloggerOrchestrator:
    """Tests for BloggerOrchestrator."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return OrchestratorConfig(
            openai_api_key="test-key",
            max_retries=1,
            verbose=False,
            enable_critique=False,
        )
    
    def test_orchestrator_initialization(self, config):
        """Test orchestrator initialization."""
        orchestrator = BloggerOrchestrator(config=config, verbose=False)
        assert orchestrator.config == config
    
    def test_orchestrator_run_basic(self, config):
        """Test basic orchestrator execution."""
        orchestrator = BloggerOrchestrator(config=config, verbose=False)
        
        result = orchestrator.run(
            topic="Test Topic",
            blogger_urls=["https://example.com"]
        )
        
        assert isinstance(result, dict)
        assert result['topic'] == "Test Topic"
        assert 'content' in result
        assert 'keywords' in result
        assert 'style_profile' in result
        assert 'image_prompts' in result
    
    def test_orchestrator_with_output_file(self, config, tmp_path):
        """Test orchestrator with output file."""
        orchestrator = BloggerOrchestrator(config=config, verbose=False)
        output_file = tmp_path / "test_output.json"
        
        result = orchestrator.run(
            topic="Test",
            blogger_urls=["https://example.com"],
            output_path=str(output_file)
        )
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data['workflow_id'] == result['workflow_id']
    
    def test_orchestrator_get_state(self, config):
        """Test getting orchestrator state."""
        orchestrator = BloggerOrchestrator(config=config, verbose=False)
        
        # Before running
        assert orchestrator.get_state() is None
        
        # After running
        orchestrator.run(
            topic="Test",
            blogger_urls=["https://example.com"]
        )
        state = orchestrator.get_state()
        assert state is not None
        assert state.topic == "Test"


class TestPhaseRefinement:
    """Refinement phase: resolved language passed through, stale `keywords=` kwarg dropped."""

    @pytest.fixture
    def critique_config(self):
        return OrchestratorConfig(
            openai_api_key="test-key",
            max_retries=1,
            verbose=False,
            enable_critique=True,
        )

    @pytest.fixture
    def offline(self, monkeypatch):
        """Keep the pipeline offline/deterministic."""

        class Resp:
            status_code = 400
            text = ""

        monkeypatch.setattr("src.orchestrator.main.requests.get", lambda *a, **k: Resp())
        monkeypatch.setattr(
            "src.orchestrator.main.research_topic_online",
            lambda *a, **k: {
                "context": "Research synthesis.",
                "articles": [],
                "key_findings": [],
                "research_synthesis": "Synth.",
                "scrape_stats": {},
            },
        )

    def _critique_config_orchestrator(self, orch):
        orch.style_analyzer.analyze = lambda blogger_urls, sample_text=None: {
            "language": "en",
            "tone": "conversational",
        }
        orch.critic.critique = lambda content, style_profile=None, topic=None: {
            "needs_revision": True,
            "coherence_score": 8,
            "style_match": 7,
            "suggestions": ["Shorten the intro"],
        }
        return orch

    def test_refinement_passes_resolved_language_and_drops_keywords(self, critique_config, offline):
        orch = self._critique_config_orchestrator(
            BloggerOrchestrator(config=critique_config, verbose=False)
        )
        captured = {}

        def fake_refine_content(**kwargs):
            captured["kwargs"] = kwargs
            return "# Refined\n\n" + "Contenido refinado en inglés. " * 20

        orch.content_generator.refine_content = fake_refine_content
        orch.run(topic="Test", blogger_urls=["https://example.com"], language="en")

        assert captured["kwargs"]["language"] == "en"
        assert "keywords" not in captured["kwargs"]

    def test_refinement_auto_resolves_language_from_profile(self, critique_config, offline):
        orch = BloggerOrchestrator(config=critique_config, verbose=False)
        orch.style_analyzer.analyze = lambda blogger_urls, sample_text=None: {
            "language": "es",
            "tone": "conversational",
        }
        orch.critic.critique = lambda content, style_profile=None, topic=None: {
            "needs_revision": True,
            "coherence_score": 8,
            "style_match": 7,
            "suggestions": ["Mejora la intro"],
        }
        captured = {}
        orch.content_generator.refine_content = lambda **kwargs: (
            captured.update(kwargs) or "# Refinado\n\n" + "Contenido refinado en español. " * 20
        )
        orch.run(topic="Test", blogger_urls=["https://example.com"], language="auto")

        assert captured["language"] == "es"
        assert "keywords" not in captured


class TestStyleAnalysisPrebakedShortCircuit:
    """REQ-BE-LOADER: registered presets skip scraping and StyleAnalyzer."""

    @pytest.fixture
    def preset_config(self):
        return OrchestratorConfig(
            openai_api_key="test-key",
            max_retries=1,
            verbose=False,
            enable_critique=False,
        )

    def test_style_analysis_uses_prebaked_profile_without_network(self, preset_config, monkeypatch):
        """Preset URL -> pre-baked profile; requests.get and analyze never called."""
        orch = BloggerOrchestrator(config=preset_config, verbose=False)
        state = WorkflowState(
            workflow_id="preset-test",
            topic="Receta de paella",
            blogger_urls=["https://elcomidista.elpais.com"],
        )
        orch.state_manager = StateManager(state)

        def boom(*args, **kwargs):
            raise AssertionError("network/analyzer must not run for registered preset URLs")

        monkeypatch.setattr("src.orchestrator.main.requests.get", boom)
        monkeypatch.setattr(orch.style_analyzer, "analyze", boom)

        orch._phase_style_analysis(["https://elcomidista.elpais.com"])

        assert state.style_profile is not None
        assert state.style_profile["alias"] == "El Comidista"
        assert state.style_profile["language"] == "es"
        assert state.phases["style_analysis"].status == PhaseStatus.COMPLETED

    def test_style_analysis_preset_by_id(self, preset_config, monkeypatch):
        """Preset passed as plain ID also resolves to pre-baked profile."""
        orch = BloggerOrchestrator(config=preset_config, verbose=False)
        state = WorkflowState(
            workflow_id="preset-id",
            topic="Inteligencia artificial",
            blogger_urls=["javipas"],
        )
        orch.state_manager = StateManager(state)

        def boom(*args, **kwargs):
            raise AssertionError("network/analyzer must not run for registered preset IDs")

        monkeypatch.setattr("src.orchestrator.main.requests.get", boom)
        monkeypatch.setattr(orch.style_analyzer, "analyze", boom)

        orch._phase_style_analysis(["javipas"])

        assert state.style_profile["alias"] == "JaviPas"
        assert state.style_profile["language"] == "es"
        assert state.phases["style_analysis"].status == PhaseStatus.COMPLETED

    def test_style_analysis_custom_url_keeps_live_scrape_fallback(self, preset_config, monkeypatch):
        """Spec Scenario 4: unregistered URLs still reach the scraper path."""
        orch = BloggerOrchestrator(config=preset_config, verbose=False)
        state = WorkflowState(
            workflow_id="custom-url",
            topic="Tema cualquiera",
            blogger_urls=["https://example.com"],
        )
        orch.state_manager = StateManager(state)

        scraped = {"calls": 0}

        class Resp:
            status_code = 200
            text = "<html><p>Un párrafo suficientemente largo para pasar el filtro.</p></html>"

        def fake_get(*args, **kwargs):
            scraped["calls"] += 1
            return Resp()

        monkeypatch.setattr("src.orchestrator.main.requests.get", fake_get)
        orch.style_analyzer.analyze = lambda blogger_urls, sample_text=None: {
            "alias": "Custom",
            "language": "es",
        }

        orch._phase_style_analysis(["https://example.com"])

        assert scraped["calls"] > 0, "custom URL must still hit the live scrape path"
        assert state.style_profile["alias"] == "Custom"
        assert state.phases["style_analysis"].status == PhaseStatus.COMPLETED

    def test_style_analysis_with_explicit_preset_id(self, preset_config, monkeypatch):
        """Explicit preset_id param resolves pre-baked profile without network."""
        orch = BloggerOrchestrator(config=preset_config, verbose=False)
        state = WorkflowState(
            workflow_id="preset-id-explicit",
            topic="Analítica electoral",
            blogger_urls=["https://elpais.com/opinion/analytics/"],
        )
        orch.state_manager = StateManager(state)

        def boom(*args, **kwargs):
            raise AssertionError("network/analyzer must not run when preset_id is valid")

        monkeypatch.setattr("src.orchestrator.main.requests.get", boom)
        monkeypatch.setattr(orch.style_analyzer, "analyze", boom)

        orch._phase_style_analysis(["https://elpais.com/opinion/analytics/"], preset_id="kiko-llaneras")

        assert state.style_profile["alias"] == "Kiko Llaneras"
        assert state.phases["style_analysis"].status == PhaseStatus.COMPLETED

    def test_style_analysis_preset_id_with_custom_url(self, preset_config, monkeypatch):
        """Preset ID combined with extra custom URL uses preset pre-baked profile, skipping live scrape."""
        orch = BloggerOrchestrator(config=preset_config, verbose=False)
        state = WorkflowState(
            workflow_id="preset-plus-custom",
            topic="Política y datos",
            blogger_urls=["https://elpais.com/opinion/analytics/", "https://custom-unregistered-blog.com"],
        )
        orch.state_manager = StateManager(state)

        def boom(*args, **kwargs):
            raise AssertionError("network/analyzer must not run when preset_id is valid, even with extra custom URLs")

        monkeypatch.setattr("src.orchestrator.main.requests.get", boom)
        monkeypatch.setattr(orch.style_analyzer, "analyze", boom)

        orch._phase_style_analysis(
            ["https://elpais.com/opinion/analytics/", "https://custom-unregistered-blog.com"],
            preset_id="kiko-llaneras",
        )

        assert state.style_profile["alias"] == "Kiko Llaneras"
        assert state.phases["style_analysis"].status == PhaseStatus.COMPLETED

    @pytest.mark.parametrize("preset_id, url", [
        ("kiko-llaneras", "https://elpais.com/opinion/analytics/"),
        ("ezra-klein", "https://www.nytimes.com/column/ezra-klein"),
    ])
    def test_kiko_and_ezra_resolve_by_url_without_network(self, preset_config, monkeypatch, preset_id, url):
        """Kiko Llaneras and Ezra Klein full section URLs resolve pre-baked without network."""
        orch = BloggerOrchestrator(config=preset_config, verbose=False)
        state = WorkflowState(
            workflow_id=f"url-resolve-{preset_id}",
            topic="Opinión",
            blogger_urls=[url],
        )
        orch.state_manager = StateManager(state)

        def boom(*args, **kwargs):
            raise AssertionError(f"network/analyzer must not run for preset URL {url}")

        monkeypatch.setattr("src.orchestrator.main.requests.get", boom)
        monkeypatch.setattr(orch.style_analyzer, "analyze", boom)

        orch._phase_style_analysis([url])

        assert state.style_profile is not None
        assert state.phases["style_analysis"].status == PhaseStatus.COMPLETED


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
