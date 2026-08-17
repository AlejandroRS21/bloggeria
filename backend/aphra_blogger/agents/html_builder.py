"""
HTMLBuilder Agent - Converts Markdown content to structured HTML/JSX.

This agent takes generated blog content in Markdown format and converts it
to clean, semantic HTML/JSX ready for Next.js integration.
"""

import re
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

try:
    import markdown
    from markdown.extensions import fenced_code, tables, toc, codehilite
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

try:
    from ..llm import create_llm_provider, LLMProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


logger = logging.getLogger(__name__)

_COMPREHENSIVE_STOPWORDS = {
    # Spanish Stopwords
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'del', 'a', 'ante',
    'bajo', 'cabe', 'con', 'contra', 'desde', 'en', 'entre', 'hacia', 'hasta',
    'para', 'por', 'según', 'segun', 'sin', 'so', 'sobre', 'tras', 'y', 'e', 'ni', 'que',
    'pero', 'mas', 'más', 'o', 'u', 'como', 'cuando', 'donde', 'dónde', 'quien', 'quién',
    'cual', 'cuál', 'cuanto', 'cuánto', 'porque', 'porqué', 'es', 'son', 'fue', 'fueron',
    'ser', 'estar', 'ha', 'han', 'hay', 'había', 'habia', 'tiene', 'tienen', 'hacer',
    'esta', 'está', 'este', 'esto', 'estos', 'estas', 'están', 'estan', 'estaba', 'estaban',
    'otro', 'otra', 'otros', 'otras', 'mismo', 'misma', 'mismos', 'mismas', 'tan', 'tanto',
    'tanta', 'tantos', 'tantas', 'mucho', 'mucha', 'muchos', 'muchas', 'poco', 'poca',
    'pocos', 'pocas', 'cada', 'todo', 'toda', 'todos', 'todas', 'algo', 'nada', 'alguno',
    'alguna', 'algunos', 'algunas', 'ninguno', 'ninguna', 'ningunos', 'ningunas', 'aquél',
    'aquel', 'aquella', 'aquellos', 'aquellas', 'eso', 'esos', 'aquello',
    'mi', 'mis', 'tu', 'tus', 'su', 'sus', 'nuestro', 'nuestra', 'nuestros',
    'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'suya', 'suyo', 'suyos',
    'suyas', 'mía', 'mío', 'míos', 'mías', 'tuya', 'tuyo', 'tuyos', 'tuyas', 'ya', 'aún',
    'aun', 'bien', 'siempre', 'nunca', 'jamás', 'jamas', 'quizá', 'quizas', 'quizás',
    'también', 'tambien', 'tampoco', 'además', 'ademas', 'luego', 'entonces', 'así', 'asi',
    'menos', 'muy', 'casi', 'solo', 'sólo', 'parece', 'parecen', 'decir',
    'dicho', 'parte', 'partes', 'forma', 'formas', 'manera', 'maneras', 'lugar', 'lugares',
    'cosa', 'cosas', 'caso', 'casos', 'tiempo', 'años', 'anos', 'vez', 'veces',
    # English Stopwords
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'almost', 'along',
    'already', 'also', 'although', 'always', 'am', 'among', 'an', 'and', 'another',
    'any', 'anyone', 'anything', 'anywhere', 'are', 'around', 'as', 'at', 'back', 'be',
    'became', 'because', 'become', 'becomes', 'becoming', 'been', 'before', 'behind',
    'being', 'below', 'beside', 'between', 'both', 'but', 'by', 'can', 'cannot', 'could',
    'did', 'do', 'does', 'doing', 'done', 'down', 'during', 'each', 'either', 'else',
    'even', 'ever', 'every', 'everyone', 'everything', 'few', 'for', 'from', 'further',
    'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
    'himself', 'his', 'how', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just',
    'know', 'like', 'likely', 'made', 'make', 'makes', 'many', 'may', 'me', 'might',
    'more', 'most', 'much', 'must', 'my', 'myself', 'neither', 'no', 'nor', 'not',
    'nothing', 'now', 'of', 'off', 'often', 'on', 'once', 'one', 'only', 'or', 'other',
    'others', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'part', 'per', 'perhaps',
    'please', 'same', 'see', 'seem', 'seemed', 'seeming', 'seems', 'several', 'shall',
    'she', 'should', 'since', 'so', 'some', 'someone', 'something', 'somewhere', 'still',
    'such', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then',
    'there', 'these', 'they', 'thing', 'things', 'think', 'this', 'those', 'though',
    'through', 'throughout', 'thus', 'to', 'together', 'too', 'under', 'until', 'up',
    'upon', 'us', 'use', 'used', 'uses', 'using', 'very', 'want', 'was', 'we', 'well',
    'were', 'what', 'whatever', 'when', 'where', 'which', 'while', 'who', 'whom',
    'whose', 'why', 'will', 'with', 'within', 'without', 'would', 'yes', 'yet', 'you',
    'your', 'yours', 'yourself', 'yourselves'
}

