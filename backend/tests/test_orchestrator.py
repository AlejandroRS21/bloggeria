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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
