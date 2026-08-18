"""
Critic Agent.

Reviews and critiques generated content for coherence,
style matching, and quality.
"""

from typing import Dict, Any, Optional
import os

try:
    from ..llm import create_llm_provider, LLMProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class CriticAgent:
    """
    Critiques blog content for quality and style matching.
    
    Evaluates:
    - Coherence and flow
    - Style matching with target blogger
    - Content quality
    - Areas for improvement
    
    Uses HuggingFace models by default for cost-effective critique.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "auto"
    ):
        """
        Initialize the CriticAgent.
        
        Args:
            api_key: API key for LLM provider
            model: Model to use. If None, uses high-quality model.
            provider: "huggingface", "openai", or "auto"
        """
        self.model = model
        self.provider_name = provider
        
        if LLM_AVAILABLE:
            try:
                # Factory will handle defaults
                self.llm = create_llm_provider(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    temperature=0.3,
                    max_tokens=1000
                )
            except Exception as e:
                print(f"Warning: Failed to initialize LLM provider: {e}")
                self.llm = None
        else:
            self.llm = None
    
    def critique(
        self,
        content: str,
        style_profile: Dict[str, Any],
        topic: str
    ) -> Dict[str, Any]:
        """
        Critique the generated content.
        
        Args:
            content: Content to critique
            style_profile: Target style profile
            topic: Original topic
            
        Returns:
            Dictionary with critique results
        """
        if not self.llm or not self.llm.is_available():
            return self._fallback_critique(content)
        
        prompt = f"""Critique this blog post as an expert editor.

TOPIC: {topic}

TARGET STYLE PROFILE:
- Tone: {style_profile.get('tone', 'N/A')}
- Voice: {style_profile.get('voice', 'N/A')}
- Structure: {style_profile.get('structure', 'N/A')}
- Key expressions: {', '.join(style_profile.get('expressions', [])[:5])}

CONTENT TO CRITIQUE:
{content}

EVALUATION CRITERIA:
1. Coherence (0-10): Does the post flow logically? Are transitions smooth?
2. Style Match (0-10): Does it match the target blogger's style and voice?
3. Engagement (0-10): Is it engaging and interesting to read?
4. Authenticity (0-10): Does it feel genuine and not forced?

Provide critique as JSON:
{{
  "coherence_score": number,
  "style_match": number,
  "engagement_score": number,
  "authenticity_score": number,
  "overall_score": average,
  "strengths": ["list of 2-3 strong points"],
  "weaknesses": ["list of 2-3 weak points"],
  "suggestions": ["list of 3-5 specific improvements"],
  "needs_revision": boolean (true if overall_score < 7)
}}

Return ONLY valid JSON."""

        try:
            messages = self.llm.create_messages(
                system_prompt="You are an expert blog editor who provides constructive, detailed critiques.",
                user_prompt=prompt
            )
            
            response = self.llm.chat_completion(messages)

            from ..llm.json_utils import extract_json
            result = extract_json(response.content)
            return result

        except Exception as e:
            print(f"Warning: Critique failed: {e}. Using fallback.")
            return self._fallback_critique(content)
    
    def _fallback_critique(self, content: str) -> Dict[str, Any]:
        """Fallback critique based on simple heuristics."""
        word_count = len(content.split())
        has_sections = "##" in content
        has_intro = any(phrase in content.lower() for phrase in ["sé que", "hace unos días", "el caso es que"])
        
        coherence = 8 if has_sections else 6
        style_match = 8 if has_intro else 6
        
        return {
            "coherence_score": coherence,
            "style_match": style_match,
            "engagement_score": 7,
            "authenticity_score": 7,
            "overall_score": (coherence + style_match + 7 + 7) / 4,
            "strengths": [
                "Good structure with clear sections",
                "Personal and conversational tone",
                f"Appropriate length ({word_count} words)"
            ],
            "weaknesses": [
                "Could use more specific examples",
                "Some transitions could be smoother"
            ],
            "suggestions": [
                "Add more personal anecdotes or specific examples",
                "Include more characteristic expressions naturally",
                "Strengthen the conclusion with a call to action"
            ],
            "needs_revision": False
        }
