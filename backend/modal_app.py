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

import os
import re
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import modal

from src.orchestrator.safety import (
    SafetyAgent,
    check_deterministic,
    log_moderation_event,
    sanitize_html,
)

# Create Modal app
app = modal.App("blogger-agent-tfg")

# Supabase project the frontend reads from (REQ-2). Writes to any other
# project are rejected, never silent.
EXPECTED_SUPABASE_PROJECT_ID = "stqtpbdzqgcbaqdvrsij"

# ── Queue, Concurrency, and Rate Limit Configuration ───────────────
MAX_CONCURRENT_GENERATIONS = int(os.environ.get("MAX_CONCURRENT_GENERATIONS", "2"))
RATE_LIMIT_MAX_PER_HOUR = int(os.environ.get("RATE_LIMIT_MAX_PER_HOUR", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "3600"))
JOB_STALE_TIMEOUT_SECONDS = int(os.environ.get("JOB_STALE_TIMEOUT_SECONDS", "7200"))


def _get_queue():
    import modal
    return modal.Queue.from_name("blogger-job-queue", create_if_missing=True)


def _get_job_store():
    import modal
    return modal.Dict.from_name("blogger-jobs", create_if_missing=True)


def _get_rate_store():
    import modal
    return modal.Dict.from_name("blogger-rate-limit", create_if_missing=True)


# ── In-memory fallbacks for local/webhook.local() runs ─────────────
# When no FastAPI Request is present (unit tests, local debugging) the
# webhook MUST NOT touch Modal cloud state: queue/store are process-local
# so tests stay deterministic and offline.
class _MemoryQueue:
    def __init__(self):
        self._items = deque()

    def put(self, item):
        self._items.append(item)

    def get(self, block=False):
        if not self._items:
            raise IndexError("empty")
        return self._items.popleft()

    def __len__(self):
        return len(self._items)

    def len(self):
        return len(self._items)


_MEMORY_QUEUE = None
_MEMORY_STORE: Dict[str, Any] = {}


def _memory_queue() -> Any:
    global _MEMORY_QUEUE
    if _MEMORY_QUEUE is None:
        _MEMORY_QUEUE = _MemoryQueue()
    return _MEMORY_QUEUE


def _memory_store() -> Dict[str, Any]:
    return _MEMORY_STORE


def _client_ip(request: Any) -> Optional[str]:
    """Extract client IP from FastAPI Request (supports X-Forwarded-For)."""
    if not request:
        return None
    client = getattr(request, "client", None)
    if client and getattr(client, "host", None):
        return client.host
    headers = getattr(request, "headers", {}) or {}
    xff = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For")
    if xff and isinstance(xff, str):
        return xff.split(",")[0].strip()
    return None


def _rate_limited(
    ip: Optional[str],
    store: Any = None,
    max_reqs: Optional[int] = None,
    window: Optional[int] = None,
) -> bool:
    """Check and update IP rate limit. Returns True if request exceeds threshold."""
    if not ip:
        return False
    store = store if store is not None else _get_rate_store()
    max_reqs = max_reqs if max_reqs is not None else RATE_LIMIT_MAX_PER_HOUR
    window = window if window is not None else RATE_LIMIT_WINDOW_SECONDS
    now = datetime.now().timestamp()
    history = list(store.get(ip, []))
    fresh = [t for t in history if now - t < window]
    if len(fresh) >= max_reqs:
        return True
    fresh.append(now)
    store[ip] = fresh
    return False


def _mark_job(
    job_id: str,
    status: str,
    store: Any = None,
    ip: Optional[str] = None,
    error: Optional[str] = None,
):
    """Record job lifecycle state in Modal Dict and best-effort Supabase status entry."""
    if not job_id:
        return
    store = store if store is not None else _get_job_store()
    existing = store.get(job_id, {})
    store[job_id] = {
        "status": status,
        "updated_at": datetime.now().timestamp(),
        "ip": ip or existing.get("ip"),
        "error": error if error is not None else existing.get("error"),
    }
    _mark_job_supabase(job_id, status, error=error or existing.get("error"))


