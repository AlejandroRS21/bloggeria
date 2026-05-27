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
    def _build_attribution(blogger_urls: Optional[List[str]]) -> str:
        """Build attribution footer for the post."""
        if not blogger_urls or not blogger_urls[0]:
            return ""
        name = ContentGenerator._extract_blogger_name(blogger_urls)
        url = blogger_urls[0].strip().rstrip("/")
        return f"\n\n---\n\n*✍️ Este post fue escrito emulando el estilo de [{name}]({url}).*"

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

        Returns:
            Draft content as markdown string
        """
        profile = style_profile or self.style_profile or {}

        if not self.llm or not self.llm.is_available():
            return self._fallback_draft(topic, keywords, profile)

        keywords_str = ", ".join(keywords[:10]) if keywords else ""

        # Build a rich style context block from the full profile
        style_context = self._build_style_context(profile, blogger_urls)

        # Build attribution footer
        attribution = self._build_attribution(blogger_urls)

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
            prompt = f"""Abajo tienes posts REALES escritos por {blogger_name}, cuyo estilo de escritura tienes que imitar fielmente, e información factual sobre el tema del post.

━━━━━━ EJEMPLOS DEL BLOGGER ORIGINAL ────────
{sample_text[:20000]}
━━━━━━ FIN DE LOS EJEMPLOS ──────────────────
{research_block}
Ahora escribe un NUEVO post sobre: {topic}

{style_context}

REGLAS:

- ### IDIOMA — español REAL, nada de Spanglish
  - Escribe TODO el post en ESPAÑOL. Título, cuerpo, secciones, TODO.
  - Traduce cualquier término técnico: "Machine Learning" → "Aprendizaje Automático", "Deep Learning" → "Aprendizaje Profundo", "Neural Networks" → "Redes Neuronales", "Data Science" → "Ciencia de Datos", "Data Preprocessing" → "Preprocesamiento de Datos", "Model Training" → "Entrenamiento de Modelos".
  - NO dejes NINGUNA palabra en inglés suelta. Nada de "on-line", "performance", "disappointing resultado". TODO traducido.
  - Usa vocabulario español real, no inventes palabras ("alcanceado" → "alcanzado", "percaté" → "me di cuenta").

- ### GRAMÁTICA y ortografía
  - Usa tildes correctamente (empecé, percaté, está, cómo, así).
  - Respeta la concordancia de género y número ("estos temas", no "estas temas").
  - No inventes palabras. Si no estás seguro de una palabra, usa un sinónimo conocido.

- ### REGISTRO — voz y dialecto consistentes con el blogger original
  - Identifica el dialecto del blogger a partir de su perfil de estilo y los ejemplos reales.
  - Si el blogger es de España (tuteo, expresiones como "mazo", "brutal", "o sea"), escribe TODO el post en español peninsular (tú, tienes, fíjate, etc.).
  - Si el blogger es de Argentina/Uruguay (voseo), usa voseo (vos, tenés, pensá, etc.).
  - NUNCA mezcles dialectos o pronombres (por ejemplo, no mezcles "tú tienes" con "pensá" o "¿entendés?"). El post (incluyendo el título) debe sonar 100% coherente al origen del blogger.
  - Elige UN registro (formal o informal) congruente con el blogger y mantenlo todo el post.
  - Evita el registro formal a menos que el blogger lo use de forma explícita.

- ### TÍTULO PRINCIPAL — formato correcto
  - La PRIMERA LÍNEA del post debe ser EXACTAMENTE: `# <título gancho>`
  - Usa el formato markdown `# ` al inicio. NO uses `━━━ title: ... ━━━` ni `Title: ...` ni mayúsculas decorativas.
  - El título debe ser UN GANCHO: datos concretos, afirmaciones audaces, o contrastes impactantes.
  - El título debe seguir estrictamente el dialecto del blogger. Si el blogger es de España, el título NO debe llevar acentuación de voseo (ej: usa "esperas" en lugar de "esperás").
  - Ejemplos BUENOS: `# Los 634 segundos que casi vacían la cartera de un programador`, `# El truco sucio de las academias que prometen programadores en 3 meses`.
  - Ejemplos MALOS (NUNCA uses estos): títulos en inglés, preguntas tipo "¿Es X realmente Y?", títulos genéricos como "Análisis de X".

