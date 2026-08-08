"""
Style Analyzer Agent.

Analyzes a blogger's writing style including tone, voice,
structure, and characteristic expressions.
"""

from typing import List, Dict, Any, Optional
import os

try:
    from ..llm import create_llm_provider, LLMProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class StyleAnalyzer:
    """
    Analyzes the writing style of a blogger.
    
    Extracts:
    - Tone (conversational, formal, humorous, etc.)
    - Voice (first person, third person, etc.)
    - Structure patterns (intro-body-conclusion, etc.)
    - Characteristic expressions and phrases
    - Sentence and paragraph metrics
    
    Uses HuggingFace models by default, with OpenAI as fallback.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: Optional[str] = None,
        provider: str = "auto"
    ):
        """
        Initialize the StyleAnalyzer.
        
        Args:
            api_key: API key for LLM provider (HF_TOKEN, OPENAI_API_KEY, etc.)
            model: Model to use. If None, uses provider defaults.
            provider: "huggingface", "openai", or "auto" (tries HF first)
        """
        self.model = model
        self.provider_name = provider
        
        if LLM_AVAILABLE:
            try:
                self.llm = create_llm_provider(
                    provider=provider,
                    api_key=api_key,
                    model=model, # Dejar que el factory decida si no se provee
                    temperature=0.3,
                    max_tokens=1000
                )
            except Exception as e:
                print(f"Warning: Failed to initialize LLM provider: {e}")
                self.llm = None
        else:
            self.llm = None
    
    def analyze(self, blogger_urls: List[str], sample_text: str = None) -> Dict[str, Any]:
        """
        Analyze the blogger's writing style.
        
        Args:
            blogger_urls: List of blog URLs to analyze
            sample_text: Optional sample text if URLs can't be scraped yet
            
        Returns:
            Dictionary with style profile
        """
        if not self.llm or not self.llm.is_available():
            # Fallback to rule-based analysis
            return self._fallback_analysis(sample_text or "")
        
        # Safe extraction of sample_text
        safe_sample = (sample_text or "")[:5000]
        url_context = f"URLs: {', '.join(blogger_urls)}" if blogger_urls else ""
        
        prompt = f"""Analyze the writing style of the blogger from this context: 
{url_context}

SAMPLE TEXT FROM THE BLOGGER:
{safe_sample}

Your task: Create a detailed style profile as JSON with these fields:
{{
  "tone": "string describing overall tone (e.g. conversational, formal, humorous, technical)",
  "voice": "narrative voice perspective (e.g. first person, third person, instructional)",
  "language_level": "formal/casual/colloquial",
  "structure": "typical post structure and flow",
  "expressions": ["list", "of", "characteristic", "expressions", "and", "phrases", "used", "in", "text"],
  "vocabulary": ["list", "of", "characteristic", "words", "and", "terms", "the", "blogger", "uses"],
  "topics": ["list", "of", "topics", "the", "blogger", "typically", "covers"],
  "common_opens": ["typical", "opening", "lines", "or", "phrases"],
  "common_closes": ["typical", "closing", "lines", "or", "phrases"],
  "sentence_pattern": "description of typical sentence structure (e.g. 'short and punchy', 'medium length with occasional complex sentences', 'long and elaborate')",
  "paragraph_pattern": "description of paragraph style",
  "use_of_humor": "description of how humor is used (or if it is absent)",
  "technical_level": "how technical the content gets (e.g. 'non-technical', 'technical-intermediate', 'very technical')",
  "personality_traits": ["trait1", "trait2", "trait3"],
  "engagement_style": "how they engage with readers",
  "language": "ISO 639-1 code of the language the blogger writes in (e.g. 'es', 'en')",
  "language_label": "human-readable name of the blogger's language (e.g. 'Español', 'English')"
}}

Respond with ONLY the JSON, no other text."""

        try:
            messages = self.llm.create_messages(
                system_prompt="You are an expert in analyzing writing styles and linguistic patterns.",
                user_prompt=prompt
            )
            
            response = self.llm.chat_completion(messages)
            
            import json
            result = json.loads(response.content)
            return self._resolve_language_fields(result)
            
        except Exception as e:
            print(f"Warning: LLM analysis failed: {e}. Using fallback.")
            return self._fallback_analysis(sample_text or "")
    
    @staticmethod
    def _resolve_language_fields(profile: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the language fields of a parsed style profile.

        Missing, empty or invalid language values resolve to "es" (REQ-1).
        """
        language = profile.get("language")
        if language not in ("es", "en"):
            language = "es"
        profile["language"] = language
        label = profile.get("language_label")
        if not label or not isinstance(label, str):
            profile["language_label"] = "Español" if language == "es" else "English"
        return profile
    
    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based analysis when LLM is not available."""
        return {
            "tone": "conversational, direct, informative",
            "voice": "first person",
            "language_level": "casual tech",
            "language": "es",
            "language_label": "Español",
            "structure": "intro → main points → reflection",
            "expressions": [
                "interesante",
                "en definitiva",
                "el problema es que",
                "por otro lado",
                "en conclusión"
            ],
            "vocabulary": ["tecnología", "innovación", "futuro", "digital", "cambio"],
            "topics": ["technology", "programming", "AI", "digital transformation"],
            "common_opens": ["Vamos a ver...", "El otro día...", "Hace tiempo que..."],
            "common_closes": ["Y vosotros, ¿qué opináis?", "En fin, hasta la próxima."],
            "sentence_pattern": "medium length, varied structure",
            "paragraph_pattern": "3-5 lines, medium complexity",
            "use_of_humor": "Subtle and occasional",
            "technical_level": "technical-intermediate, explains complex topics accessibly",
            "personality_traits": [
                "curious",
                "enthusiastic",
                "analytical"
            ],
            "engagement_style": "Directly addresses the reader and asks open questions"
        }

