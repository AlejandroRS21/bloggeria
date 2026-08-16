"""Tests for content moderation robustness (5-layer system).

Covers:
1. Deterministic pre-LLM layer (blacklist / PII / spam)
2. Robust JSON parsing (no false rejections on non-JSON LLM output)
3. Niche-aware moderation (salsa_rosa vs tech tolerance)
4. Persistent moderation audit logging
5. HTML sanitization (XSS prevention)
6. Backward-compatible moderate_topic contract
"""

from unittest.mock import MagicMock, patch

import pytest

from src.orchestrator.safety import (
    DEFAULT_BLACKLIST,
    SPAM_PATTERNS,
    SafetyAgent,
    check_deterministic,
    log_moderation_event,
    luhn_check,
    normalize_niche,
    parse_moderation_json,
    sanitize_html,
)


# ── 1. Deterministic pre-LLM layer ─────────────────────────────────────────

class TestDeterministicModerator:
    def test_safe_text_passes(self):
        assert check_deterministic("Cómo mejorar tu productividad con Python") is None

    def test_blacklist_rejects(self):
        result = check_deterministic("Este producto es una puta estafa")
        assert result is not None
        assert result["layer"] == "deterministic_blacklist"
        assert result["approved"] is False
        assert result["safe"] is False

    def test_email_pii_rejected(self):
        result = check_deterministic("Contacta a maria.perez@gmail.com para más info")
        assert result is not None
        assert result["layer"] == "deterministic_pii"
        assert "correo" in result["reason"]

    def test_dni_pii_rejected(self):
        result = check_deterministic("El cliente con DNI 41234567A compró el producto")
        assert result is not None
        assert result["layer"] == "deterministic_pii"

    def test_credit_card_luhn_rejected(self):
        # Valid Luhn test number (4111111111111111)
        result = check_deterministic("Mi tarjeta es 4111 1111 1111 1111 y pago con ella")
        assert result is not None
        assert result["layer"] == "deterministic_pii"
        assert "tarjeta" in result["reason"]

    def test_credit_card_invalid_luhn_passes(self):
        # Sum fails Luhn -> should NOT be flagged as PII
        assert check_deterministic("El número 1234567890123456 no es válido") is None

    def test_spam_fraud_rejected(self):
        result = check_deterministic("¡Gana dinero gratis haciendo clic aquí para reclamar tu premio!")
        assert result is not None
        assert result["layer"] == "deterministic_spam"

    def test_url_shortener_spam_rejected(self):
        result = check_deterministic("Mira esta oferta: https://bit.ly/xyz123")
        assert result is not None
        assert result["layer"] == "deterministic_spam"

    def test_empty_input_returns_none(self):
        assert check_deterministic("") is None
        assert check_deterministic(None) is None


class TestLuhnCheck:
    def test_valid_card(self):
        assert luhn_check("4111111111111111") is True

    def test_invalid_card(self):
        assert luhn_check("4111111111111112") is False

    def test_too_short(self):
        assert luhn_check("1234") is False


# ── 2. Robust JSON parsing ─────────────────────────────────────────────────

class TestParseModerationJson:
    def test_plain_valid_json(self):
        res = parse_moderation_json('{"safe": false, "reason": "mala"}')
        assert res["safe"] is False

    def test_valid_json_with_approved_key(self):
        res = parse_moderation_json('{"approved": false, "reason": "no"}')
        assert res["safe"] is False

    def test_markdown_codeblock_json(self):
        res = parse_moderation_json('```json\n{"safe": true, "reason": "OK"}\n```')
        assert res["safe"] is True

    def test_non_json_benign_text_no_false_rejection(self):
        # Core requirement: non-JSON LLM output must NOT cause false rejection
        res = parse_moderation_json("Gracias por tu consulta. Este tema es completamente seguro y apropiado para publicar. Saludos!")
        assert res["safe"] is True
        assert res["approved"] is True

    def test_non_json_with_safe_marker(self):
        res = parse_moderation_json('El tema es seguro. Resultado: "safe": true')
        assert res["safe"] is True

    def test_non_json_with_unsafe_marker(self):
        res = parse_moderation_json('Resultado: "safe": false, motivo: "incita al odio"')
        assert res["safe"] is False

    def test_empty_response_fails_open(self):
        res = parse_moderation_json("")
        assert res["safe"] is True

    def test_malformed_json_with_safe_hint(self):
        res = parse_moderation_json('{"safe": true, "reason": "OK" extra garbage')
        # Regex extracts the balanced object? No: malformed -> hint fallback
        assert res["safe"] is True


# ── 3. Niche-aware moderation ──────────────────────────────────────────────

class TestNicheAwareness:
    def test_normalize_niche_spanish_aliases(self):
        assert normalize_niche("salsa_rosa") == "gossip"
        assert normalize_niche("tecnologia") == "tech"
        assert normalize_niche("comida") == "food"
        assert normalize_niche("noticias") == "news"
        assert normalize_niche("literatura") == "literature"

    def test_normalize_niche_english_keys(self):
        assert normalize_niche("gossip") == "gossip"
        assert normalize_niche("tech") == "tech"

    def test_normalize_niche_fallback_tech(self):
        assert normalize_niche("misterioso") == "tech"
        assert normalize_niche(None) == "tech"
        assert normalize_niche("") == "tech"

    def test_safe_gossip_topic_not_rejected(self):
        # Gossip about a celebrity's public life is allowed in salsa_rosa niche
        result = check_deterministic("Última hora: nuevo romance de un famoso actor en Madrid")
        assert result is None

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_gossip_prompt_includes_niche_context(self, mock_create):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"safe": true, "reason": "OK"}'
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="key", provider="huggingface")
        agent.validate_topic("Nuevo romance de famoso", niche="gossip")
        prompt_used = mock_llm.generate.call_args[0][0]
        assert "Prensa Rosa" in prompt_used

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_tech_prompt_has_tech_context(self, mock_create):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"safe": true, "reason": "OK"}'
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="key", provider="huggingface")
        agent.validate_topic("Nuevo framework JS", niche="tech")
        prompt_used = mock_llm.generate.call_args[0][0]
        assert "Tecnología" in prompt_used


