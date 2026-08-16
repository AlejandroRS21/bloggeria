"""Tests for Modal FIFO queue, bounded concurrency, deduplication and rate limit.

All tests run offline: queue/job-store/rate-store are injected as process-local
fakes (or the webhook's local in-memory backends). No Modal cloud state is
ever touched (REQ-TEST-5.1, REQ-TEST-5.2).
"""

import time
from datetime import datetime
from types import SimpleNamespace

import modal_app
from modal_app import (
    JOB_STALE_TIMEOUT_SECONDS,
    _client_ip,
    _drain_once,
    _is_job_active,
    _mark_job,
    _MemoryQueue,
    _rate_limited,
    enqueue_job,
    webhook,
)


def _payload(job_id: str) -> dict:
    return {
        "blogger_urls": ["https://simonwillison.net"],
        "topic": "IA en el desarrollo web",
        "job_id": job_id,
        "provider": "gemini",
        "niche": "tech",
    }


class TestFifoQueueOrder:
    def test_drain_processes_in_fifo_order(self):
        queue = _MemoryQueue()
        store = {}
        for jid in ("job-a", "job-b", "job-c"):
            queue.put(_payload(jid))

        spawned = []
        drained = _drain_once(
            queue=queue, job_store=store, max_conc=5,
            spawner=lambda **kw: spawned.append(kw["job_id"]),
        )

        assert drained == 3
        assert spawned == ["job-a", "job-b", "job-c"]


class TestMaxConcurrency:
    def test_drain_respects_running_capacity(self):
        queue = _MemoryQueue()
        for jid in ("job-a", "job-b", "job-c"):
            queue.put(_payload(jid))

        # One non-stale job already running → only 1 slot free with MAX=2.
        store = {
            "job-running": {
                "status": "running",
                "updated_at": datetime.now().timestamp(),
                "ip": None,
            }
        }

        spawned = []
        drained = _drain_once(
            queue=queue, job_store=store, max_conc=2,
            spawner=lambda **kw: spawned.append(kw["job_id"]),
        )

        assert drained == 1
        assert spawned == ["job-a"]
        # jobs b and c stay queued (not marked, not spawned)
        assert queue.len() == 2


class TestStaleJobRecovery:
    def test_stale_running_does_not_count_toward_limit(self):
        queue = _MemoryQueue()
        for jid in ("job-a", "job-b"):
            queue.put(_payload(jid))

        old = datetime.now().timestamp() - JOB_STALE_TIMEOUT_SECONDS - 1
        store = {
            "job-zombie": {"status": "running", "updated_at": old, "ip": None},
        }

        spawned = []
        drained = _drain_once(
            queue=queue, job_store=store, max_conc=2,
            spawner=lambda **kw: spawned.append(kw["job_id"]),
        )

        assert drained == 2
        assert spawned == ["job-a", "job-b"]


class TestJobLifecycle:
    def test_drain_marks_spawned_job_running(self):
        queue = _MemoryQueue()
        queue.put(_payload("job-x"))
        store = {}

        _drain_once(queue=queue, job_store=store, max_conc=1, spawner=lambda **kw: None)

        assert store["job-x"]["status"] == "running"

    def test_mark_job_done(self):
        store = {}
        _mark_job("job-x", "queued", store=store)
        _mark_job("job-x", "done", store=store)
        assert store["job-x"]["status"] == "done"
        assert "updated_at" in store["job-x"]

    def test_drain_marks_failed_when_spawn_fails(self):
        queue = _MemoryQueue()
        queue.put(_payload("job-fail"))
        store = {}

        def boom(**kw):
            raise RuntimeError("spawn failed")

        _drain_once(queue=queue, job_store=store, max_conc=1, spawner=boom)

        assert store["job-fail"]["status"] == "failed"
        assert "spawn failed" in store["job-fail"]["error"]
        assert queue.len() == 0


class TestJobDeduplication:
    def _fresh_done(self, ts_offset: float) -> dict:
        return {
            "status": "done",
            "updated_at": datetime.now().timestamp() - ts_offset,
            "ip": None,
        }

    def test_active_when_queued(self):
        store = {"job-x": {"status": "queued", "updated_at": time.time(), "ip": None}}
        assert _is_job_active("job-x", store=store) is True

    def test_active_when_running(self):
        store = {"job-x": {"status": "running", "updated_at": time.time(), "ip": None}}
        assert _is_job_active("job-x", store=store) is True

    def test_active_when_done_recently(self):
        store = {"job-x": self._fresh_done(5)}
        assert _is_job_active("job-x", store=store) is True

    def test_inactive_when_done_old(self):
        store = {"job-x": self._fresh_done(120)}
        assert _is_job_active("job-x", store=store) is False

    def test_inactive_unknown_job(self):
        assert _is_job_active("nope", store={}) is False

    def test_webhook_rejects_duplicate_job_id(self, monkeypatch):
        monkeypatch.setattr(modal_app, "moderate_topic", lambda topic, **kw: {"approved": True})
        monkeypatch.setattr(modal_app, "_is_job_active", lambda jid, store=None: True)
        result = webhook.local(_payload("job-dup"))
        assert result["success"] is False
        assert "ya está en ejecución" in result["error"]

    def test_webhook_generates_job_id_when_missing(self, monkeypatch):
        monkeypatch.setattr(modal_app, "moderate_topic", lambda topic, **kw: {"approved": True})
        captured = {}
        monkeypatch.setattr(
            modal_app, "enqueue_job",
            lambda payload, **kw: captured.update(payload),
        )
        result = webhook.local({"blogger_urls": ["https://x.com"], "topic": "t"})
        assert result["success"] is True
        assert result["job_id"].startswith("job-")
        assert captured.get("job_id") == result["job_id"]


