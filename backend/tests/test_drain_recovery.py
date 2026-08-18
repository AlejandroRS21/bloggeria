"""Tests for drain recovery: stale-running requeue + payload persistence."""
import time

from aphra_blogger import llm  # noqa: F401  (ensure package importable)

# The drain helpers live in modal_app.py which imports modal; guard import.
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "modal_app", "modal_app.py")
if spec and spec.loader:
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # modal SDK may not be importable here
        mod = None
        _IMPORT_ERR = e
else:
    mod = None
    _IMPORT_ERR = None


class FakeQueue:
    def __init__(self):
        self.items = []

    def put(self, payload):
        self.items.append(payload)

    def get(self, block=False):
        if not self.items:
            raise Exception("empty")
        return self.items.pop(0)

    def len(self):
        return len(self.items)


class FakeStore(dict):
    pass


def test_requeue_stale_running():
    if mod is None:
        import pytest
        pytest.skip(f"modal_app import failed: {_IMPORT_ERR}")
    store = FakeStore()
    queue = FakeQueue()
    now = time.time()
    store["stale-job"] = {
        "status": "running",
        "updated_at": now - 3600,  # 1h ago -> stale
        "payload": {"topic": "x", "blogger_urls": ["https://a.com"]},
    }
    store["fresh-job"] = {
        "status": "running",
        "updated_at": now - 10,  # 10s ago -> not stale
        "payload": {"topic": "y"},
    }
    n = mod._requeue_stale_running(store, queue, stale_after=600)
    assert n == 1
    assert len(queue.items) == 1
    assert queue.items[0]["job_id"] == "stale-job"
    assert queue.items[0]["topic"] == "x"
    assert store["stale-job"]["status"] == "queued"


def test_mark_job_persists_payload():
    if mod is None:
        import pytest
        pytest.skip(f"modal_app import failed: {_IMPORT_ERR}")
    store = FakeStore()
    mod._mark_job("j1", "queued", store=store)
    store["j1"] = {**store["j1"], "payload": {"topic": "t", "job_id": "j1"}}
    mod._mark_job("j1", "running", store=store)
    assert store["j1"]["payload"]["topic"] == "t"
    assert store["j1"]["status"] == "running"


def test_enqueue_persists_payload():
    if mod is None:
        import pytest
        pytest.skip(f"modal_app import failed: {_IMPORT_ERR}")
    store = FakeStore()
    queue = FakeQueue()
    payload = {"topic": "t", "blogger_urls": ["https://a.com"], "job_id": "j2"}
    mod.enqueue_job(payload, queue=queue, store=store)
    assert store["j2"]["payload"]["topic"] == "t"
    assert queue.len() == 1