def _mark_job_supabase(job_id: str, status: str, error: Optional[str] = None):
    """Sync job status to Supabase posts table if env credentials are set."""
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not supabase_url or not supabase_key or not job_id:
        return
    try:
        resolved_project = supabase_project_id(supabase_url)
        if resolved_project != EXPECTED_SUPABASE_PROJECT_ID:
            return
        from supabase import create_client
        sb = create_client(supabase_url, supabase_key)
        # Check if record already exists for job_id
        res = sb.table("posts").select("id, slug").eq("job_id", job_id).execute()
        existing_rows = res.data if res else []
        if existing_rows:
            target_id = existing_rows[0]["id"]
            update_data: Dict[str, Any] = {"status": status}
            if error:
                update_data["error_message"] = str(error)
            sb.table("posts").update(update_data).eq("id", target_id).execute()
        elif status == "failed":
            # For failed jobs with no existing post row, insert a stub post row so frontend polling finds the failure
            stub_data = {
                "id": f"failed-{job_id}",
                "job_id": job_id,
                "slug": f"failed-{job_id}",
                "title": "Generación fallida",
                "content": "",
                "author": "Blogger Agent",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "status": "failed",
                "error_message": str(error or "Error desconocido en el backend"),
            }
            sb.table("posts").upsert(stub_data).execute()
    except Exception as db_err:
        print(f"[_mark_job_supabase] Failed to update job status in Supabase: {db_err}")


def _get_running_count(store: Any = None) -> int:
    """Count non-stale running jobs in the job store."""
    store = store if store is not None else _get_job_store()
    now = datetime.now().timestamp()
    count = 0
    try:
        keys = list(store.keys())
    except Exception:
        return 0
    for k in keys:
        item = store.get(k, {})
        if item.get("status") == "running":
            updated_at = item.get("updated_at", 0)
            if now - updated_at <= JOB_STALE_TIMEOUT_SECONDS:
                count += 1
    return count


def _is_job_active(job_id: str, store: Any = None) -> bool:
    """Check if a job_id is currently queued or running to prevent duplicate jobs."""
    if not job_id:
        return False
    store = store if store is not None else _get_job_store()
    item = store.get(job_id)
    if not item or not isinstance(item, dict):
        return False
    status = item.get("status")
    if status in ("queued", "running"):
        return True
    if status == "done":
        now = datetime.now().timestamp()
        updated_at = item.get("updated_at", 0)
        if now - updated_at < 60:
            return True
    return False


def _use_memory_backend(request: Any) -> bool:
    """Process-local state when no FastAPI Request OR running in local mode.

    Unit tests and webhook.local() runs must never touch Modal cloud state;
    only deployed (non-local) invocations use the real cloud queue/dicts.
    """
    if request is None:
        return True
    try:
        import modal
        return bool(modal.is_local())
    except Exception:
        return True


def enqueue_job(
    payload: Dict[str, Any],
    ip: Optional[str] = None,
    queue: Any = None,
    store: Any = None,
):
    """Enqueues a generation payload into the Modal Queue and updates job status."""
    queue = queue if queue is not None else _get_queue()
    job_id = payload.get("job_id")
    if job_id:
        _mark_job(job_id, "queued", store=store, ip=ip)
    queue.put(payload)


def _prune_done_jobs(store: Any = None, ttl: float = JOB_STALE_TIMEOUT_SECONDS) -> int:
    """Remove done job entries older than the TTL to bound store memory."""
    store = store if store is not None else _get_job_store()
    now = datetime.now().timestamp()
    pruned = 0
    try:
        keys = list(store.keys())
    except Exception:
        return 0
    for k in keys:
        item = store.get(k, {})
        if isinstance(item, dict) and item.get("status") == "done":
            if now - item.get("updated_at", 0) > ttl:
                try:
                    del store[k]
                    pruned += 1
                except Exception:
                    pass
    return pruned


