"""Pre-baked style profile registry (REQ-BE-LOADER).

Maps known blogger presets (by ID, slug, or blog URL) to local style
profile JSON files in ``backend/profiles/``. Registered presets skip live
web scraping entirely; unregistered (custom) URLs fall back to
``StyleAnalyzer.analyze`` in the orchestrator.

Security: lookups never resolve attacker-controlled paths. Input containing
``..`` or an absolute path is rejected outright, and filenames come ONLY
from this module's own ``REGISTRY`` map — never from user input.
"""

import json
from pathlib import Path
from typing import Any

# backend/profiles/ — this file lives at backend/src/orchestrator/bloggers_registry.py
PROFILES_DIR = Path(__file__).resolve().parent.parent.parent / "profiles"

# Modal runtime mounts backend/ under /root/ (src -> /root/src, aphra_blogger ->
# /root/aphra_blogger, profiles -> /root/backend/profiles per REQ-BE-MODAL).
_MODAL_PROFILES_DIR = Path("/root/backend/profiles")

# Canonical blogger id / slug / normalized netloc -> profile filename.
# The map is the single source of truth for safe filename resolution.
REGISTRY: dict[str, str] = {
    # Canonical IDs (also the profile file IDs)
    "javipas": "javipas_style_profile.json",
    "microsiervos": "microsiervos_style_profile.json",
    "simon_willison": "simon_willison_style_profile.json",
    "julia_evans": "julia_evans_style_profile.json",
    "dan_luu": "dan_luu_style_profile.json",
    "dan_abramov": "dan_abramov_style_profile.json",
    "kiko_llaneras": "kiko_llaneras_style_profile.json",
    "ezra_klein": "ezra_klein_style_profile.json",
    "zenda_libros": "zenda_libros_style_profile.json",
    "marginalian": "marginalian_style_profile.json",
    "el_comidista": "el_comidista_style_profile.json",
    "serious_eats": "serious_eats_style_profile.json",
    "lecturas_cotilleos": "lecturas_cotilleos_style_profile.json",
    # Slugs (frontend preset ids and URL-friendly forms)
    "jvns": "julia_evans_style_profile.json",
    "simonwillison": "simon_willison_style_profile.json",
    "danluu": "dan_luu_style_profile.json",
    "overreacted": "dan_abramov_style_profile.json",
    "el-comidista": "el_comidista_style_profile.json",
    "julia-evans": "julia_evans_style_profile.json",
    "simon-willison": "simon_willison_style_profile.json",
    "dan-luu": "dan_luu_style_profile.json",
    "dan-abramov": "dan_abramov_style_profile.json",
    "kiko-llaneras": "kiko_llaneras_style_profile.json",
    "ezra-klein": "ezra_klein_style_profile.json",
    "zenda-libros": "zenda_libros_style_profile.json",
    "lecturas-cotilleos": "lecturas_cotilleos_style_profile.json",
    "serious-eats": "serious_eats_style_profile.json",
    # Blog domains (netloc, www-less)
    "javipas.com": "javipas_style_profile.json",
    "microsiervos.com": "microsiervos_style_profile.json",
    "simonwillison.net": "simon_willison_style_profile.json",
    "jvns.ca": "julia_evans_style_profile.json",
    "danluu.com": "dan_luu_style_profile.json",
    "overreacted.io": "dan_abramov_style_profile.json",
    "kikollaneras.elpais.com": "kiko_llaneras_style_profile.json",
    "ezraklein.nytimes.com": "ezra_klein_style_profile.json",
    # Real frontend section URLs for shared domains
    "elpais.com/opinion/analytics": "kiko_llaneras_style_profile.json",
    "nytimes.com/column/ezra-klein": "ezra_klein_style_profile.json",
    "zendalibros.com": "zenda_libros_style_profile.json",
    "themarginalian.org": "marginalian_style_profile.json",
    "elcomidista.elpais.com": "el_comidista_style_profile.json",
    "seriouseats.com": "serious_eats_style_profile.json",
    "lecturas.com": "lecturas_cotilleos_style_profile.json",
}


def _resolve_profiles_dir() -> Path:
    """Return the profiles directory that exists, local dev or Modal runtime."""
    if PROFILES_DIR.is_dir():
        return PROFILES_DIR
    return _MODAL_PROFILES_DIR


def _normalize_key(raw: str, strip_path: bool = False) -> str | None:
    """Normalize a lookup input to a registry key, or None if unsafe/invalid.

    Accepts blogger IDs, slugs, and http(s) blog URLs (with or without
    scheme, ``www.`` prefix, and trailing post paths). Rejects traversal
    sequences (``..``) and absolute filesystem paths.
    """
    value = raw.strip().lower()
    if not value or ".." in value:
        return None
    if value.startswith(("/", "\\")):
        return None
    if "://" in value:
        value = value.split("://", 1)[1]
    value = value.rstrip("/")
    if value.startswith("www."):
        value = value[4:]
    if strip_path and "/" in value:
        value = value.split("/", 1)[0]
    return value or None


def get_prebaked_profile(url_or_id: str) -> dict[str, Any] | None:
    """Look up a pre-baked style profile by blogger ID, slug, or blog URL.

    Returns the parsed profile dictionary when the input matches a
    registered preset and its JSON file exists and parses; otherwise None
    (callers fall back to live scraping).
    """
    # 1. Try exact key (preserves path for section URLs on shared domains)
    key = _normalize_key(url_or_id, strip_path=False)
    filename = REGISTRY.get(key or "")  # "" never keys the map

    # 2. Fall back to netloc-only key if exact path missed (e.g. blog post URLs)
    if filename is None and key and "/" in key:
        domain_key = _normalize_key(url_or_id, strip_path=True)
        filename = REGISTRY.get(domain_key or "")

    if filename is None:
        return None

    # Belt-and-braces: filename comes from our own map, but never resolve
    # outside the profiles dir regardless.
    profile_path = (_resolve_profiles_dir() / filename).resolve()
    profiles_root = _resolve_profiles_dir().resolve()
    if profiles_root not in profile_path.parents:
        return None

    try:
        with open(profile_path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
