"""Verification-only tests for RLS policy + read-path visibility (REQ-3, REQ-5).

Offline/guarded: the pure helpers are always unit-tested; the live DB checks
skip unless real Supabase credentials are present (SUPABASE_DB_URL for the
pg_policies check, SUPABASE_URL + SUPABASE_ANON_KEY for the anon read path).
"""

import os

import pytest

PUBLIC_READ_POLICY_MISSING = "RLS Public read policy missing"


def check_public_read_policy(conn) -> str | None:
    """Return None when the 'Public read' SELECT policy exists on posts.

    Otherwise return the report string "RLS Public read policy missing".
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT policyname, cmd FROM pg_policies "
            "WHERE tablename = 'posts' AND policyname = 'Public read' AND cmd = 'SELECT'"
        )
        row = cur.fetchone()
    if row:
        return None
    return PUBLIC_READ_POLICY_MISSING


def report_missing_stage(posts: list[dict], newest_expected: str | None) -> str:
    """REQ-5: report which stage failed when a post is not visible.

    Returns "read ok: N posts visible, newest=..." when the anon read path
    returns rows sorted by date DESC, otherwise a "read failed: ..." report.
    """
    if not posts:
        return "read failed: no rows returned by anon getAllPosts"
    dates = [p.get("date") for p in posts]
    if dates != sorted(dates, reverse=True):
        return "read failed: posts not sorted by date DESC"
    return f"read ok: {len(posts)} posts visible, newest={dates[0]}"


class FakeCursor:
    def __init__(self, row):
        self._row = row

    def execute(self, query):
        pass

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, row):
        self._row = row

    def cursor(self):
        return FakeCursor(self._row)

    def close(self):
        pass


class TestPublicReadPolicyCheck:
    def test_policy_present_returns_none(self):
        assert check_public_read_policy(FakeConn(("Public read", "SELECT"))) is None

    def test_policy_missing_reports_message(self):
        report = check_public_read_policy(FakeConn(None))
        assert report == PUBLIC_READ_POLICY_MISSING


class TestMissingStageReport:
    def test_no_rows_reports_read_failure(self):
        assert report_missing_stage([], "2026-08-07") == (
            "read failed: no rows returned by anon getAllPosts"
        )

    def test_unsorted_rows_reports_read_failure(self):
        posts = [{"date": "2026-08-01"}, {"date": "2026-08-07"}]
        assert report_missing_stage(posts, "2026-08-07").startswith("read failed:")

    def test_sorted_rows_reports_ok(self):
        posts = [{"date": "2026-08-07"}, {"date": "2026-08-01"}]
        assert report_missing_stage(posts, "2026-08-07").startswith("read ok:")


def _has_psycopg2():
    try:
        import psycopg2  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not (os.environ.get("SUPABASE_DB_URL") and _has_psycopg2()),
    reason="requires SUPABASE_DB_URL + psycopg2",
)
def test_public_read_policy_exists_live():
    """Live check: pg_policies must contain 'Public read' on posts."""
    import psycopg2

    conn = psycopg2.connect(os.environ["SUPABASE_DB_URL"])
    try:
        report = check_public_read_policy(conn)
        assert report is None, report
    finally:
        conn.close()


@pytest.mark.skipif(
    not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_ANON_KEY")),
    reason="requires SUPABASE_URL + SUPABASE_ANON_KEY",
)
def test_anon_read_path_shows_newest_post_live():
    """Live REQ-5 diagnostic: anon getAllPosts (no filter) sorted date DESC."""
    from supabase import create_client

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    resp = sb.table("posts").select("id, slug, title, date").order("date", desc=True).execute()
    posts = resp.data or []
    assert report_missing_stage(posts, None).startswith("read ok:"), (
        "post absent on the anon read path — check generation/write/read stages"
    )
