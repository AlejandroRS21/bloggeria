"""Tests for Modal packaging (REQ-BE-MODAL).

Verifies the Modal image build mounts backend/profiles/ so serverless
workers can resolve pre-baked style profiles at runtime. The real `modal`
package is stubbed to keep the test offline and deterministic.
"""

import importlib
import sys

import pytest


def _load_modal_app(monkeypatch, calls):
    """Import modal_app with a stubbed `modal` that records image-build calls."""

    class FakeImage:
        def debian_slim(self, *a, **k):
            return self

        def pip_install_from_requirements(self, *a, **k):
            return self

        def apt_install(self, *a, **k):
            return self

        def pip_install(self, *a, **k):
            return self

        def add_local_dir(self, local, **kw):
            calls.append(("add_local_dir", local, kw))
            return self

        def add_local_file(self, *a, **k):
            return self

    def _debian(*a, **k):
        return FakeImage()

    class FakeApp:
        @staticmethod
        def function(*a, **k):
            return lambda f: f

    class FakeSecret:
        @staticmethod
        def from_name(*a, **k):
            return object()

    class FakeCls:
        @staticmethod
        def from_name(*a, **k):
            return None

    class FakeModal:
        App = staticmethod(lambda *a, **k: FakeApp())
        Image = type("Image", (), {"debian_slim": staticmethod(_debian)})
        fastapi_endpoint = staticmethod(lambda *a, **k: lambda f: f)
        Cron = staticmethod(lambda *a, **k: None)
        Secret = FakeSecret
        Cls = FakeCls

    monkeypatch.setitem(sys.modules, "modal", FakeModal())
    if "modal_app" in sys.modules:
        importlib.reload(sys.modules["modal_app"])
    return importlib.import_module("modal_app")


class TestModalProfilesMount:
    def test_image_mounts_profiles_dir(self, monkeypatch):
        calls = []
        _load_modal_app(monkeypatch, calls)

        dir_mounts = [c for c in calls if c[0] == "add_local_dir"]
        assert dir_mounts, "image build must call add_local_dir at least once\n" + repr(calls)

        profile_mounts = [
            (str(local), kw)
            for kind, local, kw in dir_mounts
            if str(local).endswith(("profiles", "/profiles"))
        ]
        assert profile_mounts, "no backend/profiles mount found in image build\n" + repr(dir_mounts)
        _, kw = profile_mounts[0]
        assert kw.get("remote_path") == "/root/backend/profiles"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
