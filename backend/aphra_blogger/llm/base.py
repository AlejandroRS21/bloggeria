"""
Base classes for LLM provider abstraction.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    
    api_key: Optional[str] = None
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    
    # HuggingFace specific
    hf_endpoint: Optional[str] = None  # Custom inference endpoint


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    
    content: str
    model: str
    provider: str
    finish_reason: str
    usage: Optional[Dict[str, int]] = None  # tokens used


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Create a chat completion.
        
        Args:
            messages: List of messages with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            LLMResponse with the completion
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available (has API key, etc.)."""
        pass
    
    def create_messages(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> List[Dict[str, str]]:
        """Helper to create standard message format."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Simple text generation from a single prompt.
        
        Args:
            prompt: Text prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text string
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, temperature, max_tokens)
        return response.content
