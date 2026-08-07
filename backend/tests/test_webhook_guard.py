"""Tests for modal_app cron + webhook guards (REQ-1, REQ-2, REQ-4).

These tests exercise the undecorated logic seams of modal_app so they run
without a deployed Modal runtime. The Modal Function wrappers delegate to
these plain functions.
"""

from unittest.mock import Mock

from modal_app import (
    EXPECTED_SUPABASE_PROJECT_ID,
    _run_daily_cleanup,
    persist_post,
    supabase_project_id,
)


class TestDailyCleanupDryRun:
    def test_runs_dry_run_by_default(self, monkeypatch):
        captured = {}

        def fake_cleanup_posts(**kwargs):
            captured.update(kwargs)

        monkeypatch.setattr("cleanup_supabase.cleanup_posts", fake_cleanup_posts)
        _run_daily_cleanup()
        assert captured["dry_run"] is True

    def test_explicit_opt_in_disables_dry_run(self, monkeypatch):
        captured = {}

        def fake_cleanup_posts(**kwargs):
            captured.update(kwargs)

        monkeypatch.setattr("cleanup_supabase.cleanup_posts", fake_cleanup_posts)
        _run_daily_cleanup(dry_run=False)
        assert captured["dry_run"] is False


class TestSupabaseProjectId:
    def test_extracts_project_id_from_url(self):
        url = "https://stqtpbdzqgcbaqdvrsij.supabase.co"
        assert supabase_project_id(url) == "stqtpbdzqgcbaqdvrsij"

    def test_detects_foreign_project(self):
        url = "https://kcpfslzzldokgptbqmzx.supabase.co"
        assert supabase_project_id(url) == "kcpfslzzldokgptbqmzx"

    def test_returns_none_for_unparseable_url(self):
        assert supabase_project_id("not-a-url") is None


class TestProjectMismatchGuard:
    def test_mismatch_is_rejected_with_both_ids_logged(self, capsys):
        result = persist_post(
            sb=None,
            post_data={"id": "w1"},
            resolved_project="kcpfslzzldokgptbqmzx",
        )
        out = capsys.readouterr().out
        assert result["success"] is False
        assert "kcpfslzzldokgptbqmzx" in result["error"]
        assert EXPECTED_SUPABASE_PROJECT_ID in result["error"]
        assert "kcpfslzzldokgptbqmzx" in out
        assert "REJECTED" in out

    def test_matching_project_writes_and_logs_success(self, capsys):
        fake_sb = Mock()
        fake_sb.table.return_value.upsert.return_value.execute.return_value = Mock(
            data=[{"id": "w1"}]
        )
        result = persist_post(
            sb=fake_sb,
            post_data={"id": "w1", "slug": "s1"},
            resolved_project=EXPECTED_SUPABASE_PROJECT_ID,
        )
        out = capsys.readouterr().out
        assert result["success"] is True
        assert "w1" in out
        assert "status=success" in out

    def test_upsert_failure_logs_error_and_returns_failure(self, capsys):
        fake_sb = Mock()
        fake_sb.table.return_value.upsert.side_effect = RuntimeError("RLS denied insert")
        result = persist_post(
            sb=fake_sb,
            post_data={"id": "w1", "slug": "s1"},
            resolved_project=EXPECTED_SUPABASE_PROJECT_ID,
        )
        out = capsys.readouterr().out
        assert result["success"] is False
        assert "RLS denied insert" in result["error"]
        assert "RLS denied insert" in out
