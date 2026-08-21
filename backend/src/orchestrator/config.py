"""
Orchestrator configuration module.

Manages configuration for the blogger orchestrator including
LLM settings, retry policies, and workflow parameters.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
import toml
from pathlib import Path


@dataclass
class OrchestratorConfig:
    """Configuration for the BloggerOrchestrator."""
    
    # LLM Settings
    default_model: str = "Qwen/Qwen2.5-72B-Instruct"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Retry Settings
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    backoff_factor: float = 2.0
    
    # Workflow Settings
    enable_critique: bool = True
    max_critique_iterations: int = 2
    verbose: bool = True
    
    # Content Settings
    min_word_count: int = 800
    max_word_count: int = 2500
    
    # Deep Research Settings
    enable_deep_research: bool = True
    max_research_articles: int = 5
    max_scrape_chars_per_article: int = 5000
    max_research_chars_total: int = 15000
    
    # API Keys (from environment)
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    huggingface_token: Optional[str] = None
    modal_api_key: Optional[str] = None
    
    # Provider Settings
    provider: str = "auto"  # "auto", "huggingface", "openai", "gemini", "modal"
    
    # Timeouts
    agent_timeout: int = 300  # seconds per agent
    
    @classmethod
    def from_toml(cls, config_path: str) -> "OrchestratorConfig":
        """Load configuration from TOML file."""
        with open(config_path, 'r') as f:
            data = toml.load(f)
        
        # Extract relevant sections
        models = data.get('models', {})
        workflow = data.get('workflow', {})
        content = data.get('content', {})
        
        return cls(
            default_model=models.get('default_model', 'Qwen/Qwen2.5-72B-Instruct'),
            temperature=models.get('openai', {}).get('temperature', 0.7),
            max_tokens=models.get('openai', {}).get('max_tokens', 2000),
            enable_critique=workflow.get('enable_critic', True),
            max_critique_iterations=workflow.get('max_iterations', 2),
            verbose=workflow.get('verbose', True),
            min_word_count=content.get('min_word_count', 800),
            max_word_count=content.get('max_word_count', 2500),
            gemini_api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            huggingface_token=os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN'),
            modal_api_key=os.getenv('MODAL_API_KEY'),
            provider=models.get('provider', 'auto'),
        )
    
    @classmethod
    def default(cls) -> "OrchestratorConfig":
        """Create default configuration."""
        return cls(
            gemini_api_key=os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            huggingface_token=os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN'),
            modal_api_key=os.getenv('MODAL_API_KEY'),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        has_key = any([
            self.gemini_api_key,
            self.openai_api_key, 
            self.anthropic_api_key,
            self.huggingface_token, 
            self.modal_api_key,
            os.getenv('MODAL_TOKEN_ID') and os.getenv('MODAL_TOKEN_SECRET')
        ])
        
        if not has_key:
            raise ValueError(
                "At least one API key must be set: GEMINI_API_KEY, OPENAI_API_KEY, HF_TOKEN, or MODAL_TOKEN_ID/SECRET"
            )
        
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        
        if self.min_word_count > self.max_word_count:
            raise ValueError("min_word_count cannot be greater than max_word_count")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'default_model': self.default_model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'max_retries': self.max_retries,
            'enable_critique': self.enable_critique,
            'verbose': self.verbose,
        }
