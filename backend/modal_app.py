"""
Modal deployment for Blogger Agent TFG.

This module deploys the BloggerOrchestrator as a serverless function on Modal.
It provides webhook endpoints for generating blog posts that mimic a blogger's style.

Usage:
    modal deploy backend/modal_app.py
    
Then call the webhook:
    POST https://[your-app]--blogger-agent.modal.run
    {
        "blogger_urls": ["https://javipas.com/post1", "https://javipas.com/post2"],
        "topic": "Las mejores prácticas para desarrollar APIs REST con Python"
    }
"""

import modal
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Create Modal app
app = modal.App("blogger-agent-tfg")

# Supabase project the frontend reads from (REQ-2). Writes to any other
# project are rejected, never silent.
EXPECTED_SUPABASE_PROJECT_ID = "stqtpbdzqgcbaqdvrsij"

backend_dir = os.path.dirname(__file__)

# Create Docker image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements(os.path.join(backend_dir, "requirements.txt"))
    .apt_install("git")  # For potential git operations
    .pip_install("google-genai")
    .add_local_dir(os.path.join(backend_dir, "src"), remote_path="/root/src")
    .add_local_dir(os.path.join(backend_dir, "tools"), remote_path="/root/tools")
    .add_local_dir(os.path.join(backend_dir, "aphra_blogger"), remote_path="/root/aphra_blogger")
    .add_local_file(os.path.join(backend_dir, "cleanup_supabase.py"), remote_path="/root/cleanup_supabase.py")
)

