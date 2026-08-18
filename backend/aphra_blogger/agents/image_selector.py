"""
Image Selector Agent.

Selects appropriate images and generates prompts
for image placement in blog posts.
"""

from typing import List, Dict, Any, Optional
import os
import re

try:
    from ..llm import create_llm_provider, LLMProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class ImageSelectorAgent:
    """
    Selects images and generates image prompts for blog posts.
    
    Creates:
    - Image placement suggestions
    - Descriptive prompts for image generation
    - Alt text for accessibility
    
    Uses HuggingFace models by default for cost-effective image selection.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "auto"
    ):
        """
        Initialize the ImageSelectorAgent.
        
        Args:
            api_key: API key for LLM provider
            model: Model to use. If None, uses provider defaults.
            provider: "huggingface", "openai", or "auto"
        """
        self.model = model
        self.provider_name = provider
        
        if LLM_AVAILABLE:
            try:
                self.llm = create_llm_provider(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    temperature=0.5,
                    max_tokens=1000
                )
            except Exception as e:
                print(f"Warning: Failed to initialize LLM provider: {e}")
                self.llm = None
        else:
            self.llm = None
    
    def select_images(
        self,
        content: str,
        topic: str,
        num_images: int = 3
    ) -> List[Dict[str, str]]:
        """
        Select image placements and generate prompts.
        
        Args:
            content: Blog post content
            topic: Post topic
            num_images: Number of images to suggest
            
        Returns:
            List of image placement dictionaries
        """
        if not self.llm or not self.llm.is_available():
            return self._fallback_selection(content, topic, num_images)
        
        prompt = f"""Analyze this blog post and suggest {num_images} strategic image placements.

TOPIC: {topic}

CONTENT:
{content[:2000]}...

For each image, provide:
1. Position (header, section-1, section-2, etc.)
2. Detailed prompt for image generation (be specific and descriptive)
3. Alt text for accessibility

Return JSON array:
[
  {{
    "position": "header",
    "prompt": "detailed image generation prompt",
    "alt_text": "accessible description",
    "context": "why this image here"
  }},
  ...
]

Guidelines:
- Header image should be eye-catching and represent the main topic
- Section images should illustrate specific points
- Prompts should be detailed enough for AI image generation
- Alt text must be descriptive for screen readers

Return ONLY valid JSON array."""

        try:
            messages = self.llm.create_messages(
                system_prompt="You are an expert in visual content strategy and accessibility.",
                user_prompt=prompt
            )
            
            response = self.llm.chat_completion(messages)

            from ..llm.json_utils import extract_json
            result = extract_json(response.content)
            return result

        except Exception as e:
            print(f"Warning: Image selection failed: {e}. Using fallback.")
            return self._fallback_selection(content, topic, num_images)
    
    def _fallback_selection(
        self,
        content: str,
        topic: str,
        num_images: int
    ) -> List[Dict[str, str]]:
        """Fallback image selection based on content analysis."""
        images = [
            {
                "position": "header",
                "prompt": f"Professional, modern hero image representing {topic}. "
                         f"Clean design, technology theme, high quality, 16:9 aspect ratio",
                "alt_text": f"Hero image about {topic}",
                "context": "Main visual to grab attention"
            }
        ]
        
        # Find sections in content
        sections = re.findall(r'## (.+)', content)
        
        for i, section in enumerate(sections[:num_images-1], 1):
            images.append({
                "position": f"section-{i}",
                "prompt": f"Illustrative image for blog section about {section}. "
                         f"Related to {topic}, professional style, clear and informative",
                "alt_text": f"Illustration for section: {section}",
                "context": f"Visual support for {section} section"
            })
        
        # If not enough sections, add generic images
        while len(images) < num_images:
            i = len(images)
            images.append({
                "position": f"section-{i}",
                "prompt": f"Supporting image about {topic}, modern design, technology theme",
                "alt_text": f"Supporting image {i} for {topic}",
                "context": "Additional visual content"
            })
        
        return images[:num_images]
