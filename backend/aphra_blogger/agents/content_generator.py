"""
Content Generator Agent.

Generates blog content in the style of the analyzed blogger.
Uses few-shot learning and style profiles extracted from corpus.
"""

from typing import Dict, Any, Optional, List
import os

try:
    from ..llm import create_llm_provider, LLMProvider

    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


# Language rule blocks (REQ-2). "es" entries MUST stay byte-identical
# to the frozen goldens in tests/golden/es_rules_*.txt (REQ-7).
_LANGUAGE_RULES_ES_MAIN = '- ### IDIOMA — español REAL, nada de Spanglish\n  - Escribe TODO el post en ESPAÑOL. Título, cuerpo, secciones, TODO.\n  - Traduce cualquier término técnico: "Machine Learning" → "Aprendizaje Automático", "Deep Learning" → "Aprendizaje Profundo", "Neural Networks" → "Redes Neuronales", "Data Science" → "Ciencia de Datos", "Data Preprocessing" → "Preprocesamiento de Datos", "Model Training" → "Entrenamiento de Modelos".\n  - NO dejes NINGUNA palabra en inglés suelta. Nada de "on-line", "performance", "disappointing resultado". TODO traducido.\n  - Usa vocabulario español real, no inventes palabras ("alcanceado" → "alcanzado", "percaté" → "me di cuenta").\n\n- ### GRAMÁTICA y ortografía\n  - Usa tildes correctamente (empecé, percaté, está, cómo, así).\n  - Respeta la concordancia de género y número ("estos temas", no "estas temas").\n  - No inventes palabras. Si no estás seguro de una palabra, usa un sinónimo conocido.\n\n- ### REGISTRO — voz y dialecto consistentes con el blogger original\n  - Identifica el dialecto del blogger a partir de su perfil de estilo y los ejemplos reales.\n  - Si el blogger es de España (tuteo, expresiones como "mazo", "brutal", "o sea"), escribe TODO el post en español peninsular (tú, tienes, fíjate, etc.).\n  - Si el blogger es de Argentina/Uruguay (voseo), usa voseo (vos, tenés, pensá, etc.).\n  - NUNCA mezcles dialectos o pronombres (por ejemplo, no mezcles "tú tienes" con "pensá" o "¿entendés?"). El post (incluyendo el título) debe sonar 100% coherente al origen del blogger.\n  - Elige UN registro (formal o informal) congruente con el blogger y mantenlo todo el post.\n  - Evita el registro formal a menos que el blogger lo use de forma explícita.\n\n- ### TÍTULO PRINCIPAL — formato correcto\n  - La PRIMERA LÍNEA del post debe ser EXACTAMENTE: `# <título gancho>`\n  - Usa el formato markdown `# ` al inicio. NO uses `━━━ title: ... ━━━` ni `Title: ...` ni mayúsculas decorativas.\n  - El título debe ser UN GANCHO: datos concretos, afirmaciones audaces, o contrastes impactantes.\n  - El título debe seguir estrictamente el dialecto del blogger. Si el blogger es de España, el título NO debe llevar acentuación de voseo (ej: usa "esperas" en lugar de "esperás").\n  - Ejemplos BUENOS: `# Los 634 segundos que casi vacían la cartera de un programador`, `# El truco sucio de las academias que prometen programadores en 3 meses`.\n  - Ejemplos MALOS (NUNCA uses estos): títulos en inglés, preguntas tipo "¿Es X realmente Y?", títulos genéricos como "Análisis de X".'