# Define secrets (will need to be configured in Modal dashboard)
# modal secret create openai-secret OPENAI_API_KEY=sk-...
# modal secret create hf-secret HF_TOKEN=hf_...
# modal secret create brave-secret BRAVE_API_KEY=BSACc5UYx490dRN2WCRaIimxw59Ao7A
# modal secret create supabase-secret SUPABASE_URL=... SUPABASE_SERVICE_KEY=... SUPABASE_ANON_KEY=...

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("openai-secret"),
        modal.Secret.from_name("huggingface-secret"),
        modal.Secret.from_name("gemini-secret"),
        modal.Secret.from_name("brave-secret"),
        modal.Secret.from_name("unsplash-secret"),
    ],
    timeout=600,  # 10 minutes max
    memory=2048,  # 2GB RAM
)
def generate_blog_post(
    blogger_urls: List[str],
    topic: str,
    enable_critique: bool = True,
    min_word_count: int = 800,
    max_word_count: int = 2500,
    provider: str = "gemini",
    language: str = "auto",
) -> Dict[str, Any]:
    """
    Generate a blog post that mimics the style of the given blogger.
    
    This function orchestrates all agents to:
    1. Analyze the blogger's writing style
    2. Extract keywords and patterns
    3. Generate content with that style
    4. Critique and refine the content
    5. Build HTML/JSX structure
    6. Select image placement prompts
    
    Args:
        blogger_urls: List of URLs from the blogger to analyze
        topic: Topic to write about
        enable_critique: Whether to enable critique phase (default: True)
        min_word_count: Minimum words for generated content (default: 800)
        max_word_count: Maximum words for generated content (default: 2500)
        provider: LLM provider to use ("huggingface", "openai", "auto")
        language: "auto" (explicit > style_profile > "es"), "es" or "en"
        
    Returns:
        Dict with complete blog post data
    """
    # Ensure /root is in sys.path so the mounts can be resolved
    import sys
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
        
    # Import here to avoid loading during image build
    from src.orchestrator.main import BloggerOrchestrator
    from src.orchestrator.config import OrchestratorConfig
    
    # Configure orchestrator
    config = OrchestratorConfig(
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        huggingface_token=os.environ.get("HF_TOKEN"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY"),
        provider=provider,
        enable_critique=enable_critique,
        min_word_count=min_word_count,
        max_word_count=max_word_count,
        verbose=True,
    )
    
    # Create orchestrator
    orchestrator = BloggerOrchestrator(config=config, verbose=True)
    
    # Run the workflow
    result = orchestrator.run(
        topic=topic,
        blogger_urls=blogger_urls,
        language=language,
        output_path=None,  # Don't save to file in serverless
    )
    
    return result


def _normalize_language(language: Any) -> str:
    """Normalize a webhook language value to es|en|auto (REQ-6).

    Invalid or missing values fall back to "auto" — the webhook NEVER rejects
    a request because of a bad language value.
    """
    if language in ("es", "en", "auto"):
        return language
    return "auto"


def _extract_language(data: Dict[str, Any]) -> str:
    """Extract and normalize the optional language param from a payload."""
    return _normalize_language(data.get("language", "auto"))


def _parse_moderation_response(text: str) -> Dict[str, Any]:
    """Parse JSON moderation response from LLM output."""
    import json
    import re
    json_match = re.search(r'\{[^}]+\}', text.strip())
    if json_match:
        try:
            result = json.loads(json_match.group())
            return {
                "approved": result.get("approved", True),
                "reason": result.get("reason"),
            }
        except json.JSONDecodeError:
            pass
    return {"approved": True, "reason": None}


_MODERATION_SYSTEM_PROMPT = """Eres un moderador de contenido. Debes determinar si el siguiente TEMA es apropiado para generar un artículo de blog profesional.

Un tema INAPROPIADO incluye:
- Contenido explícitamente sexual o pornográfico
- Violencia extrema, gore o crueldad gratuita
- Discurso de odio, discriminación, racismo, xenofobia, homofobia
- Denigración o humillación de personas o grupos por su origen, género, religión, orientación sexual, discapacidad
- Contenido ilegal o que promueva actividades ilegales (drogas, armas, terrorismo)
- Acoso, bullying o intimidación
- Autolesiones, trastornos alimenticios, suicidio
- Spam, desinformación maliciosa o teorías conspirativas dañinas
- Contenido que promueva la violencia de género o normalice el abuso

Un tema APROPIADO incluye (incluso si es polémico, siempre que el enfoque sea serio e informativo):
- Tecnología, ciencia, cultura, educación, historia
- Noticias y actualidad tratadas con respeto y rigor
- Opinión y análisis profesional
- Política, economía, sociedad (con enfoque analítico, no incitador)
- Salud, bienestar, deportes
- Entretenimiento y cultura pop
- Cualquier tema tratado desde una perspectiva INFORMATIVA y RESPETUOSA

IMPORTANTE: No rechaces un tema solo porque sea controvertido. Recházalo SOLO si su contenido intrínseco es denigrante, explícito, ilegal o promueve el odio."""


def _moderate_with_modal(topic: str) -> Optional[Dict[str, Any]]:
    """Try moderation using the Modal-hosted model. Returns None if unavailable."""
    user_prompt = f"""TEMA A EVALUAR: "{topic}"

Responde ÚNICAMENTE con un JSON válido, sin texto adicional:
- Si es APROPIADO: {{"approved": true, "reason": null}}
- Si es INAPROPIADO: {{"approved": false, "reason": "explicación clara y específica de por qué es inapropiado"}}"""

    try:
        # Call Modal-hosted model directly — works inside Modal's runtime
        # without needing explicit tokens (Modal handles auth internally)
        RemoteCls = modal.Cls.from_name("blogger-agent-models", "LlamaModel")
        instance = RemoteCls()

        response = instance.generate.remote(
            messages=[
                {"role": "system", "content": _MODERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=200,
        )

        text = ""
        if isinstance(response, dict):
            text = response.get("content", "")
        else:
            text = str(response)

        result = _parse_moderation_response(text)
        print(f"[Moderation] Modal verdict: approved={result.get('approved')}")
        return result

    except Exception as e:
        print(f"[Moderation] Modal model unavailable: {e}")
        return None


def _moderate_with_gemini(topic: str) -> Optional[Dict[str, Any]]:
    """Fallback moderation using Gemini. Returns None if unavailable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(api_key=api_key)

        user_prompt = f"""TEMA A EVALUAR: "{topic}"

Responde ÚNICAMENTE con un JSON válido, sin texto adicional:
- Si es APROPIADO: {{"approved": true, "reason": null}}
- Si es INAPROPIADO: {{"approved": false, "reason": "explicación clara y específica de por qué es inapropiado"}}"""

        config = genai_types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=200,
            system_instruction=_MODERATION_SYSTEM_PROMPT,
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=config,
        )

        text = response.text or ""
        result = _parse_moderation_response(text)
        print(f"[Moderation] Gemini verdict: approved={result.get('approved')}")
        return result

    except ImportError:
        print("[Moderation] google-genai not available")
        return None
    except Exception as e:
        print(f"[Moderation] Gemini error: {e}")
        return None


def moderate_topic(topic: str) -> Dict[str, Any]:
    """
    Check if a topic is appropriate for content generation.

    Uses the Modal-hosted LLM as the primary moderation engine.
    Falls back to Gemini if the Modal model is unavailable.
    Topics containing explicit, violent, hateful, or degrading content are rejected.

    Args:
        topic: The topic string to moderate.

    Returns:
        Dict with:
            - approved (bool): True if topic is safe
            - reason (str | None): Explanation if rejected, None if approved
    """
    # Strategy 1: Modal-hosted model (primary, runs inside Modal infra)
    print(f"[Moderation] Checking topic: '{topic[:60]}{'...' if len(topic) > 60 else ''}'")
    result = _moderate_with_modal(topic)
    if result is not None:
        return result

    # Strategy 2: Gemini API (fallback)
    result = _moderate_with_gemini(topic)
    if result is not None:
        return result

    # Both unavailable → fail open, allow through
    print("[Moderation] No moderation provider available, allowing through")
    return {"approved": True, "reason": None}


def supabase_project_id(url: str) -> str | None:
    """Extract the Supabase project ID from a SUPABASE_URL origin.

    Supabase URLs are https://<project-id>.supabase.co, so the project ID
    is the first label of the netloc. Returns None for unparseable values.
    """
    try:
        return urlparse(url).netloc.split(".")[0] or None
    except ValueError:
        return None


def persist_post(
    sb: Any,
    post_data: dict[str, Any],
    resolved_project: str | None,
) -> dict[str, Any]:
    """Upsert a generated post, rejecting writes to a mismatched project.

    REQ-2: never write silently to a different Supabase project; a mismatch
    logs both project IDs and returns success:false.
    REQ-4: log an explicit outcome — success with the inserted row id, or
    failure with the error detail. Insert failures are never silent.
    """
    if resolved_project != EXPECTED_SUPABASE_PROJECT_ID:
        error = (
            "Supabase project mismatch: supabase-secret resolves to "
            f"'{resolved_project}', expected '{EXPECTED_SUPABASE_PROJECT_ID}'. "
            "Write rejected to prevent silent writes to the wrong project."
        )
        print(f"[Webhook] REJECTED write: {error}")
        return {"success": False, "error": error}

    try:
        sb.table("posts").upsert(post_data).execute()
        print(f"[Webhook] Upsert success: id={post_data.get('id')} status=success")
        return {"success": True}
    except Exception as db_err:
        print(f"[Webhook] Upsert FAILED: {db_err}")
        return {"success": False, "error": f"DB insert failed: {db_err}"}


def _map_to_supabase(
    result: Dict[str, Any], blogger_name: Optional[str] = None
) -> Dict[str, Any]:
    """Map the orchestrator result dict to the Supabase posts schema."""
    metadata = result.get("html_structure", {}).get("metadata", {})
    workflow_id = result.get("workflow_id", "")
    base_slug = metadata.get("slug") or workflow_id
    short_id = workflow_id[:6] if workflow_id else "post"
    # Añadimos un sufijo para evitar errores de restricción UNIQUE en supabase
    unique_slug = f"{base_slug}-{short_id}"
    
    # Obtener primera imagen del contenido para cover_image_url
    content_html = result.get("html_structure", {}).get("html", "")
    cover_img = None
    img_match = re.search(r'<img[^>]+src="([^"]+)"', content_html)
    if img_match:
        cover_img = img_match.group(1)
    
    # Atribución de estilo (REQ-2): blogger_name explícito > heurística desde
    # la primera URL > None. Reutiliza ContentGenerator en modo solo lectura
    # (REQ-8: content_generator.py queda intacto).
    blogger_urls = result.get("blogger_urls") or []
    style_source_url = blogger_urls[0] if blogger_urls else None
    style_source = None
    if style_source_url:
        if blogger_name:
            style_source = blogger_name
        else:
            from aphra_blogger.agents.content_generator import ContentGenerator
            style_source = ContentGenerator._extract_blogger_name(blogger_urls)
    
    return {
        "id": workflow_id,
        "slug": unique_slug,
        "title": metadata.get("title") or result.get("title", "Sin título"),
        "description": metadata.get("description", ""),
        "content": content_html,
        "author": "Blogger Agent",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "word_count": metadata.get("word_count"),
        "reading_time": metadata.get("reading_time"),
        "keywords": result.get("keywords", []),
        "tags": metadata.get("keywords", []),
        "cover_image_url": cover_img,
        "style_source": style_source,
        "style_source_url": style_source_url,
    }


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("openai-secret"),
        modal.Secret.from_name("supabase-secret"),
        modal.Secret.from_name("gemini-secret"),
    ],
)
@modal.fastapi_endpoint(method="POST")
def webhook(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Webhook endpoint for generating blog posts.
    
    This is the main entry point for external requests.
    
    Request body:
    {
        "blogger_urls": ["url1", "url2", ...],
        "topic": "Topic to write about",
        "blogger_name": "Author name", // optional (REQ-3)
        "enable_critique": true,  // optional
        "min_word_count": 800,    // optional
        "max_word_count": 2500,   // optional
        "provider": "huggingface" // optional
    }
    
    Response:
    {
        "success": true,
        "data": {
            // Complete blog post data (see generate_blog_post return)
        },
        "error": null
    }
    
    Or on error:
    {
        "success": false,
        "data": null,
        "error": "Error message"
    }
    """
    try:
        # Validate required fields
        if "blogger_urls" not in data:
            return {
                "success": False,
                "data": None,
                "error": "Missing required field: blogger_urls"
            }
        
        if "topic" not in data:
            return {
                "success": False,
                "data": None,
                "error": "Missing required field: topic"
            }
        
        # Extract parameters
        blogger_urls = data["blogger_urls"]
        topic = data["topic"]
        enable_critique = data.get("enable_critique", True)
        min_word_count = data.get("min_word_count", 800)
        max_word_count = data.get("max_word_count", 2500)
        provider = data.get("provider", "gemini")
        language = _extract_language(data)
        
        # Validate types
        if not isinstance(blogger_urls, list):
            return {
                "success": False,
                "data": None,
                "error": "blogger_urls must be a list"
            }
        
        if not isinstance(topic, str):
            return {
                "success": False,
                "data": None,
                "error": "topic must be a string"
            }

        # Atribución de estilo (REQ-3): blogger_name opcional y string
        blogger_name = data.get("blogger_name")
        if blogger_name is not None and not isinstance(blogger_name, str):
            return {
                "success": False,
                "data": None,
                "error": "blogger_name must be a string"
            }
        
        # ── Content Moderation ────────────────────────────────────────────
        moderation = moderate_topic(topic)
        if not moderation.get("approved", True):
            reason = moderation.get("reason", "Tema no apto para generación de contenido")
            print(f"[Webhook] Topic REJECTED by moderator: {reason}")
            return {
                "success": False,
                "data": None,
                "error": f"⛔ Tema rechazado por protección de contenido: {reason}"
            }
        print(f"[Webhook] Topic approved by moderator ✓")
        # ──────────────────────────────────────────────────────────────────
        
        # Call the generator
        result = generate_blog_post.remote(
            blogger_urls=blogger_urls,
            topic=topic,
            enable_critique=enable_critique,
            min_word_count=min_word_count,
            max_word_count=max_word_count,
            provider=provider,
            language=language,
        )

        # ── Persist to Supabase (REQ-2: fail loudly on project mismatch) ──
        supabase_url = os.environ.get("SUPABASE_URL", "")
        resolved_project = supabase_project_id(supabase_url)
        # Startup log: resolved SUPABASE_URL origin + target project id
        print(f"[Webhook] supabase URL origin: {urlparse(supabase_url).netloc or '(empty)'}")
        print(f"[Webhook] supabase project: {resolved_project or 'UNKNOWN'}")
        try:
            from supabase import create_client
            sb = create_client(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_SERVICE_KEY"],
            )
            post_data = _map_to_supabase(result, blogger_name=blogger_name)
        except Exception as db_err:
            print(f"[Webhook] DB init failed: {db_err}")
            return {
                "success": False,
                "data": None,
                "error": f"DB insert failed: {db_err}",
            }

        outcome = persist_post(sb, post_data, resolved_project)
        if not outcome["success"]:
            return {
                "success": False,
                "data": None,
                "error": outcome["error"],
            }

        return {
            "success": True,
            "data": {"slug": post_data["slug"]},
            "error": None,
        }
        
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("openai-secret")],
)
def scrape_blogger_corpus(
    blog_url: str,
    max_posts: int = 30,
    delay: float = 1.0,
) -> Dict[str, Any]:
    """
    Scrape a blogger's posts to build a corpus.
    
    This is a helper function for building the initial corpus
    without needing to generate a post.
    
    Args:
        blog_url: Base URL of the blog to scrape
        max_posts: Maximum number of posts to scrape (default: 30)
        delay: Delay between requests in seconds (default: 1.0)
        
    Returns:
        Dict with scraped posts:
        {
            "posts": [...],
            "metadata": {...}
        }
    """
    # Ensure /root is in sys.path so the mounts can be resolved
    import sys
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
        
    from tools.scraper import BlogScraper
    
    scraper = BlogScraper(
        base_url=blog_url,
        max_posts=max_posts,
        delay=delay,
    )
    
    posts = scraper.scrape_blog()
    
    return {
        "posts": posts,
        "metadata": {
            "count": len(posts),
            "source": blog_url,
            "max_requested": max_posts,
        }
    }


def _run_daily_cleanup(dry_run: bool = True):
    """Run the cleanup cron against the DB.

    Scheduled runs default to DRY-RUN (REQ-1): posts are evaluated and
    what-would-be-deleted is logged, but nothing is deleted. Real deletion
    requires an explicit opt-in via dry_run=False.
    """
    import sys
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")

    from cleanup_supabase import cleanup_posts

    mode = "DRY RUN" if dry_run else "REAL DELETE"
    print(f"[DailyCleanup] {mode} — deletion requires explicit dry_run=False opt-in")
    cleanup_posts(keep_limit=100, quality_check=True, dry_run=dry_run)
    print("[DailyCleanup] finished.")


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("supabase-secret")],
    schedule=modal.Cron("0 0 * * *"),  # Runs every day at midnight
)
def daily_cleanup(dry_run: bool = True):
    """
    Scheduled task to clean up old posts.

    By default it runs in DRY-RUN mode (REQ-1): it keeps the 100 most recent
    posts, evaluates quality, and only logs what would be deleted.
    Real deletion requires an explicit opt-in:
    daily_cleanup.remote(dry_run=False)
    """
    _run_daily_cleanup(dry_run=dry_run)
