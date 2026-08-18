"""Tests for FallbackProvider chain behaviour."""
import pytest

from aphra_blogger.llm.base import LLMProvider, LLMResponse, LLMConfig
from aphra_blogger.llm.fallback_provider import FallbackProvider


class _StubProvider(LLMProvider):
    def __init__(self, name, *, available=True, fail=False, empty=False):
        super().__init__(LLMConfig(model=name))
        self._name = name
        self._available = available
        self._fail = fail
        self._empty = empty
        self.calls = 0

    def is_available(self):
        return self._available

    def chat_completion(self, messages, temperature=None, max_tokens=None):
        self.calls += 1
        if self._fail:
            raise RuntimeError(f"{self._name} boom")
        content = "" if self._empty else f"ok from {self._name}"
        return LLMResponse(content=content, model=self._name,
                           provider=self._name, finish_reason="stop")


def test_first_provider_used_when_healthy():
    a = _StubProvider("A")
    b = _StubProvider("B")
    fb = FallbackProvider([a, b], labels=["A", "B"], retries_per_provider=1)
    resp = fb.generate("hi")
    assert resp == "ok from A"
    assert fb.last_provider_used == "A"
    assert b.calls == 0


def test_falls_over_on_failure():
    a = _StubProvider("A", fail=True)
    b = _StubProvider("B")
    fb = FallbackProvider([a, b], labels=["A", "B"], retries_per_provider=1, backoff_seconds=0)
    resp = fb.generate("hi")
    assert resp == "ok from B"
    assert fb.last_provider_used == "B"
    assert a.calls == 1


def test_skips_unavailable_and_empty():
    a = _StubProvider("A", available=False)
    b = _StubProvider("B", empty=True)
    c = _StubProvider("C")
    fb = FallbackProvider([a, b, c], labels=["A", "B", "C"], retries_per_provider=1, backoff_seconds=0)
    resp = fb.generate("hi")
    assert resp == "ok from C"
    assert a.calls == 0  # unavailable, never called
    assert b.calls == 1  # tried, returned empty


def test_raises_when_all_fail():
    a = _StubProvider("A", fail=True)
    b = _StubProvider("B", fail=True)
    fb = FallbackProvider([a, b], labels=["A", "B"], retries_per_provider=1, backoff_seconds=0)
    with pytest.raises(RuntimeError, match="All providers failed"):
        fb.generate("hi")


def test_is_available_reflects_any_child():
    a = _StubProvider("A", available=False)
    b = _StubProvider("B", available=True)
    assert FallbackProvider([a, b]).is_available() is True
    assert FallbackProvider([_StubProvider("X", available=False)]).is_available() is False