def _drain_once(
    queue: Any = None,
    job_store: Any = None,
    spawner: Any = None,
    max_conc: Optional[int] = None,
) -> int:
    """Process up to available capacity from the FIFO queue."""
    queue = queue if queue is not None else _get_queue()
    job_store = job_store if job_store is not None else _get_job_store()
    _prune_done_jobs(job_store, ttl=JOB_STALE_TIMEOUT_SECONDS)
    if spawner is None:
        spawner = generate_blog_post.spawn
    max_conc = max_conc if max_conc is not None else MAX_CONCURRENT_GENERATIONS

    running = _get_running_count(job_store)
    available_slots = max(0, max_conc - running)
    drained = 0

    for _ in range(available_slots):
        try:
            payload = queue.get(block=False)
        except Exception:
            break
        if not payload or not isinstance(payload, dict):
            continue
        job_id = payload.get("job_id")
        if job_id:
            _mark_job(job_id, "running", store=job_store)
        try:
            spawner(**payload)
            drained += 1
        except Exception as spawn_err:
            print(f"[_drain_once] Failed to spawn job {job_id}: {spawn_err}")
            if job_id:
                _mark_job(job_id, "failed", store=job_store, error=str(spawn_err))

    return drained

backend_dir = os.path.dirname(__file__)

# Create Docker image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements(os.path.join(backend_dir, "requirements.txt"))
    .apt_install("git")  # For potential git operations
    .pip_install("google-genai")
    .add_local_dir(os.path.join(backend_dir, "src"), remote_path="/root/src")
    .add_local_dir(os.path.join(backend_dir, "tools"), remote_path="/root/tools")
    .add_local_dir(os.path.join(backend_dir, "profiles"), remote_path="/root/backend/profiles")
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
        modal.Secret.from_name("supabase-secret"),
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
    job_id: Optional[str] = None,
    blogger_name: Optional[str] = None,
    preset_id: Optional[str] = None,
    blogger_preset_id: Optional[str] = None,
    niche: str = "tech",
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
    from src.orchestrator.config import OrchestratorConfig
    from src.orchestrator.main import BloggerOrchestrator
    
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
    
    resolved_preset_id = preset_id or blogger_preset_id

    workflow_failed = False
    workflow_error = None
    try:
        if job_id:
            _mark_job(job_id, "running")
        # Run the workflow
        result = orchestrator.run(
            topic=topic,
            blogger_urls=blogger_urls,
            language=language,
            output_path=None,  # Don't save to file in serverless
            preset_id=resolved_preset_id,
        )
        
        # ── Content Moderation: validate the COMPLETE generated article ─────
        # before persisting. If unsafe, the post is NOT published (REQ-MOD-1).
        try:
            from src.orchestrator.safety import SafetyAgent, normalize_niche

            niche_key = normalize_niche(niche)
            # Reuse whichever LLM credentials the orchestrator already has.
            llm_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if llm_api_key:
                llm_provider = "gemini" if os.environ.get("GEMINI_API_KEY") else "openai"
                safety = SafetyAgent(api_key=llm_api_key, provider=llm_provider)
                article_check = safety.validate_article(
                    {
                        "title": result.get("title", ""),
                        "description": result.get("html_structure", {}).get("metadata", {}).get("description", ""),
                        "content": result.get("html_structure", {}).get("html", ""),
                    },
                    niche=niche_key,
                )
            else:
                # No LLM available in this runtime: run the deterministic layer only.
                from src.orchestrator.safety import check_deterministic
                article_text = f"{result.get('title', '')} {result.get('html_structure', {}).get('html', '')[:4000]}"
                article_check = check_deterministic(article_text, niche=niche_key) or {
                    "approved": True, "safe": True, "reason": None, "layer": "deterministic_only"
                }

            if not article_check.get("approved", True) and not article_check.get("safe", True):
                reason = article_check.get("reason", "Artículo generado no apto")
                layer = article_check.get("layer", "llm")
                print(f"[generate_blog_post] Article REJECTED by moderator ({layer}): {reason}")
                log_moderation_event("article", reason, layer, niche_key, result.get("title", "")[:120])
                workflow_failed = True
                workflow_error = reason
                return {**result, "moderation": {"approved": False, "reason": reason}}
        except Exception as mod_err:
            # Moderation failure must NEVER block publishing a valid post.
            print(f"[generate_blog_post] Article moderation skipped (non-blocking): {mod_err}")

        # ── Persist to Supabase ──────────────────────────────────────────
        supabase_url = os.environ.get("SUPABASE_URL", "")
        resolved_project = supabase_project_id(supabase_url)
        print(f"[generate_blog_post] supabase URL origin: {urlparse(supabase_url).netloc or '(empty)'}")
        print(f"[generate_blog_post] supabase project: {resolved_project or 'UNKNOWN'}")
        try:
            from supabase import create_client
            sb = create_client(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_SERVICE_KEY"],
            )
            post_data = _map_to_supabase(result, blogger_name=blogger_name, job_id=job_id)
            post_data["status"] = "done"
            # ── Sanitize LLM-generated HTML before publishing (REQ-MOD-5) ──
            post_data["content"] = sanitize_html(post_data.get("content", ""))
            outcome = persist_post(sb, post_data, resolved_project)
            if not outcome["success"]:
                print(f"[generate_blog_post] Failed to persist post: {outcome.get('error')}")
                workflow_failed = True
                workflow_error = outcome.get("error")
        except Exception as db_err:
            print(f"[generate_blog_post] DB persistence failed: {db_err}")
            workflow_failed = True
            workflow_error = str(db_err)

        return result
    except Exception as pipe_err:
        workflow_failed = True
        workflow_error = str(pipe_err)
        raise pipe_err
    finally:
        if job_id:
            try:
                final_status = "failed" if workflow_failed else "done"
                _mark_job(job_id, final_status, error=workflow_error)
                _drain_once()
            except Exception as drain_err:
                print(f"[generate_blog_post] Job completion mark/drain error: {drain_err}")


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