_LANGUAGE_RULES_ES_SIMPLIFIED = '- ### IDIOMA — español REAL, nada de Spanglish\n  - Escribe TODO el post en ESPAÑOL. Título, cuerpo, secciones, TODO.\n  - Traduce cualquier término técnico: "Machine Learning" → "Aprendizaje Automático", "Deep Learning" → "Aprendizaje Profundo", "Neural Networks" → "Redes Neuronales", "Data Science" → "Ciencia de Datos", etc.\n  - NO dejes NINGUNA palabra en inglés suelta. TODO traducido.\n  - Usa vocabulario español real, no inventes palabras.\n\n- ### GRAMÁTICA y ortografía\n  - Usa tildes correctamente (empecé, percaté, está, cómo, así).\n  - Respeta la concordancia de género y número.\n  - No inventes palabras. Usa sinónimos conocidos.\n\n- ### REGISTRO — voz y dialecto consistentes con el blogger original\n  - Identifica el dialecto del blogger a partir de su perfil de estilo.\n  - Si el blogger es de España (tuteo, expresiones como "mazo", "brutal", "o sea"), escribe TODO el post en español peninsular (tú, tienes, fíjate, etc.).\n  - Si el blogger es de Argentina/Uruguay (voseo), usa voseo (vos, tenés, pensá, etc.).\n  - NUNCA mezcles dialectos o pronombres (por ejemplo, no mezcles "tú tienes" con "pensá" o "¿entendés?"). El post (incluyendo el título) debe sonar 100% coherente al origen del blogger.\n  - Elige UN registro (formal o informal) congruente con el blogger y mantenlo todo el post.\n  - Evita el registro formal a menos que el blogger lo use de forma explícita.\n\n- ### TÍTULO PRINCIPAL — formato correcto\n  - La PRIMERA LÍNEA debe ser EXACTAMENTE: `# <título gancho>`\n  - Usa formato markdown `# `. NO uses `━━━ title:` ni `Title:` ni mayúsculas decorativas.\n  - El título debe ser UN GANCHO: datos concretos, afirmaciones audaces.\n  - El título debe seguir estrictamente el dialecto del blogger. Si el blogger es de España, el título NO debe llevar acentuación de voseo (ej: usa "esperas" en lugar de "esperás").\n  - NUNCA uses títulos en inglés ni preguntas tipo "¿Es X realmente Y?".'

_LANGUAGE_RULES_EN = '- ### LANGUAGE — write in real English\n  - Write the ENTIRE post in ENGLISH. Title, body, sections, everything.\n  - Keep technical terms as-is ("Machine Learning", "Deep Learning", "Neural Networks", "Data Science"). Do NOT translate them.\n  - Do not leave stray words in other languages.\n  - Use natural English vocabulary.\n\n- ### GRAMMAR and spelling\n  - Use correct English grammar and spelling.\n  - Respect subject-verb agreement ("these topics", not "this topics").\n  - Don\'t invent words. When unsure, use a known synonym.\n\n- ### VOICE and register\n  - Match the blogger\'s voice from the style profile and real examples.\n  - Pick ONE register (formal or informal) consistent with the blogger and keep it for the whole post.\n  - Avoid formal register unless the blogger explicitly uses it.\n\n- ### MAIN TITLE — correct format\n  - The FIRST LINE of the post must be EXACTLY: `# <hook title>`\n  - Use markdown `# ` at the start. Do NOT use `━━━ title: ... ━━━` nor `Title: ...` nor decorative caps.\n  - The title must be a HOOK: concrete data, bold claims, or striking contrasts.\n  - Examples of GOOD titles: `# The 634 seconds that almost emptied a programmer\'s wallet`, `# The dirty trick of bootcamps that promise programmers in 3 months`.\n'

_SYSTEM_PROMPTS = {
    "es": "Eres un escritor de blogs profesional. Escribes posts como lo haría el blogger real: con voz propia, estructura orgánica, y respetando fielmente su estilo lingüístico y dialecto original sin caer en modismos que no correspondan.",
    "en": "You are a professional blog writer. You write posts the way the real blogger would: with your own voice, organic structure, and faithfully respecting their linguistic style and dialect without falling into mannerisms that do not fit.",
}

_ATTRIBUTION_TEMPLATES = {
    "es": "\n\n---\n\n*✍️ Este post fue escrito emulando el estilo de [{name}]({url}).*",
    "en": "\n\n---\n\n*✍️ This post was written emulating the style of [{name}]({url}).*",
}

