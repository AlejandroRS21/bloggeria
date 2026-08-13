"""Tests for style attribution mapping (REQ-2, REQ-3).

Exercises the undecorated logic seam `_map_to_supabase` and the webhook
type guard via `webhook.local(...)`, matching the test_webhook_guard
pattern (no deployed Modal runtime).
"""

import modal_app
from modal_app import _map_to_supabase, webhook

BASE_RESULT = {
    "workflow_id": "w1",
    "title": "Post de prueba",
    "keywords": ["ia"],
    "html_structure": {
        "metadata": {"slug": "post", "title": "Post de prueba", "description": "d"},
        "html": "",
    },
}


class TestMapToSupabaseStyleSource:
    def test_explicit_blogger_name_wins_over_heuristic(self):
        result = {**BASE_RESULT, "blogger_urls": ["https://simonwillison.net"]}
        mapped = _map_to_supabase(result, blogger_name="Simon Willison")
        assert mapped["style_source"] == "Simon Willison"
        assert mapped["style_source_url"] == "https://simonwillison.net"

    def test_heuristic_fallback_from_first_url(self):
        result = {**BASE_RESULT, "blogger_urls": ["https://example.com/blog"]}
        mapped = _map_to_supabase(result)
        assert mapped["style_source"] == "Example"
        assert mapped["style_source_url"] == "https://example.com/blog"

    def test_no_blogger_data_yields_none_fields(self):
        mapped = _map_to_supabase(BASE_RESULT)
        assert mapped["style_source"] is None
        assert mapped["style_source_url"] is None


class TestWebhookBloggerNameGuard:
    def test_non_string_blogger_name_rejected(self, monkeypatch):
        monkeypatch.setattr(
            modal_app, "moderate_topic", lambda topic: {"approved": True}
        )
        payload = {
            "blogger_urls": ["https://simonwillison.net"],
            "topic": "IA en el desarrollo web",
            "blogger_name": 42,
        }
        result = webhook.local(payload)
        assert result == {
            "success": False,
            "data": None,
            "error": "blogger_name must be a string",
        }
