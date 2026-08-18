"""
Unsplash Image Search Agent.

Searches for relevant, high-quality photographs based on topic/prompt keywords.
Free tier: 50 requests/hour, no API key required for search with Client-ID header.
"""

import os
import re
import random
from typing import List, Dict, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


UNSPLASH_API = "https://api.unsplash.com/search/photos"

# strip filler words but keep the meaningful core of the prompt
_FILLER = re.compile(
    r"\b(professional|modern|hero|image|illustrative|representing|about|related|to|"
    r"high|quality|clean|design|technology|theme|aspect|ratio|"
    r"eye|stunning|beautiful|amazing|inspiring|style|concept|for|the|and|with|"
    r"photography|photo|picture|blog|section|article|visual|support|content)\b",
    re.IGNORECASE,
)


def _extract_keywords(prompt: str, max_words: int = 6) -> str:
    """Extract meaningful search keywords from an image prompt."""
    cleaned = _FILLER.sub(" ", prompt)
    words = [w.strip(" ,;:") for w in cleaned.split() if len(w.strip(" ,;:")) > 2]
    # prefer words that are not stopwords; keep first max_words
    if words:
        return " ".join(words[:max_words])
    return " ".join(prompt.split()[:max_words])


def search_image(
    query: str,
    access_key: Optional[str] = None,
    used_urls: Optional[set] = None,
    seed: Optional[int] = None,
) -> Optional[str]:
    """
    Search Unsplash for a photo matching the query.

    Fetches up to 10 results and picks one pseudo-randomly (seeded) so the
    same query does not always return the same photo, and avoids URLs already
    used in this batch (dedupe).
    """
    if not REQUESTS_AVAILABLE:
        return None

    key = access_key or os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        return None

    keywords = _extract_keywords(query)
    if not keywords:
        return None

    try:
        resp = requests.get(
            UNSPLASH_API,
            headers={"Authorization": f"Client-ID {key}"},
            params={"query": keywords, "per_page": 10, "orientation": "landscape"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            candidates = [r["urls"]["regular"] for r in results]
            # prefer unused candidates
            pool = [u for u in candidates if not used_urls or u not in used_urls]
            if not pool:
                pool = candidates
            rng = random.Random(seed if seed is not None else None)
            chosen = rng.choice(pool)
            if used_urls is not None:
                used_urls.add(chosen)
            return chosen
    except Exception as e:
        print(f"[Unsplash] Search failed for '{keywords}': {e}")

    return None


def enrich_images(prompts: List[Dict[str, str]], access_key: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Take image prompt dicts (from ImageSelectorAgent) and add Unsplash URLs.

    Each prompt dict gets a 'url' field with a real photo URL.
    Prompts that already have a 'url' are skipped.
    Images are deduped within the batch and picked pseudo-randomly per prompt.
    """
    used_urls: set = set()
    enriched = []
    for idx, img in enumerate(prompts):
        if img.get("url"):
            enriched.append(img)
            continue

        # Try the prompt first, fall back to alt_text
        query = img.get("prompt", "") or img.get("alt_text", "")
        url = search_image(query, access_key, used_urls=used_urls, seed=idx * 7919 + 13)

        if url:
            img["url"] = url
            img["source"] = "unsplash"
            print(f"[Unsplash] ✓ Image for '{query[:40]}...' -> {url[:60]}...")
        else:
            print(f"[Unsplash] ✗ No result for '{query[:40]}...'")

        enriched.append(img)

    return enriched