class TestRateLimit:
    def test_ip_blocked_after_max(self):
        store = {}
        for _ in range(5):
            assert _rate_limited("1.2.3.4", store=store) is False
        assert _rate_limited("1.2.3.4", store=store) is True

    def test_different_ips_independent(self):
        store = {}
        for _ in range(6):
            _rate_limited("1.2.3.4", store=store)
        assert _rate_limited("5.6.7.8", store=store) is False

    def test_window_rolls_over_old_timestamps(self):
        store = {
            "1.2.3.4": [datetime.now().timestamp() - 4000] * 5,  # older than 3600s window
        }
        assert _rate_limited("1.2.3.4", store=store) is False

    def test_configurable_max(self):
        store = {}
        assert _rate_limited("9.9.9.9", store=store, max_reqs=2) is False
        assert _rate_limited("9.9.9.9", store=store, max_reqs=2) is False
        assert _rate_limited("9.9.9.9", store=store, max_reqs=2) is True

    def test_no_ip_bypasses_and_does_not_write(self):
        store = {}
        assert _rate_limited(None, store=store) is False
        assert store == {}

    def test_webhook_rate_limit_response(self, monkeypatch):
        monkeypatch.setattr(modal_app, "moderate_topic", lambda topic, **kw: {"approved": True})
        monkeypatch.setattr(modal_app, "_rate_limited", lambda ip, **kw: True)
        result = webhook.local(_payload("job-rl"))
        assert result["success"] is False
        assert "Límite de tasa excedido" in result["error"]

    def test_webhook_enqueues_when_under_limit(self, monkeypatch):
        monkeypatch.setattr(modal_app, "moderate_topic", lambda topic, **kw: {"approved": True})
        captured = {}
        monkeypatch.setattr(
            modal_app, "enqueue_job",
            lambda payload, **kw: captured.update(payload),
        )
        result = webhook.local(_payload("job-ok"))
        assert result == {"success": True, "job_id": "job-ok", "status": "queued"}
        assert captured.get("job_id") == "job-ok"


class TestClientIp:
    def test_client_ip_prefers_client_host(self):
        request = SimpleNamespace(
            client=SimpleNamespace(host="10.0.0.1"),
            headers={"x-forwarded-for": "1.2.3.4"},
        )
        assert _client_ip(request) == "10.0.0.1"

    def test_client_ip_falls_back_to_xff(self):
        request = SimpleNamespace(
            client=None,
            headers={"x-forwarded-for": "1.2.3.4, 5.6.7.8"},
        )
        assert _client_ip(request) == "1.2.3.4"

    def test_client_ip_none_when_neither(self):
        request = SimpleNamespace(client=None, headers={})
        assert _client_ip(request) is None


class TestPruneDoneJobs:
    def test_prune_removes_old_done(self):
        store = {
            "job-old": {
                "status": "done",
                "updated_at": datetime.now().timestamp() - 7300,
                "ip": None,
            }
        }
        _drain_once(queue=_MemoryQueue(), job_store=store)
        assert "job-old" not in store

    def test_prune_keeps_recent_done(self):
        store = {
            "job-recent": {
                "status": "done",
                "updated_at": datetime.now().timestamp() - 120,
                "ip": None,
            }
        }
        _drain_once(queue=_MemoryQueue(), job_store=store)
        assert store["job-recent"]["status"] == "done"

    def test_prune_never_removes_non_done(self):
        old = datetime.now().timestamp() - 100000
        store = {
            "job-running": {"status": "running", "updated_at": old, "ip": None},
            "job-queued": {"status": "queued", "updated_at": old, "ip": None},
            "job-failed": {"status": "failed", "updated_at": old, "ip": None},
        }
        _drain_once(queue=_MemoryQueue(), job_store=store)
        assert set(store) == {"job-running", "job-queued", "job-failed"}


class TestEnqueueJob:
    def test_enqueue_adds_to_queue_and_marks_queued(self):
        queue = _MemoryQueue()
        store = {}
        enqueue_job(_payload("job-q"), queue=queue, store=store)
        assert queue.len() == 1
        assert store["job-q"]["status"] == "queued"
        assert queue.get()["job_id"] == "job-q"
