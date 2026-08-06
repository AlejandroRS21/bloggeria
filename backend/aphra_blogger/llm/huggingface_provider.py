"""
HuggingFace provider implementation.

Supports both HuggingFace Inference API and custom inference endpoints.
"""

from typing import List, Dict, Optional
import os
import json

try:
    from huggingface_hub import InferenceClient
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

from .base import LLMProvider, LLMResponse, LLMConfig


class HuggingFaceProvider(LLMProvider):
    """HuggingFace Inference API provider."""
    
    # Default models for different tasks
    DEFAULT_MODELS = {
        "chat": "meta-llama/Meta-Llama-3.1-8B-Instruct",  # Fast and good quality
        "analysis": "mistralai/Mistral-7B-Instruct-v0.2",  # Good for analysis
        "generation": "meta-llama/Meta-Llama-3.1-70B-Instruct",  # Best quality
    }
    
    def __init__(self, config: LLMConfig):
        """Initialize HuggingFace provider."""
        super().__init__(config)
        
        if not HF_AVAILABLE:
            raise ImportError(
                "huggingface_hub package not installed. "
                "Install with: pip install huggingface-hub"
            )
        
        api_key = config.api_key or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        
        if api_key:
            # Use custom endpoint if provided, otherwise use standard API
            if config.hf_endpoint:
                self.client = InferenceClient(model=config.hf_endpoint, token=api_key)
            else:
                # If model not set, use default chat model
                model = config.model if config.model != "gpt-4-turbo-preview" else self.DEFAULT_MODELS["chat"]
                self.client = InferenceClient(model=model, token=api_key)
        else:
            self.client = None
    
    def is_available(self) -> bool:
        """Check if HuggingFace is available."""
        return self.client is not None
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Create chat completion with HuggingFace."""
        if not self.is_available():
            raise RuntimeError("HuggingFace client not available. Check HF_TOKEN.")
        
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        try:
            # Format messages for HF chat completion
            # HF uses a specific format for chat models
            response = self.client.chat_completion(
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )
            
            # Extract content from response
            if hasattr(response, 'choices') and len(response.choices) > 0:
                content = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
            else:
                # Fallback for different response formats
                content = str(response)
                finish_reason = "stop"
            
            return LLMResponse(
                content=content,
                model=self.client.model,
                provider="huggingface",
                finish_reason=finish_reason,
                usage=None,  # HF doesn't always provide token usage
            )
        except Exception as e:
            raise RuntimeError(f"HuggingFace API error: {e}")
