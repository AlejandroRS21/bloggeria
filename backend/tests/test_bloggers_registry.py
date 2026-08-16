"""Tests for the pre-baked style profile registry (REQ-BE-LOADER, REQ-TESTS).

Covers:
- Path-traversal defense for registry input (threat matrix: routing/path traversal)
- Lookup by exact ID, slug, and canonical/full URL
- Schema compliance of all 13 pre-baked profile JSON files
"""

import json

import pytest

from src.orchestrator.bloggers_registry import PROFILES_DIR, get_prebaked_profile

# Canonical profile filenames required by REQ-BE-PROFILES (5 niches x ES/EN).
EXPECTED_PROFILES = {
    # Tech
    "javipas_style_profile.json",
    "microsiervos_style_profile.json",
    "simon_willison_style_profile.json",
    "julia_evans_style_profile.json",
    "dan_luu_style_profile.json",
    "dan_abramov_style_profile.json",
    # News
    "kiko_llaneras_style_profile.json",
    "ezra_klein_style_profile.json",
    # Literature
    "zenda_libros_style_profile.json",
    "marginalian_style_profile.json",
    # Food
    "el_comidista_style_profile.json",
    "serious_eats_style_profile.json",
    # Gossip
    "lecturas_cotilleos_style_profile.json",
}

# Design schema contract for {id}_style_profile.json.
REQUIRED_KEYS = {
    "alias",
    "vocabulary",
    "expressions",
    "transition_phrases",
    "topics",
    "tone",
    "voice",
    "sentence_pattern",
    "paragraph_pattern",
    "common_opens",
    "common_closes",
    "use_of_humor",
    "technical_level",
    "engagement_style",
    "language",
    "language_label",
}

# Non-empty required fields mandated by the apply task.
NON_EMPTY_KEYS = {"alias", "vocabulary", "tone", "voice", "language"}


class TestRegistryPathTraversal:
    """Threat matrix: registry input must never resolve outside backend/profiles/."""

    @pytest.mark.parametrize(
        "malicious",
        [
            "../../etc/passwd",
            "/etc/passwd",
            "\\etc\\passwd",
            "https://elcomidista.elpais.com/../../etc/passwd",
            "..%2f..%2fetc%2fpasswd",
        ],
    )
    def test_registry_path_traversal(self, malicious):
        """Traversal inputs return None — never a file read outside profiles/."""
        assert get_prebaked_profile(malicious) is None

    def test_absolute_local_path_is_rejected(self):
        assert get_prebaked_profile(str(PROFILES_DIR / "javipas_style_profile.json")) is None


class TestRegistryLookup:
    """Lookup by ID, slug, and canonical/full URL (REQ-BE-LOADER)."""

    def test_lookup_by_id(self):
        profile = get_prebaked_profile("javipas")
        assert profile is not None
        assert profile["alias"] == "JaviPas"
        assert profile["language"] == "es"

    def test_lookup_by_slug(self):
        profile = get_prebaked_profile("el-comidista")
        assert profile is not None
        assert profile["alias"] == "El Comidista"
        assert profile["language"] == "es"

    def test_lookup_by_canonical_url(self):
        """Spec Scenario 2: elcomidista.elpais.com resolves without scraping."""
        profile = get_prebaked_profile("https://elcomidista.elpais.com")
        assert profile is not None
        assert profile["language"] == "es"
        assert profile["topics"]

    def test_lookup_by_full_post_url(self):
        """An arbitrary post path on a registered domain still resolves."""
        profile = get_prebaked_profile("https://www.microsiervos.com/2024/05/curiosidad.html")
        assert profile is not None
        assert profile["alias"] == "Microsiervos"

    def test_lookup_www_stripped(self):
        assert get_prebaked_profile("https://www.microsiervos.com") is not None
        assert get_prebaked_profile("microsiervos.com") is not None

    def test_lookup_en_preset(self):
        profile = get_prebaked_profile("https://simonwillison.net")
        assert profile is not None
        assert profile["language"] == "en"

    def test_missing_id_returns_none(self):
        assert get_prebaked_profile("unknown-blogger") is None

    def test_missing_url_returns_none(self):
        """Spec Scenario 4: custom URLs must NOT match the registry."""
        assert get_prebaked_profile("https://example.com") is None

    def test_empty_input_returns_none(self):
        assert get_prebaked_profile("") is None
        assert get_prebaked_profile("   ") is None


FRONTEND_PRESETS = [
    ("javipas", "https://javipas.com"),
    ("microsiervos", "https://www.microsiervos.com"),
    ("simonwillison", "https://simonwillison.net"),
    ("jvns", "https://jvns.ca"),
    ("danluu", "https://danluu.com"),
    ("overreacted", "https://overreacted.io"),
    ("kiko-llaneras", "https://elpais.com/opinion/analytics/"),
    ("ezra-klein", "https://www.nytimes.com/column/ezra-klein"),
    ("zenda-libros", "https://www.zendalibros.com"),
    ("marginalian", "https://www.themarginalian.org"),
    ("el-comidista", "https://elcomidista.elpais.com"),
    ("serious-eats", "https://www.seriouseats.com"),
    ("lecturas-cotilleos", "https://www.lecturas.com"),
]


class TestAll13PresetsResolution:
    """Requirement: All 13 frontend presets MUST resolve pre-baked profiles by ID and by frontend URL."""

    @pytest.mark.parametrize("preset_id, frontend_url", FRONTEND_PRESETS)
    def test_preset_resolves_by_id(self, preset_id, frontend_url):
        profile = get_prebaked_profile(preset_id)
        assert profile is not None, f"Preset ID '{preset_id}' failed to resolve pre-baked profile"
        assert "alias" in profile

    @pytest.mark.parametrize("preset_id, frontend_url", FRONTEND_PRESETS)
    def test_preset_resolves_by_frontend_url(self, preset_id, frontend_url):
        profile = get_prebaked_profile(frontend_url)
        assert profile is not None, f"Frontend URL '{frontend_url}' (preset '{preset_id}') failed to resolve pre-baked profile"
        assert "alias" in profile


class TestProfileSchema:
    """All 13 pre-baked profiles exist, parse, and match the design schema."""

    def test_all_expected_profiles_present(self):
        files = {p.name for p in PROFILES_DIR.glob("*_style_profile.json")}
        assert files == EXPECTED_PROFILES

    @pytest.mark.parametrize("filename", sorted(EXPECTED_PROFILES))
    def test_profile_is_valid_json_with_required_keys(self, filename):
        data = json.loads((PROFILES_DIR / filename).read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        missing = REQUIRED_KEYS - set(data)
        assert not missing, f"{filename} missing keys: {sorted(missing)}"

    @pytest.mark.parametrize("filename", sorted(EXPECTED_PROFILES))
    def test_profile_required_fields_non_empty(self, filename):
        data = json.loads((PROFILES_DIR / filename).read_text(encoding="utf-8"))
        for key in NON_EMPTY_KEYS:
            value = data[key]
            assert value not in (None, "", [], {}), f"{filename}.{key} is empty"

    @pytest.mark.parametrize("filename", sorted(EXPECTED_PROFILES))
    def test_profile_language_valid(self, filename):
        data = json.loads((PROFILES_DIR / filename).read_text(encoding="utf-8"))
        assert data["language"] in ("es", "en")

    def test_all_languages_represented(self):
        langs = set()
        for filename in EXPECTED_PROFILES:
            data = json.loads((PROFILES_DIR / filename).read_text(encoding="utf-8"))
            langs.add(data["language"])
        assert langs == {"es", "en"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