# UI strings per language (REQ-3). Unknown languages default to es.
_UI_STRINGS = {
    "es": {"back": "Volver al Blog", "reading_time": "min de lectura", "words": "palabras"},
    "en": {"back": "Back to Blog", "reading_time": "min read", "words": "words"},
}


@dataclass
class HTMLOutput:
    """Structured HTML output from HTMLBuilder."""
    html: str
    full_page: str
    meta_title: str
    meta_description: str
    meta_keywords: List[str]
    reading_time: int  # minutes
    word_count: int
    headings: List[Dict[str, str]]  # [{"level": "h2", "text": "...", "id": "..."}]


class HTMLBuilder:
    """
    Agent for converting Markdown content to HTML/JSX.
    
    Features:
    - Markdown to HTML conversion
    - Complete HTML5 page generation
    - Semantic HTML structure
    - Image placeholder integration
    - Meta tags generation
    - Table of contents extraction
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: str = "auto"
    ):
        """
        Initialize HTMLBuilder agent.
        
        Args:
            api_key: API key for LLM provider (optional)
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
                    temperature=0.7,
                    max_tokens=200
                )
                logger.info(f"HTMLBuilder initialized with LLM provider: {provider}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM provider: {e}. Using fallback mode.")
                self.llm = None
        else:
            self.llm = None
            logger.info("HTMLBuilder initialized in fallback mode")
        
        if not MARKDOWN_AVAILABLE:
            logger.warning("python-markdown not installed. Using basic conversion.")
    
    def _strip_title_from_content(self, content: str) -> tuple:
        """Strip the first Title from content, return (title, body).

        The full-page template already renders an <h1> from meta_title, so
        we remove any leading title from the body to avoid duplication.

        Handles three formats:
          - Markdown: ``# Title``
          - Plain:    ``Title: ...`` or ``title: ...``
          - Decorated:``━━━ title: ... ━━━`` (the model often wraps titles)

        Args:
            content: Raw markdown content.

        Returns:
            Tuple of (title: str, body: str).
        """
        lines = content.split("\n", 1)
        first_line = lines[0].strip()
        rest = lines[1] if len(lines) > 1 else ""

        # 1. Standard markdown heading
        if first_line.startswith("# "):
            title = first_line[2:].strip()
            body = rest.strip()
            return title, body

        # 2. Plain "Title:" or "title:" prefix
        title_match = re.match(r"^[Tt]itle:\s*(.*)", first_line)
        if title_match:
            title = title_match.group(1).strip()
            body = rest.strip()
            return title, body

        # 3. Decorated box format: ━━━━━ title: ... ━━━━━
        # Strip leading/trailing box-drawing chars, then look for "title:"
        stripped = first_line.strip("━─═– ")
        lowered = stripped.lower()
        if lowered.startswith("title:"):
            title = stripped[6:].strip()
            body = rest.strip()
            return title, body

        # Fallback — scan rest of content for a markdown heading
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
            # Remove that heading from the body too
            body = re.sub(r"^#\s+.+$\n?", "", content, count=1, flags=re.MULTILINE).strip()
            return title, body

        # No explicit title found
        return "", content

    @staticmethod
    def _resolve_language(language: Optional[str], style_profile: Optional[Dict] = None) -> str:
        """Resolve the effective page language (REQ-3).

        Explicit "es"/"en" wins; otherwise style_profile["language"];
        missing or invalid values fall back to "es".
        """
        if language in ("es", "en"):
            return language
        profile_language = (style_profile or {}).get("language")
        if profile_language in ("es", "en"):
            return profile_language
        return "es"

    def build(
        self,
        content: str,
        topic: str,
        images: Optional[List[Dict]] = None,
        style_profile: Optional[Dict] = None,
        language: Optional[str] = None
    ) -> HTMLOutput:
        """
        Convert Markdown content to structured HTML/JSX.
        
        Args:
            content: Markdown content to convert
            topic: Blog post topic (for meta tags)
            images: List of image placements from ImageSelectorAgent
            style_profile: Style profile from StyleAnalyzer (optional)
            language: "es"/"en"; defaults to style_profile["language"] or "es"
            
        Returns:
            HTMLOutput with html, full_page, and metadata
        """
        logger.info(f"Building HTML/JSX for topic: {topic}")
        lang = self._resolve_language(language, style_profile)
        
        # Strip the first # Title from content to avoid duplicate <h1>
        extracted_title, body_content = self._strip_title_from_content(content)
        
        # Convert Markdown to HTML (body only — title is in the page template)
        html = self._markdown_to_html(body_content)
        
        # Insert image placeholders
        if images:
            html = self._insert_image_placeholders(html, images)
        
        # Extract headings for TOC
        headings = self._extract_headings(html)
        
        # Calculate reading time and word count
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # ~200 words per minute
        
        # Generate meta tags — use extracted title, fallback to topic
        meta_title = extracted_title or self._generate_meta_title(topic, content)
        meta_description = self._generate_meta_description(content, language=lang)
        meta_keywords = self._extract_keywords_for_meta(content, style_profile, language=lang)
        
        # Generate full HTML page
        full_page = self.generate_full_html_page(
            html_content=html,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            reading_time=reading_time,
            word_count=word_count,
            lang=lang
        )
        
        output = HTMLOutput(
            html=html,
            full_page=full_page,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            reading_time=reading_time,
            word_count=word_count,
            headings=headings
        )
        
        logger.info(f"HTML build complete: {word_count} words, {len(headings)} headings")
        return output
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to HTML."""
        if MARKDOWN_AVAILABLE:
            # Use python-markdown for proper conversion
            md = markdown.Markdown(extensions=[
                'fenced_code',
                'tables',
                'toc',
                'codehilite',
                'nl2br'
            ])
            html = md.convert(markdown_content)
        else:
            # Fallback: basic conversion
            html = self._basic_markdown_to_html(markdown_content)
        
        # Wrap in article tag
        html = f'<article class="blog-post">\n{html}\n</article>'
        
        return html
    
    def _basic_markdown_to_html(self, content: str) -> str:
        """Basic Markdown to HTML conversion (fallback)."""
        lines = content.split('\n')
        html_lines = []
        in_code_block = False
        in_list = False
        
        for line in lines:
            # Code blocks
            if line.startswith('```'):
                if in_code_block:
                    html_lines.append('</code></pre>')
                    in_code_block = False
                else:
                    lang = line[3:].strip() or 'text'
                    html_lines.append(f'<pre><code class="language-{lang}">')
                    in_code_block = True
                continue
            
            if in_code_block:
                html_lines.append(line)
                continue
            
            # Headings
            if line.startswith('# '):
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('#### '):
                html_lines.append(f'<h4>{line[5:]}</h4>')
            
            # Lists
            elif line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line[2:]}</li>')
            elif re.match(r'^\d+\. ', line) is not None:
                if not in_list:
                    html_lines.append('<ol>')
                    in_list = True
                html_lines.append(f'<li>{line[line.index(".")+2:]}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                
                # Paragraphs
                if line.strip():
                    # Bold and italic
                    line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                    line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                    line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
                    html_lines.append(f'<p>{line}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        return '\n'.join(html_lines)
    
    def _insert_image_placeholders(self, html: str, images: List[Dict]) -> str:
        """Insert image placeholders into HTML."""
        for i, image in enumerate(images):
            position = image.get('position', 'section-1')
            prompt = image.get('prompt', '')
            alt_text = image.get('alt_text', 'Blog image')
            
            # Use actual URL if provided, otherwise use picsum.photos (free, no API key)
            image_url = image.get('url')
            if not image_url:
                # Seed determinístico para que misma posición siempre misma imagen
                seed = re.sub(r'[^a-zA-Z0-9]+', '-', prompt.lower().strip()[:50]).strip('-') or f"blog-img-{i}"
                image_url = f"https://picsum.photos/seed/{seed}/800/400"
            
            placeholder = f'''
<figure class="blog-image" data-position="{position}">
  <img 
    src="{image_url}" 
    alt="{alt_text}"
    data-image-prompt="{prompt}"
    loading="lazy"
  />
  <figcaption>{alt_text}</figcaption>
</figure>
'''
            
            # Insert after specific heading or at beginning
            if position == 'header':
                # Insert at the beginning of article
                html = html.replace('<article class="blog-post">', 
                                  f'<article class="blog-post">{placeholder}')
            elif position.startswith('section-'):
                # Insert after specific h2
                section_num = position.split('-')[1]
                h2_pattern = r'(<h2[^>]*>.*?</h2>)'
                matches = list(re.finditer(h2_pattern, html))
                
                if matches and int(section_num) <= len(matches):
                    insert_pos = matches[int(section_num) - 1].end()
                    html = html[:insert_pos] + placeholder + html[insert_pos:]
        
        return html
    
    
    def generate_full_html_page(
        self,
        html_content: str,
        meta_title: str,
        meta_description: str,
        meta_keywords: List[str],
        reading_time: int,
        word_count: int,
        lang: str = "es"
    ) -> str:
        """Generate a complete HTML5 page styled with Tailwind Typography."""
        ui = _UI_STRINGS.get(lang, _UI_STRINGS["es"])
        return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta_title} - Blogger Agent IA</title>
    <meta name="description" content="{meta_description}">
    <meta name="keywords" content="{', '.join(meta_keywords)}">
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Lora:ital@0;1&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .font-serif {{ font-family: 'Lora', serif; }}
    </style>
</head>
<body class="bg-gray-50 flex flex-col min-h-screen">
    <!-- Header -->
    <header class="bg-white border-b sticky top-0 z-50">
        <nav class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="../index.html" class="text-2xl font-black text-gray-900 tracking-tighter">BLOGGER<span class="text-blue-600">IA</span></a>
            <div class="flex gap-6 text-sm font-bold uppercase tracking-widest text-gray-400">
                <a href="../index.html" class="hover:text-blue-600 transition-colors">{ui["back"]}</a>
            </div>
        </nav>
    </header>

    <main class="flex-grow max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <article class="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 md:p-12 overflow-hidden">
            <header class="mb-10 text-center border-b pb-10">
                <h1 class="text-4xl md:text-5xl font-black text-gray-900 tracking-tighter mb-4 leading-tight">{meta_title}</h1>
                <div class="flex items-center justify-center gap-3 text-sm font-bold uppercase tracking-widest text-gray-400">
                    <span>{reading_time} {ui["reading_time"]}</span>
                    <span class="bg-gray-200 w-1.5 h-1.5 rounded-full"></span>
                    <span>{word_count} {ui["words"]}</span>
                </div>
            </header>
            
            <div class="prose prose-lg md:prose-xl max-w-none prose-a:text-blue-600 hover:prose-a:text-blue-500 font-serif prose-headings:font-sans prose-headings:font-black prose-img:rounded-2xl prose-img:shadow-md">
                {html_content}
            </div>
        </article>
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t py-12 mt-12">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p class="text-xs font-black text-gray-400 uppercase tracking-widest leading-loose">
                © 2026 Blogger Agent TFG<br>
                AlejandroRS21 - Universidad San Pablo CEU
            </p>
        </div>
    </footer>
</body>
</html>'''
    
    def _extract_headings(self, html: str) -> List[Dict[str, str]]:
        """Extract headings from HTML for table of contents."""
        headings = []
        
        # Find all h2 and h3 tags
        heading_pattern = r'<(h[23])(?:\s+id="([^"]*)")?[^>]*>(.*?)</\1>'
        matches = re.finditer(heading_pattern, html, re.IGNORECASE)
        
        for match in matches:
            level = match.group(1)
            heading_id = match.group(2) or self._slugify(match.group(3))
            text = re.sub(r'<[^>]+>', '', match.group(3))  # Strip tags
            
            headings.append({
                'level': level,
                'id': heading_id,
                'text': text
            })
        
        return headings
    
    def _slugify(self, text: str) -> str:
        """Convert text to slug for IDs."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Convert to lowercase and replace spaces with hyphens
        slug = text.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug
    
    def _generate_meta_title(self, topic: str, content: str) -> str:
        """Generate SEO-optimized meta title."""
        # LLM not needed for title extraction, use simple parsing
        # Extract first heading as title
        first_h1 = re.search(r'#\s+(.+)', content)
        if first_h1:
            return first_h1.group(1).strip()
        
        # Fallback to topic
        return topic
    
    def _generate_meta_description(self, content: str, language: str = "es") -> str:
        """Generate meta description from content."""
        if self.llm and self.llm.is_available():
            try:
                messages = self.llm.create_messages(
                    system_prompt="Generate a concise meta description (150-160 characters) for SEO from the following blog content.",
                    user_prompt=content[:1000]
                )
                
                response = self.llm.chat_completion(
                    messages,
                    max_tokens=100
                )
                
                description = response.content.strip()
                # Ensure it's within character limit
                if len(description) > 160:
                    description = description[:157] + "..."
                
                return description
                
            except Exception as e:
                logger.error(f"Error generating meta description: {e}")
        
        # Fallback: use first paragraph
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if not para.startswith('#') and len(para) > 50:
                # Clean markdown
                clean = re.sub(r'[#*`]', '', para)
                if len(clean) > 160:
                    clean = clean[:157] + "..."
                return clean.strip()
        
        # Language-neutral fallback (REQ-3): never force Spanish
        if language == "en":
            return "Blog article about technology and innovation."
        return "Artículo de blog sobre tecnología e innovación."

    def _extract_keywords_for_meta(
        self,
        content: str,
        style_profile: Optional[Dict] = None,
        language: str = "es"
    ) -> List[str]:
        """Extract keywords for meta tags."""
        # 1. Prefer explicit keywords from style_profile if present and non-empty
        if style_profile and isinstance(style_profile, dict):
            if style_profile.get('keywords') and isinstance(style_profile['keywords'], list):
                kw_list = [str(k).strip() for k in style_profile['keywords'] if str(k).strip()]
                if kw_list:
                    return kw_list[:10]
            # 2. Prefer topics from style_profile if present
            if style_profile.get('topics') and isinstance(style_profile['topics'], list):
                topic_list = [str(t).strip() for t in style_profile['topics'] if str(t).strip()]
                if topic_list:
                    return topic_list[:10]

        # 3. Extract from content using comprehensive ES+EN stop-word list
        clean_content = re.sub(r'[#*`_~\[\]\(\)\{\}\<\>\\\/\|\:\;\,\.\?\!\'\"]', ' ', content)
        words = clean_content.lower().split()

        filtered_words = [
            w for w in words
            if len(w) >= 3 and not w.isdigit() and w not in _COMPREHENSIVE_STOPWORDS
        ]

        from collections import Counter
        word_freq = Counter(filtered_words)
        keywords = [word for word, _ in word_freq.most_common(10)]

        # Language-neutral fallback (REQ-3): never force Spanish
        if language == "en":
            return keywords if keywords else ["blog", "technology", "innovation"]
        return keywords if keywords else ["blog", "tecnología", "innovación"]
    



if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    sample_markdown = """# Mi Primer Post

## Introducción

Este es un **ejemplo** de contenido Markdown que será convertido a HTML.

## Sección Principal

Aquí hay algunos puntos importantes:

- Punto uno
- Punto dos
- Punto tres

### Subsección

Y un poco de código:

```python
def hello_world():
    print("Hello, World!")
```

## Conclusión

Este es el final del post.
"""
    
    builder = HTMLBuilder()
    output = builder.build(
        content=sample_markdown,
        topic="Mi Primer Post",
        images=[
            {"position": "header", "prompt": "Header image", "alt_text": "Header"},
            {"position": "section-1", "prompt": "Section 1 image", "alt_text": "Section 1"}
        ]
    )
    
    print(f"Meta Title: {output.meta_title}")
    print(f"Meta Description: {output.meta_description}")
    print(f"Reading Time: {output.reading_time} min")
    print(f"Headings: {len(output.headings)}")
    print(f"\nHTML Preview:")
    print(output.html[:500] + "...")
