"""Tests for HTMLBuilder agent."""

import pytest
from aphra_blogger.agents.html_builder import HTMLBuilder, HTMLOutput


from aphra_blogger.llm.base import LLMResponse


class _EchoLLM:
    """Stub LLM that echoes the meta-description instruction back."""

    def __init__(self, text: str):
        self._text = text

    def is_available(self) -> bool:
        return True

    def create_messages(self, system_prompt, user_prompt):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def chat_completion(self, messages, **kwargs):
        return LLMResponse(
            content=self._text,
            model="stub",
            provider="stub",
            finish_reason="stop",
        )


class TestMetaDescriptionEchoGuard:
    """Instruction-echo output must fall back to deterministic extraction."""

    def test_echo_falls_back_to_first_paragraph(self):
        echo = (
            "The user wants a concise meta description (150-160 characters) "
            "for SEO based on the blog content provided."
        )
        builder = HTMLBuilder(api_key=None)
        builder.llm = _EchoLLM(echo)

        markdown = (
            "# Titulo\n\n"
            "Este es un primer parrafo real que describe el articulo y es lo bastante largo como para servir de descripcion."
        )
        output = builder.build(content=markdown, topic="Test")

        assert "The user wants" not in output.meta_description
        assert "concise meta description" not in output.meta_description
        assert "primer parrafo real" in output.meta_description

    def test_valid_description_is_kept(self):
        good = "Una descripcion SEO real y breve del articulo."
        builder = HTMLBuilder(api_key=None)
        builder.llm = _EchoLLM(good)

        markdown = "# Titulo\n\nPrimer parrafo que no deberia usarse porque la salida es valida."
        output = builder.build(content=markdown, topic="Test")

        assert output.meta_description == good

    def test_echo_markers_detected(self):
        for echo in [
            "The user wants a concise meta description",
            "Meta description for SEO, between 150-160 characters",
            "SEO based on the provided content",
        ]:
            assert HTMLBuilder._is_instruction_echo(echo) is True
        assert HTMLBuilder._is_instruction_echo("Una descripcion normal.") is False
class TestHTMLBuilder:
    """Tests for HTMLBuilder agent."""
    
    def test_initialization(self):
        """Test HTMLBuilder initialization."""
        builder = HTMLBuilder()
        assert builder is not None
    
    def test_initialization_with_api_key(self):
        """Test initialization with API key."""
        builder = HTMLBuilder(api_key="test-key")
        # Verify builder is initialized (new LLM system doesn't expose api_key directly)
        assert builder is not None
        assert hasattr(builder, 'llm')
    
    def test_basic_markdown_conversion(self):
        """Test basic Markdown to HTML conversion."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = """# Test Title

## Section 1

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2
"""
        
        output = builder.build(
            content=markdown,
            topic="Test Topic"
        )
        
        assert isinstance(output, HTMLOutput)
        # The <h1> is stripped from body to avoid duplicate with page template
        assert '<h1' not in output.html, "<h1> should be stripped from body html"
        assert 'Test Title' not in output.html, "Title should be stripped from body html"
        # The <h1> lives in full_page template
        assert '<h1' in output.full_page
        assert 'Test Title' in output.full_page or 'Test Title' == output.meta_title
        # <h2> sections remain in body html
        assert '<h2' in output.html
        assert 'Section 1' in output.html
        assert '<article' in output.html
    
    def test_html_output_structure(self):
        """Test that HTMLOutput has all required fields."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = "# Test\n\nContent here."
        output = builder.build(content=markdown, topic="Test")
        
        assert hasattr(output, 'html')
        assert hasattr(output, 'meta_title')
        assert hasattr(output, 'meta_description')
        assert hasattr(output, 'meta_keywords')
        assert hasattr(output, 'reading_time')
        assert hasattr(output, 'word_count')
        assert hasattr(output, 'headings')
    
    def test_word_count_calculation(self):
        """Test word count calculation."""
        builder = HTMLBuilder(api_key=None)
        
        # exactly 100 words
        words = ' '.join(['word'] * 100)
        markdown = f"# Title\n\n{words}"
        
        output = builder.build(content=markdown, topic="Test")
        
        assert output.word_count >= 100  # At least 100 (includes title)
    
    def test_reading_time_calculation(self):
        """Test reading time calculation."""
        builder = HTMLBuilder(api_key=None)
        
        # 400 words = ~2 min reading time (200 words/min)
        words = ' '.join(['word'] * 400)
        markdown = f"# Title\n\n{words}"
        
        output = builder.build(content=markdown, topic="Test")
        
        assert output.reading_time >= 2
    
    def test_meta_title_extraction(self):
        """Test meta title extraction from H1."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = "# My Amazing Title\n\nContent"
        output = builder.build(content=markdown, topic="Test")
        
        assert output.meta_title == "My Amazing Title"
    
    def test_meta_title_fallback(self):
        """Test meta title fallback to topic."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = "Content without H1"
        output = builder.build(content=markdown, topic="Fallback Topic")
        
        assert output.meta_title == "Fallback Topic"
    
    def test_meta_description_generation(self):
        """Test meta description generation."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = """# Title