class ContentGenerator:
    """
    Generates blog content based on a topic and style profile.

    Creates:
    - Initial draft content
    - Styled content matching blogger's voice
    - Refined content based on critique

    Uses HuggingFace models by default (Llama 3.1 70B for best quality).
    """

    def __init__(
        self, api_key: Optional[str] = None, model: Optional[str] = None, provider: str = "auto"
    ):
        """
        Initialize the ContentGenerator.

        Args:
            api_key: API key for LLM provider
            model: Model to use. If None, uses high-quality model for generation.
            provider: "huggingface", "openai", or "auto"
        """
        self.model = model
        self.provider_name = provider
        self.style_profile = None

        if LLM_AVAILABLE:
            try:
                self.llm = create_llm_provider(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    temperature=0.9,
                    max_tokens=4096,
                )
            except Exception as e:
                print(f"Warning: Failed to initialize LLM provider: {e}")
                self.llm = None
        else:
            self.llm = None

    def load_style_profile(self, profile_path: str):
        """Load style profile from JSON file."""
        import json

        with open(profile_path, "r", encoding="utf-8") as f:
            self.style_profile = json.load(f)
        return self.style_profile

    def set_style_profile(self, profile: Dict[str, Any]):
        """Set style profile directly."""
        self.style_profile = profile

    def _fit_context_to_token_limit(
        self, sample_text: str, research_context: str, overhead_chars: int = 2000
    ) -> tuple:
        """Truncate sample_text and research_context to fit within token budget.

        Modal LLM has 4096 total tokens. We reserve ~1024 for output + overhead,
        leaving ~3072 tokens for input context. At ~4 chars/token in Spanish,
        that's ~8000 chars total input.

        Returns:
            Tuple of (truncated_sample, truncated_research)
        """
        budget = 8000  # chars (~2000 tokens, leaving ~2000 for output + overhead)
        sample_trimmed = (sample_text or "")[:8000]
        research_trimmed = (research_context or "")[:8000]

        # Rough estimate of total input chars (including template overhead)
        total = len(sample_trimmed) + len(research_trimmed) + overhead_chars

        if total <= budget:
            return sample_trimmed, research_trimmed

        # Need to cut: prioritize research (factual) over sample (style reference)
        # Cut research first, then sample if still over
        research_trimmed = research_trimmed[:4000]
        total = len(sample_trimmed) + len(research_trimmed) + overhead_chars

        if total <= budget:
            return sample_trimmed, research_trimmed

        # Still over: cut both proportionally
        excess = total - budget
        sample_trimmed = sample_trimmed[: max(500, len(sample_trimmed) - excess // 2)]
        research_trimmed = research_trimmed[: max(500, len(research_trimmed) - excess // 2)]

        return sample_trimmed, research_trimmed

    @staticmethod
    def _extract_blogger_name(blogger_urls: Optional[List[str]]) -> str:
        """Extract a human-readable blogger name from URLs."""
        if not blogger_urls or not blogger_urls[0]:
            return "el blogger de referencia"
        url = blogger_urls[0].strip().rstrip("/")
        # Remove protocol
        for prefix in ("https://", "http://", "www."):
            if url.startswith(prefix):
                url = url[len(prefix):]
        # Take the domain name part (before first / or .)
        name = url.split("/")[0]
        # If it's a subdomain like "blog.ejemplo.com", use the main domain
        parts = name.split(".")
        if len(parts) >= 3:
            name = parts[1]  # "ejemplo" from "blog.ejemplo.com"
        elif len(parts) >= 2:
            name = parts[0]  # "ejemplo" from "ejemplo.com"
        return name.capitalize()

    @staticmethod
    def _resolve_language(language: str, style_profile: Optional[Dict[str, Any]]) -> str:
        """Resolve the effective generation language (REQ-2).

        Explicit "es"/"en" wins; "auto" reads style_profile["language"];
        missing or invalid values fall back to "es".
        """
        if language in ("es", "en"):
            return language
        if language == "auto":
            profile_language = (style_profile or {}).get("language")
            if profile_language in ("es", "en"):
                return profile_language
        return "es"

    @staticmethod
    def _language_rules(language: str, simplified: bool = False) -> str:
        """Return the IDIOMA/GRAMÁTICA/REGISTRO/TÍTULO rules block (REQ-2).

        "es" returns the block byte-identical to the pre-change prompts
        (frozen in tests/golden/es_rules_*.txt); "en" returns English-only
        rules with technical terms kept as-is and no dialect/voseo rules.
        """
        if language == "en":
            return _LANGUAGE_RULES_EN
        return _LANGUAGE_RULES_ES_SIMPLIFIED if simplified else _LANGUAGE_RULES_ES_MAIN

    @staticmethod
    def _build_style_context(profile: Dict[str, Any], blogger_urls: Optional[List[str]]) -> str:
        """Build a rich style context block from the profile."""
        if not profile:
            return ""

        name = ContentGenerator._extract_blogger_name(blogger_urls)
        blocks = [f"━━━━━━ PERFIL DE ESTILO ─────────────────────"]
        blocks.append(f"Blogger de referencia: {name}")
        if blogger_urls:
            blocks.append(f"Blog de referencia: {blogger_urls[0].strip().rstrip('/')}")

        tone = profile.get("tone", "")
        voice = profile.get("voice", "")
        if tone or voice:
            blocks.append(f"\nTono y Voz:")
            if tone:
                blocks.append(f"  Tono: {tone}")
            if voice:
                blocks.append(f"  Voz: {voice}")

        vocab = profile.get("vocabulary", [])
        if vocab:
            blocks.append(f"\nVocabulario característico (usa estas palabras):")
            blocks.append(f"  {', '.join(vocab[:15])}")

        expressions = profile.get("expressions", [])
        if expressions:
            blocks.append(f"\nExpresiones típicas (incorpóralas naturalmente):")
            blocks.append(f"  {', '.join(expressions[:8])}")

        transitions = profile.get("transition_phrases", [])
        if transitions:
            blocks.append(f"\nFrases de transición (úsalas para conectar ideas):")
            blocks.append(f"  {', '.join(transitions[:6])}")

        tech = profile.get("technical_level", "")
        if tech:
            blocks.append(f"\nNivel técnico: {tech}")

        humor = profile.get("use_of_humor", "")
        if humor:
            blocks.append(f"Uso de humor: {humor}")

        engagement = profile.get("engagement_style", "")
        if engagement:
            blocks.append(f"Interacción con lectores: {engagement}")

        opens = profile.get("common_opens", [])
        if opens:
            blocks.append(f"\nCómo suele empezar:")
            blocks.append(f"  \"{opens[0]}\"")

        closes = profile.get("common_closes", [])
        if closes:
            blocks.append(f"Cómo suele terminar:")
            blocks.append(f"  \"{closes[0]}\"")

        blocks.append("━━━━━━ FIN DEL PERFIL ─────────────────")
        return "\n".join(blocks)

    @staticmethod
    def _build_attribution(blogger_urls: Optional[List[str]], language: str = "es") -> str:
        """Build attribution footer for the post, localized per language."""
        if not blogger_urls or not blogger_urls[0]:
            return ""
        name = ContentGenerator._extract_blogger_name(blogger_urls)
        url = blogger_urls[0].strip().rstrip("/")
        template = _ATTRIBUTION_TEMPLATES.get(language, _ATTRIBUTION_TEMPLATES["es"])
        return template.format(name=name, url=url)

    def generate_draft(
        self,
        topic: str,
        style_profile: Dict[str, Any] = None,
        keywords: list = None,
        sample_text: str = None,
        research_context: str = None,
        min_words: int = 1500,
        max_words: int = 2500,
        blogger_urls: List[str] = None,
        language: str = "auto",
    ) -> str:
        """
        Generate initial draft content using in-context learning from real blog examples.

        Args:
            topic: Topic to write about
            style_profile: Style profile (from StyleAnalyzer)
            keywords: Keywords from KeywordExtractor
            sample_text: Actual blog text scraped from the blogger, used for style reference
            research_context: Real search results and data about the topic for factual grounding
            min_words: Minimum word count
            max_words: Maximum word count
            blogger_urls: Original blogger URLs for attribution
            language: "auto" (explicit > style_profile > "es"), "es" or "en"

        Returns:
            Draft content as markdown string
        """
        profile = style_profile or self.style_profile or {}
        effective_language = self._resolve_language(language, profile)

        if not self.llm or not self.llm.is_available():
            return self._fallback_draft(topic, keywords, profile, effective_language)

        keywords_str = ", ".join(keywords[:10]) if keywords else ""

        # Build a rich style context block from the full profile
        style_context = self._build_style_context(profile, blogger_urls)

        # Build attribution footer
        attribution = self._build_attribution(blogger_urls, effective_language)

        # Fit context to Modal's 4096 token limit
        sample_text, research_context = self._fit_context_to_token_limit(
            sample_text, research_context
        )

        # Research context block (información factual real)
        research_block = ""
        if research_context and len(research_context.strip()) > 100:
            research_block = f"""
━━━━━━ INFORMACIÓN REAL SOBRE EL TEMA ━━━━━━━━
Usa esta información como base factual para el post. No inventes datos, básate en esto.
{research_context}
━━━━━━ FIN DE INFORMACIÓN ━━━━━━━━━━━━━━━━━━━━━
"""

        # Name for the instruction block
        blogger_name = self._extract_blogger_name(blogger_urls)

        if sample_text and len(sample_text.strip()) > 200:
            # ---- PROMPT CON EJEMPLOS REALES (modo principal) ----
            language_rules = self._language_rules(effective_language, simplified=False)
            prompt = f"""Abajo tienes posts REALES escritos por {blogger_name}, cuyo estilo de escritura tienes que imitar fielmente, e información factual sobre el tema del post.

━━━━━━ EJEMPLOS DEL BLOGGER ORIGINAL ────────
{sample_text[:20000]}
━━━━━━ FIN DE LOS EJEMPLOS ──────────────────
{research_block}
Ahora escribe un NUEVO post sobre: {topic}

{style_context}

REGLAS:

{language_rules}

- ### CONTENIDO y estructura
  - BÁSATE EN LA INFORMACIÓN REAL proporcionada arriba. No inventes datos.
  - NUNCA uses citas académicas en formato numérico entre corchetes (ej: [1], [2], [1, 2], [3]). Escribe de forma fluida y narrativa (ej: "según explica X...", "como se comenta en Y...").
  - Filtra y omite detalles trágicos sobre guerras, víctimas civiles o crímenes de guerra del contexto de investigación, a menos que el tema sea militar o geopolítico. Enfócate estrictamente en los aspectos tecnológicos o de opinión general acordes al blogger.
  - Usa **negritas** (formato `**texto**` de markdown) para resaltar las palabras clave, ideas principales o términos más importantes del texto, logrando que el artículo sea escaneable visualmente.
  - Incluye AL MENOS 2 datos concretos o citas específicas de la investigación. No te quedes en generalidades.
  - NO uses estructuras de plantilla como "Contexto", "Introducción", "Lo que he aprendido", "Reflexión final" o "Conclusión" como títulos de sección. Deja que la estructura fluya naturalmente.
  - Cada título de sección debe ser ESPECÍFICO al contenido concreto, no genérico. Si ese título pudiera aparecer en cualquier otro post, está mal.
  - Piensa: "¿Qué es lo más interesante de esta información?" y empieza por ahí.
  - Varía la longitud de las secciones. Algunas ideas merecen un párrafo, otras merecen varios.
  - Si el blogger usa primera persona, anécdotas personales, humor, etc., haz lo mismo.
  - Menciona estos temas si aplican naturalmente: {keywords_str}

- ### ESTILO — emulación del blogger + que no parezca IA
  - Emula el estilo de {blogger_name} en TODO el post: su vocabulario, expresiones, tono, forma de empezar y terminar. El perfil de estilo está arriba.
  - NO aclares que esto es contenido generado por IA.
  - NO generes URLs de imágenes falsas (src="https://..." inventadas).
  - Varía los conectores. No uses "Sin embargo" más de una vez. Alterna con "Pero", "No obstante", "Ahora bien", "Eso sí", "El problema", "Lo cierto es que", etc.
  - Escribe como un ser humano, no como un asistente. Sin estructuras repetitivas.

Escribe el post completo ahora:{attribution}"""
        else:
            # ---- PROMPT SIMPLIFICADO (sin ejemplos del blogger) ----
            language_rules = self._language_rules(effective_language, simplified=True)
            prompt = f"""{research_block}
Escribe un post de blog imitando el estilo de {blogger_name}. Abajo está su perfil de estilo.

Tema: {topic}

{style_context}

REGLAS:

{language_rules}

- ### CONTENIDO y calidad
  - BÁSATE EN LA INFORMACIÓN REAL. No inventes datos.
  - NUNCA uses citas en formato numérico entre corchetes (ej: [1], [2], [1, 2], [3]). Escribe de forma fluida y narrativa (ej: "según explica X...", "como se comenta en Y...").
  - Filtra y omite detalles trágicos sobre guerras, víctimas civiles o crímenes de guerra del contexto de investigación, a menos que el tema sea militar o geopolítico. Enfócate estrictamente en los aspectos tecnológicos o de opinión general acordes al blogger.
  - Usa **negritas** (formato `**texto**` de markdown) para resaltar las palabras clave, ideas principales o términos más importantes del texto, logrando que el artículo sea escaneable visualmente.
  - Incluye AL MENOS 2 datos concretos de la investigación.
  - NO uses títulos genéricos como "Introducción" o "Conclusión".
  - Cada título de sección debe ser ESPECÍFICO al contenido concreto.
  - Varía la longitud de las secciones.
  - Menciona estos temas si aplican: {keywords_str}
  - Longitud: entre {min_words} y {max_words} palabras.

- ### ESTILO — emulación del blogger + que no parezca IA
  - Emula el estilo de {blogger_name}: su vocabulario, expresiones, tono y forma de escribir. El perfil está arriba.
  - NO aclares que es contenido generado por IA.
  - NO generes URLs de imágenes falsas.
  - Varía los conectores. No uses "Sin embargo" más de una vez. Alterna con "Pero", "Eso sí", "El problema", "Lo cierto es que", etc.
  - Escribe como un ser humano, no como un asistente.

Escribe el post ahora:{attribution}"""

        try:
            messages = self.llm.create_messages(
                system_prompt=_SYSTEM_PROMPTS.get(effective_language, _SYSTEM_PROMPTS["es"]),
                user_prompt=prompt,
            )

            response = self.llm.chat_completion(messages, temperature=0.9, max_tokens=4000)

            return response.content

        except Exception as e:
            print(f"Warning: Content generation failed: {e}. Using fallback.")
            return self._fallback_draft(topic, keywords, profile)

    @staticmethod
    def _build_refine_prompt(
        draft: str,
        critique_feedback: Dict[str, Any],
        language: str,
        style_profile: Dict[str, Any] = None,
    ) -> str:
        """Build the refinement user prompt (language-aware).

        Reuses the frozen language rules (REQ-7 goldens) and the localized
        system prompt so refined output stays in the target language.
        """
        language_rules = ContentGenerator._language_rules(language)

        suggestions = critique_feedback.get("suggestions", [])
        suggestions_str = "\\n".join(f"- {s}" for s in suggestions)

        return f"""Refine this blog post based on the critique feedback.

ORIGINAL CONTENT:
{draft}

CRITIQUE FEEDBACK:
Coherence Score: {critique_feedback.get("coherence_score", "N/A")}/10
Style Match: {critique_feedback.get("style_match", "N/A")}/10

SUGGESTIONS:
{suggestions_str}

INSTRUCTIONS:
- Keep the same overall structure and tone
- Address the suggestions while maintaining the blogger's voice
- Ensure smooth transitions and coherence
- Preserve personal anecdotes and expressions
- Keep the length similar (don't add too much)

LANGUAGE RULES (MUST follow strictly):

{language_rules}

Provide the refined version in markdown format."""

    def refine_content(
        self,
        draft: str,
        critique_feedback: Dict[str, Any],
        style_profile: Dict[str, Any],
        language: str = "es",
    ) -> str:
        """
        Refine content based on critique feedback.

        Args:
            draft: Original draft
            critique_feedback: Feedback from CriticAgent
            style_profile: Style profile for reference
            language: Target language ("es" or "en") for the refined output.
                Defaults to "es".

        Returns:
            Refined content
        """
        if not self.llm or not self.llm.is_available():
            return draft  # Return original if no LLM available

        prompt = self._build_refine_prompt(
            draft=draft,
            critique_feedback=critique_feedback,
            language=language,
            style_profile=style_profile,
        )

        try:
            messages = self.llm.create_messages(
                system_prompt=_SYSTEM_PROMPTS.get(language, _SYSTEM_PROMPTS["es"]),
                user_prompt=prompt,
            )

            response = self.llm.chat_completion(messages, temperature=0.7, max_tokens=3500)

            return response.content

        except Exception as e:
            print(f"Warning: Refinement failed: {e}. Returning original draft.")
            return draft

    def _fallback_draft(
        self, topic: str, keywords: list = None, style_profile: Dict[str, Any] = None,
        language: str = "es",
    ) -> str:
        """Generate a basic draft when LLM is not available."""
        if language == "en":
            keywords_str = ", ".join(keywords[:5]) if keywords else "technology, innovation"

            return f"""# {topic}

Exploring the implications of {topic} and its current impact.

## Introduction to the Topic

The current landscape forces us to look closely at how everything evolves. When we analyze this, we realize there is much more beneath the surface. The connection with {keywords_str} becomes evident when we look at it in detail.

## Development and Key Points

First, it is important to understand the fundamental context. It did not appear without precedent; it represents the maturation of certain previous ideas. As we go deeper, the patterns become clearer.

It is worth highlighting some essential elements:
- The rapid evolution of the tools.
- The need for constant adaptation.
- The challenges inherent in implementation.

## Analysis and Perspective

When evaluating the alternatives, it is clear there is no single correct solution. It depends largely on the use case and the specific goals being pursued.

## Conclusion

In short, {topic} represents another step in this direction. We will keep watching how this whole landscape develops in the coming months. The debate, for sure, is on the table.
"""

        keywords_str = ", ".join(keywords[:5]) if keywords else "tecnología, innovación"

        return f"""# {topic}

Explorando a fondo las implicaciones de {topic} y su impacto actual.

## Introducción al Tema

El panorama actual nos obliga a mirar de cerca cómo evoluciona todo. Cuando analizamos esto, nos damos cuenta de que hay mucho más bajo la superficie. La conexión con {keywords_str} resulta evidente cuando lo observamos en detalle.

## Desarrollo y Puntos Claves

En primer lugar, hay que entender el contexto fundamental. No es algo que haya surgido sin precedentes, sino que representa la maduración de ciertas ideas previas. A medida que profundizamos, los patrones se vuelven más claros.

Es importante destacar algunos elementos esenciales:
- La rápida evolución de las herramientas.
- La necesidad de adaptación constante.
- Los desafíos inherentes a la implementación.

## Análisis y Perspectiva

Al evaluar las alternativas, queda claro que no hay una única solución correcta. Depende en gran medida del escenario de uso y de los objetivos específicos que se persigan.

## Conclusión

En definitiva, {topic} representa un paso más en esta dirección. Seguiremos atentos a cómo se desarrolla todo este panorama en los próximos meses. El debate, desde luego, está servido.
"""
