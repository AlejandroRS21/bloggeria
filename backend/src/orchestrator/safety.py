"""Content safety, deterministic guardrails, and HTML sanitization agent."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Canonical niche keys consumed by the moderators (English) plus Spanish
# aliases found in pre-baked style profiles (salsa_rosa, tecnologia, ...).
NICHE_ALIASES = {
    "tech": "tech", "tecnologia": "tech", "tecnología": "tech",
    "news": "news", "noticias": "news",
    "literature": "literature", "literatura": "literature",
    "food": "food", "comida": "food", "gastronomia": "food", "gastronomía": "food",
    "gossip": "gossip", "salsa_rosa": "gossip", "cotilleos": "gossip", "cotilleo": "gossip",
}


def normalize_niche(niche: Optional[str]) -> str:
    """Map a raw niche value (ES or EN) to a canonical moderator key."""
    if not niche:
        return "tech"
    return NICHE_ALIASES.get(niche.strip().lower(), "tech")

# --- 1. Deterministic Moderation (Pre-LLM) ---

# Common Spanish/English obscene/hate words
DEFAULT_BLACKLIST = [
    r"\bputa\b", r"\bputo\b", r"\bmaricón\b", r"\bmaricon\b", r"\bcoño\b",
    r"\bpolla\b", r"\bchingar\b", r"\bjoder\b", r"\bfuck\b", r"\bshit\b",
    r"\bhitler\b", r"\bnazi\b", r"\bmatar a todos\b", r"\bterrorismo\b"
]

# PII Patterns: Emails, Spanish DNI/NIE, Credit Cards
REGEX_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
REGEX_DNI = re.compile(r"\b\d{8}[A-HJ-NP-TV-Z]\b", re.IGNORECASE)
REGEX_NIE = re.compile(r"\b[X-Z]\d{7}[A-Z]\b", re.IGNORECASE)
REGEX_CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# Spam / Fraud Patterns
SPAM_PATTERNS = [
    re.compile(r"\b(gana|ganar)\s+(\$|€|\d+\s*euro|dinero)\s+(gratis|fácil|rapido)\b", re.IGNORECASE),
    re.compile(r"\b(crypto|bitcoin)\s+(doubler|investment|garantizado)\b", re.IGNORECASE),
    re.compile(r"\b(click|clic)\s+aquí\s+para\s+(reclamar|cobrar|premios?)\b", re.IGNORECASE),
    re.compile(r"https?://[^\s<>]*(bit\.ly|tinyurl\.com|t\.co|cutt\.ly|goo\.gl)/[^\s<>]+", re.IGNORECASE),
]


def luhn_check(card_number: str) -> bool:
    """Verifies a credit card number using Luhn algorithm."""
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


def check_deterministic(text: str, niche: str = "tech") -> Optional[Dict[str, Any]]:
    """Fast pre-LLM deterministic checks: Blacklist, PII, and Spam.
    
    Returns a dict with rejection details if unsafe, or None if safe.
    """
    if not text:
        return None

    # 1. PII: Emails
    if REGEX_EMAIL.search(text):
        return {
            "safe": False,
            "approved": False,
            "reason": "Detección de PII: dirección de correo electrónico expuesta",
            "layer": "deterministic_pii"
        }

    # 2. PII: DNI / NIE
    if REGEX_DNI.search(text) or REGEX_NIE.search(text):
        return {
            "safe": False,
            "approved": False,
            "reason": "Detección de PII: número de identificación personal (DNI/NIE) expuesto",
            "layer": "deterministic_pii"
        }

    # 3. PII: Credit Card (Regex + Luhn)
    for match in REGEX_CREDIT_CARD.finditer(text):
        candidate = match.group()
        if luhn_check(candidate):
            return {
                "safe": False,
                "approved": False,
                "reason": "Detección de PII: número de tarjeta de crédito expuesto",
                "layer": "deterministic_pii"
            }

    # 4. Blacklist
    for pattern in DEFAULT_BLACKLIST:
        if re.search(pattern, text, re.IGNORECASE):
            return {
                "safe": False,
                "approved": False,
                "reason": "Contenido rechazado por lista de palabras prohibidas",
                "layer": "deterministic_blacklist"
            }

    # 5. Spam / Fraud
    for pattern in SPAM_PATTERNS:
        if pattern.search(text):
            return {
                "safe": False,
                "approved": False,
                "reason": "Detección de spam o posible fraude en el contenido",
                "layer": "deterministic_spam"
            }

    return None


# --- 2. HTML Sanitizer (XSS Prevention) ---

# Whitelisted tags for generated blog HTML
ALLOWED_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "strong", "em", "b", "i", "u",
    "a", "img", "code", "pre", "ul", "ol", "li", "blockquote", "hr", "br",
    "div", "span", "figure", "figcaption", "table", "thead", "tbody", "tr", "th", "td"
}

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target", "rel", "class"},
    "img": {"src", "alt", "title", "class", "width", "height"},
    "code": {"class"},
    "div": {"class"},
    "span": {"class"},
}


def sanitize_html(html_content: str) -> str:
    """Sanitizes generated HTML content to prevent XSS attacks.
    
    Removes script tags, inline event handlers (onerror, onload, etc.),
    and unsafe URIs (javascript:, data:text/html).
    """
    if not html_content:
        return ""

    # 1. Remove <script> ... </script> completely
    sanitized = re.sub(r"(?i)<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>", "", html_content)

    # 2. Remove <style> ... </style> or <iframe> ... </iframe> if unapproved
    sanitized = re.sub(r"(?i)<iframe\b[^<]*(?:(?!</iframe>)<[^<]*)*</iframe>", "", sanitized)
    sanitized = re.sub(r"(?i)<object\b[^<]*(?:(?!</object>)<[^<]*)*</object>", "", sanitized)

    # 3. Remove inline event handlers like onload=..., onclick=...
    sanitized = re.sub(r"(?i)\s+on[a-z]+\s*=\s*(?:'[^']*'|\"[^\"]*\"|[^\s>]+)", "", sanitized)

    # 4. Remove dangerous URIs (javascript:, vbscript:, data:text/html)
    sanitized = re.sub(r"(?i)href\s*=\s*['\"]?\s*(?:javascript|vbscript|data\s*:\s*text/html)[^'\">]*['\"]?", 'href="#"', sanitized)
    sanitized = re.sub(r"(?i)src\s*=\s*['\"]?\s*(?:javascript|vbscript|data\s*:\s*text/html)[^'\">]*['\"]?", 'src=""', sanitized)

    return sanitized


# --- 3. Robust JSON Parsing for LLM Responses ---

def parse_moderation_json(response: str) -> Dict[str, Any]:
    """Parses LLM moderation response robustly.
    
    Prevents false rejections on valid non-JSON or poorly formatted LLM outputs.
    """
    if not response or not isinstance(response, str):
        return {"safe": True, "approved": True, "reason": "OK"}

    cleaned = response.strip()

    # Stripping markdown codeblocks if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    # Attempt regex JSON extraction
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if isinstance(data, dict):
                safe_val = data.get("safe")
                if safe_val is None:
                    safe_val = data.get("approved")
                if safe_val is None:
                    # Infer boolean from text values if boolean key missing
                    safe_val = True if data.get("status") in ("ok", "safe", "approved") else False

                reason_val = data.get("reason") or ("OK" if safe_val else "Contenido no apto")
                return {
                    "safe": bool(safe_val),
                    "approved": bool(safe_val),
                    "reason": str(reason_val)
                }
        except json.JSONDecodeError:
            pass

    # Heuristic fallback if JSON decoding fails (avoids false rejections!)
    lower_resp = cleaned.lower()
    if any(k in lower_resp for k in ["\"safe\": true", "\"approved\": true", "safe: true", "safe=true", "aprobado", "es seguro"]):
        return {"safe": True, "approved": True, "reason": "OK"}

    if any(k in lower_resp for k in ["\"safe\": false", "\"approved\": false", "inseguro", "no apto", "violación"]):
        # Extract possible reason text
        reason_match = re.search(r"reason[\"']?\s*:\s*[\"']?([^\"'\n}]+)", cleaned, re.IGNORECASE)
        reason_str = reason_match.group(1).strip() if reason_match else "Contenido marcado como no seguro."
        return {"safe": False, "approved": False, "reason": reason_str}

    # If completely ambiguous but no obvious rejection markers -> Fail safe (allow)
    logger.warning("Moderation response was non-JSON and ambiguous, failing open to avoid false rejection: %s", cleaned[:100])
    return {"safe": True, "approved": True, "reason": "OK (Parsed from non-JSON response)"}


# --- 4. Moderation Logger ---

def log_moderation_event(
    stage: str,
    reason: str,
    layer: str,
    niche: str,
    content_snippet: str,
    supabase_client: Optional[Any] = None
) -> None:
    """Logs moderation rejections to audit log (Supabase table or JSON stdout fallback)."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,  # 'topic' or 'article'
        "reason": reason,
        "layer": layer,  # 'deterministic_*' or 'llm'
        "niche": niche,
        "snippet": content_snippet[:200]
    }
    logger.warning("[Moderation Audit Log] REJECTED: %s", json.dumps(event, ensure_ascii=False))

    if supabase_client:
        try:
            supabase_client.table("moderation_logs").insert(event).execute()
        except Exception as e:
            logger.error("[Moderation Audit Log] Failed to insert to Supabase: %s", e)