This is the first paragraph that should be used as description.

Second paragraph."""
        
        output = builder.build(content=markdown, topic="Test")
        
        assert output.meta_description
        assert len(output.meta_description) <= 160
    
    def test_meta_keywords_extraction(self):
        """Test meta keywords extraction."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = "# Title\n\nContent with technology innovation artificial intelligence"
        output = builder.build(content=markdown, topic="Test")
        
        assert isinstance(output.meta_keywords, list)
        assert len(output.meta_keywords) > 0
    
    def test_heading_extraction(self):
        """Test extraction of headings for TOC."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = """# Main Title

## Section 1

### Subsection 1.1

## Section 2
"""
        
        output = builder.build(content=markdown, topic="Test")
        
        assert isinstance(output.headings, list)
        # Should extract h2 and h3 (not h1)
        assert len(output.headings) >= 2
        
        if output.headings:
            heading = output.headings[0]
            assert 'level' in heading
            assert 'text' in heading
            assert 'id' in heading
    
    def test_image_placeholder_insertion(self):
        """Test insertion of image placeholders."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = """# Title

## Section 1

Content here.

## Section 2

More content."""
        
        images = [
            {
                "position": "header",
                "prompt": "Header image prompt",
                "alt_text": "Header image"
            },
            {
                "position": "section-1",
                "prompt": "Section 1 image",
                "alt_text": "Section image"
            }
        ]
        
        output = builder.build(
            content=markdown,
            topic="Test",
            images=images
        )
        
        assert '<figure' in output.html
        assert 'blog-image' in output.html
        assert 'Header image' in output.html
    
    def test_slugify(self):
        """Test slug generation."""
        builder = HTMLBuilder(api_key=None)
        
        assert builder._slugify("Hello World") == "hello-world"
        assert builder._slugify("Test & Title!") == "test-title"
        assert builder._slugify("  Multiple   Spaces  ") == "multiple-spaces"
    
    def test_code_block_handling(self):
        """Test code block conversion."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = """# Title

```python
def hello():
    print("Hello")
```
"""
        
        output = builder.build(content=markdown, topic="Test")
        
        # Should contain code tags
        assert '<code' in output.html or '<pre' in output.html
    
    def test_list_handling(self):
        """Test list conversion."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = """# Title

- Item 1
- Item 2
- Item 3
"""
        
        output = builder.build(content=markdown, topic="Test")
        
        assert '<ul' in output.html or '<li' in output.html
    
    def test_bold_italic_handling(self):
        """Test bold and italic conversion."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = "# Title\n\nThis has **bold** and *italic* text."
        output = builder.build(content=markdown, topic="Test")
        
        assert '<strong>' in output.html or '<b>' in output.html or 'bold' in output.html
        assert '<em>' in output.html or '<i>' in output.html or 'italic' in output.html


class TestHTMLBuilderWithStyleProfile:
    """Tests for HTMLBuilder with style profile."""
    
    def test_keywords_from_style_profile(self):
        """Test using keywords from style profile."""
        builder = HTMLBuilder(api_key=None)
        
        style_profile = {
            "keywords": ["technology", "AI", "innovation", "future", "digital"]
        }
        
        markdown = "# Test\n\nContent"
        output = builder.build(
            content=markdown,
            topic="Test",
            style_profile=style_profile
        )
        
        assert len(output.meta_keywords) > 0
        # Should use keywords from style profile
        assert any(kw in ["technology", "AI", "innovation"] for kw in output.meta_keywords)


class TestHTMLBuilderEdgeCases:
    """Edge case tests for HTMLBuilder."""
    
    def test_empty_content(self):
        """Test with empty content."""
        builder = HTMLBuilder(api_key=None)
        
        output = builder.build(content="", topic="Test")
        
        assert output.word_count == 0
        assert output.reading_time == 1  # Minimum 1 minute
    
    def test_very_long_content(self):
        """Test with very long content."""
        builder = HTMLBuilder(api_key=None)
        
        # 2000 words
        long_content = "# Title\n\n" + " ".join(["word"] * 2000)
        output = builder.build(content=long_content, topic="Test")
        
        assert output.word_count >= 2000
        assert output.reading_time >= 10  # At least 10 minutes
    
    def test_content_without_headings(self):
        """Test content without any headings."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = "Just plain content without any headings."
        output = builder.build(content=markdown, topic="Test")
        
        assert isinstance(output.headings, list)
        # May be empty list
    
    def test_special_characters_in_content(self):
        """Test handling of special characters."""
        builder = HTMLBuilder(api_key=None)
        
        markdown = "# Title with <special> & characters\n\nContent with © and ™"
        output = builder.build(content=markdown, topic="Test")
        
        # Should handle gracefully
        assert output.html


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