def moderate_topic(topic: str, niche: str = "tech") -> Dict[str, Any]:
    """
    Check if a topic is appropriate for content generation.

    FIRST: deterministic pre-filter (blacklist / PII / spam — free, no LLM).
    Then: Modal-hosted LLM as the primary moderation engine.
    Falls back to Gemini if the Modal model is unavailable.

    Args:
        topic: The topic string to moderate.
        niche: Content niche ("tech", "news", "literature", "food", "gossip").

    Returns:
        Dict with:
            - approved (bool): True if topic is safe
            - safe (bool): Same as approved (backward-compatible alias)
            - reason (str | None): Explanation if rejected, None if approved
    """
    print(f"[Moderation] Checking topic: '{topic[:60]}{'...' if len(topic) > 60 else ''}' (niche={niche})")

    # Strategy 0: Deterministic pre-filter (cheap, no LLM)
    det_result = check_deterministic(topic, niche=niche)
    if det_result is not None:
        print(f"[Moderation] Deterministic REJECTED ({det_result['layer']}): {det_result['reason']}")
        log_moderation_event("topic", det_result["reason"], det_result["layer"], niche, topic)
        return det_result

    # Strategy 1: Modal-hosted model (primary, runs inside Modal infra)
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
    result: Dict[str, Any], blogger_name: Optional[str] = None, job_id: Optional[str] = None
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
            style_source = ContentGenerator._extract_blogger_name(
                blogger_urls,
                style_profile=result.get("style_profile"),
                preset_id=result.get("preset_id"),
            )
    
    return {
        "id": workflow_id,
        "job_id": job_id,
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
def webhook(data: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
    """
    Webhook endpoint for generating blog posts.
    
    This is the main entry point for external requests.
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
        job_id = data.get("job_id")
        
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

        if job_id is not None and not isinstance(job_id, str):
            return {
                "success": False,
                "data": None,
                "error": "job_id must be a string"
            }

        # Atribución de estilo (REQ-3): blogger_name opcional y string
        blogger_name = data.get("blogger_name")
        if blogger_name is not None and not isinstance(blogger_name, str):
            return {
                "success": False,
                "data": None,
                "error": "blogger_name must be a string"
            }

        preset_id = data.get("blogger_preset_id") or data.get("preset_id")
        if preset_id is not None and not isinstance(preset_id, str):
            return {
                "success": False,
                "data": None,
                "error": "blogger_preset_id must be a string"
            }

        # ── Rate-limit check by client IP ─────────────────────────────────
        ip = _client_ip(request)
        # Local runs (webhook.local(), no FastAPI Request) use process-local
        # state so tests are deterministic and never touch Modal cloud.
        use_memory = _use_memory_backend(request)
        queue = _memory_queue() if use_memory else None
        job_store = _memory_store() if use_memory else None
        rate_store = _memory_store() if use_memory else None

        if _rate_limited(ip, store=rate_store):
            print(f"[Webhook] Rate limit exceeded for IP: {ip}")
            return {
                "success": False,
                "data": None,
                "error": "⛔ Límite de tasa excedido (máximo 5 solicitudes/hora por IP). Inténtalo más tarde.",
            }

        # ── Deduplication / Job ID check ─────────────────────────────────
        resolved_job_id = job_id or f"job-{str(uuid.uuid4())[:12]}"
        if _is_job_active(resolved_job_id, store=job_store):
            print(f"[Webhook] Duplicate job_id rejected: {resolved_job_id}")
            return {
                "success": False,
                "data": None,
                "error": f"El job '{resolved_job_id}' ya está en ejecución o completado recientemente.",
            }

        # ── Niche-aware moderation ──────────────────────────────────────
        from src.orchestrator.safety import normalize_niche
        from src.orchestrator.bloggers_registry import get_prebaked_profile

        blogger_niche = None
        lookup_target = preset_id or (blogger_urls[0] if isinstance(blogger_urls, list) and blogger_urls else None)
        if lookup_target:
            try:
                blogger = get_prebaked_profile(lookup_target)
                if blogger and blogger.get("niche"):
                    blogger_niche = normalize_niche(blogger["niche"])
            except Exception:
                pass

        request_niche = normalize_niche(data.get("niche", "tech"))
        if blogger_niche:
            niche = blogger_niche
            if request_niche != blogger_niche:
                print(f"[Niche Warning] Request niche '{request_niche}' diverges from blogger preset niche '{blogger_niche}'. Using blogger niche '{blogger_niche}'.")
        else:
            niche = request_niche

        # ── Content Moderation ────────────────────────────────────────────
        moderation = moderate_topic(topic, niche=niche)
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
        
        # Enqueue payload into FIFO queue
        payload = {
            "blogger_urls": blogger_urls,
            "topic": topic,
            "enable_critique": enable_critique,
            "min_word_count": min_word_count,
            "max_word_count": max_word_count,
            "provider": provider,
            "language": language,
            "job_id": resolved_job_id,
            "blogger_name": blogger_name,
            "preset_id": preset_id,
            "niche": niche,
        }
        enqueue_job(payload, ip=ip, queue=queue, store=job_store)

        # Opportunistic drain: process immediately if under concurrency capacity
        try:
            _drain_once(queue=queue, job_store=job_store)
        except Exception as drain_err:
            print(f"[Webhook] Opportunistic drain failed (non-blocking): {drain_err}")

        return {
            "success": True,
            "job_id": resolved_job_id,
            "status": "queued",
        }
        
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }


@app.function(
    image=image,
    schedule=modal.Cron("*/1 * * * *"),  # Runs every minute to process queue
)
def drain_queue():
    """Scheduled cron worker to consume FIFO job queue under max concurrency limit."""
    dispatched = _drain_once()
    if dispatched > 0:
        print(f"[DrainQueue] Dispatched {dispatched} queued jobs.")


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