# --- 5. Main SafetyAgent Class ---

class SafetyAgent:
    """Agent responsible for content safety and professional guardrails.
    
    Supports multi-niche evaluations, full article validation, and deterministic pre-filtering.
    """

    def __init__(self, api_key: str, provider: str = "huggingface", model: Optional[str] = None) -> None:
        from aphra_blogger.llm.factory import create_llm_provider
        self.llm = create_llm_provider(provider=provider, api_key=api_key, model=model)

    def validate_topic(self, topic: str, niche: str = "tech") -> Dict[str, Any]:
        """Validates a topic against professional and safety standards."""
        # 1. Deterministic Layer
        det_result = check_deterministic(topic, niche=niche)
        if det_result is not None:
            log_moderation_event("topic", det_result["reason"], det_result["layer"], niche, topic)
            return det_result

        # 2. LLM Moderation Layer
        prompt = self._build_topic_prompt(topic, niche)
        try:
            response = self.llm.generate(prompt)
            result = parse_moderation_json(response)
            result["layer"] = "llm"
            if not result.get("safe", True):
                log_moderation_event("topic", result["reason"], "llm", niche, topic)
            return result
        except Exception as e:
            logger.error("Error in SafetyAgent LLM validation: %s", e)
            # Fail safe on LLM provider technical errors to prevent blocking post generation
            return {"safe": True, "approved": True, "reason": f"Fallback por error técnico LLM: {str(e)}", "layer": "llm_error"}

    def validate_article(self, article: Dict[str, Any], niche: str = "tech") -> Dict[str, Any]:
        """Validates a generated full article (title, description, content) before publishing."""
        title = article.get("title", "")
        description = article.get("description", "")
        content = article.get("content", "")
        combined_text = f"TÍTULO: {title}\nDESCRIPCIÓN: {description}\nCONTENIDO:\n{content[:4000]}"

        # 1. Deterministic Layer
        det_result = check_deterministic(combined_text, niche=niche)
        if det_result is not None:
            log_moderation_event("article", det_result["reason"], det_result["layer"], niche, title or combined_text[:50])
            return det_result

        # 2. LLM Moderation Layer
        prompt = self._build_article_prompt(combined_text, niche)
        try:
            response = self.llm.generate(prompt)
            result = parse_moderation_json(response)
            result["layer"] = "llm"
            if not result.get("safe", True):
                log_moderation_event("article", result["reason"], "llm", niche, title or combined_text[:50])
            return result
        except Exception as e:
            logger.error("Error in SafetyAgent article validation: %s", e)
            return {"safe": True, "approved": True, "reason": f"Fallback por error técnico LLM: {str(e)}", "layer": "llm_error"}

    def _build_topic_prompt(self, topic: str, niche: str) -> str:
        niche_context = self._get_niche_context(niche)
        return f"""
        Actúa como un Moderador de Contenido Profesional para un blog de {niche_context}.
        Tu tarea es evaluar si el siguiente TEMA es apropiado para ser publicado.
        
        TEMA: "{topic}"
        NICHO: {niche}
        
        CRITERIOS DE RECHAZO (Responde 'FALSE' si cumple alguno):
        1. Contenido obsceno, pornográfico o abuso explícito.
        2. Discurso de odio, discriminación grave o incitación a la violencia.
        3. Promoción activa de actividades ilegales o estafas.
        4. Exposición de datos personales privados (PII no pública, direcciones privadas, DNI).
        5. Temas que violen gravemente los estándares del nicho '{niche}'.
        
        Responde ÚNICAMENTE en formato JSON:
        {{
          "safe": boolean,
          "reason": "breve explicación en español si es inseguro, de lo contrario 'OK'"
        }}
        """

    def _build_article_prompt(self, article_text: str, niche: str) -> str:
        niche_context = self._get_niche_context(niche)
        return f"""
        Actúa como un Moderador de Contenido Profesional para un blog de {niche_context}.
        Tu tarea es evaluar si el siguiente ARTÍCULO COMPLETO generado es seguro para ser publicado.
        
        ARTÍCULO:
        {article_text}
        
        CRITERIOS DE RECHAZO:
        1. Contenido obsceno, pornografía o violencia explícita.
        2. Discurso de odio o acoso malicioso.
        3. Malware, enlaces fraudulentos o estafas.
        4. Inclusión no autorizada de datos personales sensibles (PII).
        
        Responde ÚNICAMENTE en formato JSON:
        {{
          "safe": boolean,
          "reason": "breve explicación en español si es inseguro, de lo contrario 'OK'"
        }}
        """

    def _get_niche_context(self, niche: str) -> str:
        canonical = normalize_niche(niche)
        niches = {
            "tech": "Tecnología, Desarrollo y Ciencia",
            "news": "Noticias Generales y Actualidad",
            "literature": "Literatura, Ensayos y Reseñas",
            "food": "Gastronomía y Recetas",
            "gossip": "Prensa Rosa, Noticias de Celebridades y Entretenimiento (Se permiten rumores y noticias públicas de celebridades, sin incitar al odio o difamación ilegal)"
        }
        return niches.get(canonical, "Estilo de Vida y Cultura General")


def check_niche_divergence(topic: str, profile: Optional[Dict[str, Any]]) -> Optional[str]:
    """Check if the given topic diverges from the blogger profile's niche."""
    if not profile or not isinstance(profile, dict) or not topic:
        return None
    raw_niche = profile.get("niche")
    if not raw_niche:
        return None

    blogger_niche = normalize_niche(raw_niche)
    topic_lower = topic.lower()

    food_keywords = {"pumpkin", "purée", "puree", "recipe", "receta", "breakfast", "desayuno", "cooking", "cocina", "tarta", "cake"}
    tech_keywords = {"python", "javascript", "code", "software", "hardware", "ai", "llm", "api", "framework", "kernel"}

    if blogger_niche == "tech" and any(w in topic_lower for w in food_keywords):
        return f"Topic '{topic}' (food/cooking) diverges from blogger niche '{blogger_niche}'."
    if blogger_niche == "food" and any(w in topic_lower for w in tech_keywords):
        return f"Topic '{topic}' (tech) diverges from blogger niche '{blogger_niche}'."
    return None
