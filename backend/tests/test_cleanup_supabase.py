"""Tests for cleanup_supabase quality detection (REQ-1: Cleanup Cron Safety)."""

import pytest

from cleanup_supabase import detect_low_quality, quality_metrics


def build_post(words: int, headings: int, boilerplate: bool = False) -> str:
    """Build HTML post content with the given word and heading counts."""
    heading_html = "".join(f"<h2>Heading {i}</h2>" for i in range(headings))
    body_words = " ".join(f"palabra{i}" for i in range(words))
    bp = "<p>Aquí tienes el post</p>" if boilerplate else ""
    return f"{heading_html}<p>{body_words}</p>{bp}"


class TestDetectLowQuality:
    def test_short_boilerplate_post_is_low(self):
        """150-word post containing 'Aquí tienes el post' must be flagged low."""
        content = build_post(150, 1, boilerplate=True)
        is_low, reason = detect_low_quality(content)
        assert is_low is True
        assert "boilerplate" in reason or "Short content" in reason

    def test_long_well_structured_post_is_kept(self):
        """450-word post with 5 headings must be kept (guarded threshold)."""
        content = build_post(450, 5)
        is_low, reason = detect_low_quality(content)
        assert is_low is False, f"expected kept, got: {reason}"

    def test_short_post_with_boilerplate_is_low(self):
        """120-word post with 1 heading and boilerplate must be low."""
        content = build_post(120, 1, boilerplate=True)
        is_low, reason = detect_low_quality(content)
        assert is_low is True
        assert "boilerplate" in reason or "Short content" in reason

    def test_default_threshold_keeps_250_word_post(self):
        """Regression: default min_words must be 200, so a 250-word post
        with 3 headings is NOT low quality (was flagged at the old 400)."""
        content = build_post(250, 3)
        is_low, reason = detect_low_quality(content)
        assert is_low is False, f"expected kept, got: {reason}"

    def test_explicit_min_words_overrides_default(self):
        """Callers can still raise the threshold explicitly."""
        content = build_post(300, 4)
        is_low, reason = detect_low_quality(content, min_words=400)
        assert is_low is True
        assert "Short content" in reason


class TestQualityMetrics:
    def test_counts_words_and_headings(self):
        metrics = quality_metrics(build_post(200, 3))
        assert metrics["word_count"] >= 200
        assert metrics["h2_count"] == 3
        assert metrics["h3_count"] == 0
        assert metrics["boilerplate"] is None

    def test_detects_boilerplate_pattern(self):
        metrics = quality_metrics(build_post(200, 3, boilerplate=True))
        assert metrics["boilerplate"] is not None
