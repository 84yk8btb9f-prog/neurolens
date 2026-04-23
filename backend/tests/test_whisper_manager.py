import time
import threading
from unittest.mock import patch, MagicMock
from app.whisper_manager import WhisperManager


def _mock_load(name):
    return MagicMock(name="whisper")


def test_not_loaded_at_startup():
    mgr = WhisperManager(idle_timeout=999)
    assert not mgr.loaded


def test_get_triggers_load():
    mgr = WhisperManager(idle_timeout=999)
    with patch("app.whisper_manager._load_whisper", side_effect=_mock_load):
        model = mgr.get()
    assert mgr.loaded
    assert model is not None


def test_get_returns_same_instance():
    mgr = WhisperManager(idle_timeout=999)
    with patch("app.whisper_manager._load_whisper", side_effect=_mock_load):
        a = mgr.get()
        b = mgr.get()
    assert a is b


def test_unload_clears_model():
    mgr = WhisperManager(idle_timeout=999)
    with patch("app.whisper_manager._load_whisper", side_effect=_mock_load):
        mgr.get()
    assert mgr.unload() is True
    assert not mgr.loaded
    assert mgr.unload() is False


def test_idle_watchdog_unloads():
    mgr = WhisperManager(idle_timeout=1)
    with patch("app.whisper_manager._load_whisper", side_effect=_mock_load):
        mgr.get()
    assert mgr.loaded
    time.sleep(2.5)
    assert not mgr.loaded


def test_concurrent_get_loads_once():
    mgr = WhisperManager(idle_timeout=999)
    call_count = 0

    def counting_load(name):
        nonlocal call_count
        time.sleep(0.05)
        call_count += 1
        return MagicMock()

    with patch("app.whisper_manager._load_whisper", side_effect=counting_load):
        threads = [threading.Thread(target=mgr.get) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert call_count == 1


def test_status_shape():
    mgr = WhisperManager(idle_timeout=120)
    status = mgr.status()
    assert status["loaded"] is False
    assert status["idle_timeout_seconds"] == 120
    assert "idle_for_seconds" in status
