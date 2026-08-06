"""
Modal provider implementation.

Allows calling LLMs hosted as Modal functions.
"""

from typing import List, Dict, Optional, Any
import os
import json

try:
    import modal
    MODAL_AVAILABLE = True
except ImportError:
    MODAL_AVAILABLE = False

from .base import LLMProvider, LLMResponse, LLMConfig


class ModalProvider(LLMProvider):
    """
    Modal LLM provider.
    
    Calls a model hosted on Modal. The Modal function can be either:
    1. A remote function (using modal.Function.lookup)
    2. A web endpoint (using requests/httpx)
    
    This provider defaults to using modal.Function.lookup for higher performance.
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize Modal provider."""
        super().__init__(config)
        
        if not MODAL_AVAILABLE:
            raise ImportError(
                "modal package not installed. "
                "Install with: pip install modal"
            )
        
        # The 'model' field in config should be the Modal function name,
        # e.g., "my-llama-app/LlamaModel.generate"
        self.function_name = config.model or "blogger-agent-models/LlamaModel.generate"
        self.client = None
        
        # Check if we are already inside a Modal environment
        # or if we have tokens configured
        if os.environ.get("MODAL_TOKEN_ID") and os.environ.get("MODAL_TOKEN_SECRET"):
            self.is_ready = True
        else:
            # Check for generic MODAL_API_KEY if used
            self.is_ready = bool(config.api_key or os.environ.get("MODAL_API_KEY"))

    def is_available(self) -> bool:
        """Check if Modal provider is configured."""
        return self.is_ready

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Create chat completion by calling the Modal class method."""
        if not self.is_available():
            raise RuntimeError("Modal configuration missing. Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET.")

        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        try:
            # function_name format: "app-name/ClassName.method_name"
            # e.g. "blogger-agent-models/LlamaModel.generate"
            if "/" in self.function_name:
                app_name, class_method = self.function_name.split("/", 1)
            else:
                app_name = "blogger-agent-models"
                class_method = self.function_name

            if "." in class_method:
                class_name, method_name = class_method.split(".", 1)
            else:
                class_name = class_method
                method_name = "generate"

            # modal.Cls.from_name is the correct API for class methods
            RemoteCls = modal.Cls.from_name(app_name, class_name)
            instance = RemoteCls()
            method = getattr(instance, method_name)

            response = method.remote(
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )

            if isinstance(response, dict):
                content = response.get("content", str(response))
                model_name = response.get("model", self.function_name)
                finish_reason = response.get("finish_reason", "stop")
                usage = response.get("usage")
            else:
                content = str(response)
                model_name = self.function_name
                finish_reason = "stop"
                usage = None

            return LLMResponse(
                content=content,
                model=model_name,
                provider="modal",
                finish_reason=finish_reason,
                usage=usage,
            )
        except Exception as e:
            raise RuntimeError(f"Modal function error ({self.function_name}): {e}")