# ── 4. Moderation audit logging ────────────────────────────────────────────

class TestModerationLogger:
    def test_log_event_called_without_supabase(self, caplog):
        # Must not raise; falls back to structured log line
        log_moderation_event(
            stage="topic",
            reason="Palabra prohibida",
            layer="deterministic_blacklist",
            niche="tech",
            content_snippet="tema malo",
        )
        # Ensure it logs a rejection marker line
        assert any("REJECTED" in r.message for r in caplog.records)

    def test_log_event_supabase_insert_on_rejection(self):
        mock_client = MagicMock()
        log_moderation_event(
            stage="article",
            reason="PII",
            layer="deterministic_pii",
            niche="gossip",
            content_snippet="email expuesto",
            supabase_client=mock_client,
        )
        mock_client.table.assert_called_once_with("moderation_logs")
        mock_client.table("moderation_logs").insert.assert_called_once()

    def test_log_event_supabase_failure_is_non_fatal(self, caplog):
        mock_client = MagicMock()
        mock_client.table.side_effect = Exception("DB down")
        # Must NOT raise even when Supabase insert fails
        log_moderation_event(
            stage="topic",
            reason="x",
            layer="llm",
            niche="tech",
            content_snippet="y",
            supabase_client=mock_client,
        )


# ── 5. HTML sanitization (XSS) ─────────────────────────────────────────────

class TestHTMLSanitizer:
    def test_script_tag_removed(self):
        html = "<p>Hola</p><script>alert('xss')</script><p>mundo</p>"
        out = sanitize_html(html)
        assert "<script>" not in out.lower()
        assert "alert" not in out

    def test_inline_event_handler_removed(self):
        html = '<img src="x.png" onerror="alert(1)"><p onclick="hack()">texto</p>'
        out = sanitize_html(html)
        assert "onerror" not in out.lower()
        assert "onclick" not in out.lower()

    def test_javascript_href_neutralized(self):
        html = '<a href="javascript:alert(1)">click</a>'
        out = sanitize_html(html)
        assert "javascript:" not in out.lower()

    def test_data_html_src_neutralized(self):
        html = '<img src="data:text/html;base64,PHNjcmlwdD4=" alt="x">'
        out = sanitize_html(html)
        assert "data:text/html" not in out.lower()

    def test_iframe_removed(self):
        html = "<p>hola</p><iframe src=\"https://evil.com\"></iframe>"
        out = sanitize_html(html)
        assert "<iframe" not in out.lower()

    def test_benign_html_preserved(self):
        html = "<p><strong>Hola</strong> <a href=\"https://ok.com\">link</a></p>"
        out = sanitize_html(html)
        assert "<strong>Hola</strong>" in out
        assert "https://ok.com" in out

    def test_empty_input(self):
        assert sanitize_html("") == ""


# ── 6. Backward-compatible moderate_topic contract via SafetyAgent ────────

class TestModerateTopicContract:
    """validate_topic must keep the same contract: {safe, reason} + backward
    compat aliases for the webhook's {approved, reason}."""

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_safe_keeps_approved_and_safe_aliases(self, mock_create):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"safe": true, "reason": "OK"}'
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="key", provider="huggingface")
        res = agent.validate_topic("Tema tranquilo")
        assert res["approved"] is True
        assert res["safe"] is True

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_deterministic_reject_short_circuits_llm(self, mock_create):
        """Layer ordering: deterministic PII rejection must NOT call the LLM."""
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="key", provider="huggingface")
        res = agent.validate_topic("Correo: juan@test.com en el artículo")
        assert res["approved"] is False
        mock_llm.generate.assert_not_called()

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_non_json_llm_response_no_false_rejection(self, mock_create):
        """REQ: LLM emitting non-JSON must not cause a false rejection."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "Este tema es completamente seguro e interesante."
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="key", provider="huggingface")
        res = agent.validate_topic("Cualquier tema válido")
        assert res["safe"] is True
        assert res["approved"] is True

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_article_validation_rejects_unsafe(self, mock_create):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = '{"safe": false, "reason": "Contiene datos privados"}'
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="key", provider="huggingface")
        res = agent.validate_article(
            {"title": "t", "description": "d", "content": "algún texto tranquilo"},
            niche="tech",
        )
        assert res["safe"] is False
        assert res["layer"] == "llm"

    @patch("aphra_blogger.llm.factory.create_llm_provider")
    def test_article_deterministic_reject_short_circuits(self, mock_create):
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm

        agent = SafetyAgent(api_key="key", provider="huggingface")
        res = agent.validate_article(
            {"title": "titulo", "description": "d", "content": "puedes llamar al 612345678 o escribir a pepe@mail.com"},
            niche="tech",
        )
        assert res["approved"] is False
        assert res["layer"].startswith("deterministic_")
        mock_llm.generate.assert_not_called()