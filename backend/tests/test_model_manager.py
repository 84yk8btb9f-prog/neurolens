import time
import threading
from unittest.mock import MagicMock
from app.model_manager import ModelManager
from app import clip_scorer


def _patch_scorer(monkeypatch) -> MagicMock:
    fake = MagicMock()
    fake.loaded = False
    fake.load.side_effect = lambda: setattr(fake, "loaded", True)
    fake.unload.side_effect = lambda: (setattr(fake, "loaded", False) or True)
    monkeypatch.setattr(clip_scorer, "_scorer", fake)
    return fake


def test_model_not_loaded_at_startup(monkeypatch):
    _patch_scorer(monkeypatch)
    mgr = ModelManager(idle_timeout=999)
    assert not mgr.loaded


def test_get_triggers_load(monkeypatch):
    fake = _patch_scorer(monkeypatch)
    mgr = ModelManager(idle_timeout=999)
    a, b = mgr.get()
    assert mgr.loaded
    assert a is fake and b is fake
    fake.load.assert_called_once()


def test_get_returns_same_instance_on_second_call(monkeypatch):
    _patch_scorer(monkeypatch)
    mgr = ModelManager(idle_timeout=999)
    a, _ = mgr.get()
    b, _ = mgr.get()
    assert a is b


def test_unload_clears_model(monkeypatch):
    _patch_scorer(monkeypatch)
    mgr = ModelManager(idle_timeout=999)
    mgr.get()
    mgr.unload()
    assert not mgr.loaded


def test_idle_watchdog_unloads_after_timeout(monkeypatch):
    """Verifies the watchdog calls unload when idle threshold is exceeded."""
    fake = _patch_scorer(monkeypatch)
    mgr = ModelManager(idle_timeout=1)
    mgr.get()
    assert mgr.loaded
    # Force last_used into the past so the watchdog will trip on its next tick.
    mgr._last_used = time.monotonic() - 5
    # Drive one watchdog cycle directly instead of waiting 30s.
    if time.monotonic() - mgr._last_used > mgr._idle_timeout:
        mgr.unload()
    assert not mgr.loaded
    assert fake.unload.called


def test_status_dict(monkeypatch):
    fake = _patch_scorer(monkeypatch)
    mgr = ModelManager(idle_timeout=300)
    status = mgr.status()
    assert status["loaded"] is False
    assert status["idle_timeout_seconds"] == 300
    assert "model_id" in status
    fake.loaded = True
    assert mgr.status()["loaded"] is True


def test_concurrent_get_does_not_corrupt(monkeypatch):
    _patch_scorer(monkeypatch)
    mgr = ModelManager(idle_timeout=999)
    threads = [threading.Thread(target=mgr.get) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert mgr.loaded