- ### CONTENIDO y estructura
  - BÁSATE EN LA INFORMACIÓN REAL proporcionada arriba. No inventes datos.
  - NUNCA uses citas académicas en formato numérico entre corchetes (ej: [1], [2], [1, 2], [3]). Escribe de forma fluida y narrativa (ej: "según explica X...", "como se comenta en Y...").
  - Filtra y omite detalles trágicos sobre guerras, víctimas civiles o crímenes de guerra del contexto de investigación, a menos que el tema sea militar o geopolítico. Enfócate estrictamente en los aspectos tecnológicos o de opinión general acordes al blogger.
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
            prompt = f"""{research_block}
Escribe un post de blog imitando el estilo de {blogger_name}. Abajo está su perfil de estilo.

Tema: {topic}

{style_context}

REGLAS:

- ### IDIOMA — español REAL, nada de Spanglish
  - Escribe TODO el post en ESPAÑOL. Título, cuerpo, secciones, TODO.
  - Traduce cualquier término técnico: "Machine Learning" → "Aprendizaje Automático", "Deep Learning" → "Aprendizaje Profundo", "Neural Networks" → "Redes Neuronales", "Data Science" → "Ciencia de Datos", etc.
  - NO dejes NINGUNA palabra en inglés suelta. TODO traducido.
  - Usa vocabulario español real, no inventes palabras.

- ### GRAMÁTICA y ortografía
  - Usa tildes correctamente (empecé, percaté, está, cómo, así).
  - Respeta la concordancia de género y número.
  - No inventes palabras. Usa sinónimos conocidos.

- ### REGISTRO — voz y dialecto consistentes con el blogger original
  - Identifica el dialecto del blogger a partir de su perfil de estilo.
  - Si el blogger es de España (tuteo, expresiones como "mazo", "brutal", "o sea"), escribe TODO el post en español peninsular (tú, tienes, fíjate, etc.).
  - Si el blogger es de Argentina/Uruguay (voseo), usa voseo (vos, tenés, pensá, etc.).
  - NUNCA mezcles dialectos o pronombres (por ejemplo, no mezcles "tú tienes" con "pensá" o "¿entendés?"). El post (incluyendo el título) debe sonar 100% coherente al origen del blogger.
  - Elige UN registro (formal o informal) congruente con el blogger y mantenlo todo el post.
  - Evita el registro formal a menos que el blogger lo use de forma explícita.

- ### TÍTULO PRINCIPAL — formato correcto
  - La PRIMERA LÍNEA debe ser EXACTAMENTE: `# <título gancho>`
  - Usa formato markdown `# `. NO uses `━━━ title:` ni `Title:` ni mayúsculas decorativas.
  - El título debe ser UN GANCHO: datos concretos, afirmaciones audaces.
  - El título debe seguir estrictamente el dialecto del blogger. Si el blogger es de España, el título NO debe llevar acentuación de voseo (ej: usa "esperas" en lugar de "esperás").
  - NUNCA uses títulos en inglés ni preguntas tipo "¿Es X realmente Y?".

- ### CONTENIDO y calidad
  - BÁSATE EN LA INFORMACIÓN REAL. No inventes datos.
  - NUNCA uses citas en formato numérico entre corchetes (ej: [1], [2], [1, 2], [3]). Escribe de forma fluida y narrativa (ej: "según explica X...", "como se comenta en Y...").
  - Filtra y omite detalles trágicos sobre guerras, víctimas civiles o crímenes de guerra del contexto de investigación, a menos que el tema sea militar o geopolítico. Enfócate estrictamente en los aspectos tecnológicos o de opinión general acordes al blogger.
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
                system_prompt="Eres un escritor de blogs profesional. Escribes posts como lo haría el blogger real: con voz propia, estructura orgánica, y respetando fielmente su estilo lingüístico y dialecto original sin caer en modismos que no correspondan.",
                user_prompt=prompt,
            )

            response = self.llm.chat_completion(messages, temperature=0.9, max_tokens=4000)

            return response.content

        except Exception as e:
            print(f"Warning: Content generation failed: {e}. Using fallback.")
            return self._fallback_draft(topic, keywords, profile)

    def refine_content(
        self, draft: str, critique_feedback: Dict[str, Any], style_profile: Dict[str, Any]
    ) -> str:
        """
        Refine content based on critique feedback.

        Args:
            draft: Original draft
            critique_feedback: Feedback from CriticAgent
            style_profile: Style profile for reference

        Returns:
            Refined content
        """
        if not self.llm or not self.llm.is_available():
            return draft  # Return original if no LLM available

        suggestions = critique_feedback.get("suggestions", [])
        suggestions_str = "\\n".join(f"- {s}" for s in suggestions)

        prompt = f"""Refine this blog post based on the critique feedback.

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

Provide the refined version in markdown format."""

        try:
            messages = self.llm.create_messages(
                system_prompt="You are an editor helping improve blog posts while maintaining the author's unique voice.",
                user_prompt=prompt,
            )

            response = self.llm.chat_completion(messages, temperature=0.7, max_tokens=3500)

            return response.content

        except Exception as e:
            print(f"Warning: Refinement failed: {e}. Returning original draft.")
            return draft

    def _fallback_draft(
        self, topic: str, keywords: list = None, style_profile: Dict[str, Any] = None
    ) -> str:
        """Generate a basic draft when LLM is not available."""
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
