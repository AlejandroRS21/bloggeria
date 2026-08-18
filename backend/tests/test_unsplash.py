"""Tests for Unsplash image selection (dedupe + variety)."""
import sys
from unittest import mock

sys.path.insert(0, ".")
from aphra_blogger.agents import unsplash


def _fake_response(urls):
    """Build a fake requests response with N results."""
    resp = mock.Mock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "results": [{"urls": {"regular": u}} for u in urls]
    }
    return resp


def test_extract_keywords_strips_filler():
    kw = unsplash._extract_keywords(
        "Professional modern hero image representing gazpacho andaluz recipe"
    )
    assert "gazpacho" in kw and "andaluz" in kw
    assert "professional" not in kw and "hero" not in kw


def test_search_image_picks_randomized_not_first():
    urls = [f"https://img.example.com/{i}" for i in range(10)]
    with mock.patch("requests.get", return_value=_fake_response(urls)) as m:
        r1 = unsplash.search_image("gazpacho andaluz", access_key="k", seed=1)
        r2 = unsplash.search_image("gazpacho andaluz", access_key="k", seed=2)
    assert m.called
    assert r1 in urls and r2 in urls
    # different seeds -> different picks (probabilistic but 10 candidates)
    assert r1 != r2


def test_enrich_images_dedupes_within_batch():
    urls = [f"https://img.example.com/{i}" for i in range(10)]
    prompts = [
        {"position": "header", "prompt": "gazpacho andaluz recipe"},
        {"position": "section-1", "prompt": "gazpacho ingredients"},
        {"position": "section-2", "prompt": "gazpacho serving"},
    ]
    with mock.patch("requests.get", return_value=_fake_response(urls)):
        out = unsplash.enrich_images(prompts, access_key="k")
    used = [o["url"] for o in out if o.get("url")]
    assert len(used) == 3, f"expected 3 images, got {len(used)}"
    assert len(set(used)) == 3, "duplicate URLs within batch"


def test_search_image_returns_none_without_key():
    with mock.patch.dict("os.environ", {}, clear=True):
        assert unsplash.search_image("gazpacho", access_key=None) is None
