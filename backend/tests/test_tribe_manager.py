import time
import threading
import pytest
from unittest.mock import patch, MagicMock
from app.tribe_manager import TribeManager, TribeNotAvailableError


def _mock_load() -> MagicMock:
    return MagicMock(name="tribe_model")


def test_not_loaded_at_startup():
    mgr = TribeManager(idle_timeout=999, min_available_gb=0)
    assert not mgr.loaded


def test_unavailable_when_package_missing():
    with patch.object(TribeManager, "_check_available", return_value=False):
        mgr = TribeManager(idle_timeout=999, min_available_gb=0)
    assert not mgr.available


def test_get_triggers_load():
    with patch.object(TribeManager, "_check_available", return_value=True):
        mgr = TribeManager(idle_timeout=999, min_available_gb=0)
    with patch("app.tribe_manager._load_tribe", side_effect=_mock_load):
        model = mgr.get()
    assert mgr.loaded
    assert model is not None


def test_get_gives_same_instance():
    with patch.object(TribeManager, "_check_available", return_value=True):
        mgr = TribeManager(idle_timeout=999, min_available_gb=0)
    with patch("app.tribe_manager._load_tribe", side_effect=_mock_load):
        a = mgr.get()
        b = mgr.get()
    assert a is b


def test_get_raises_when_unavailable():
    with patch.object(TribeManager, "_check_available", return_value=False):
        mgr = TribeManager(idle_timeout=999, min_available_gb=0)
    with pytest.raises(TribeNotAvailableError):
        mgr.get()


def test_get_raises_on_low_memory():
    with patch.object(TribeManager, "_check_available", return_value=True):
        mgr = TribeManager(idle_timeout=999, min_available_gb=10_000)
    with pytest.raises(TribeNotAvailableError, match="GB free"):
        mgr.get()


def test_unload_clears_model():
    with patch.object(TribeManager, "_check_available", return_value=True):
        mgr = TribeManager(idle_timeout=999, min_available_gb=0)
    with patch("app.tribe_manager._load_tribe", side_effect=_mock_load):
        mgr.get()
    assert mgr.unload() is True
    assert not mgr.loaded
    assert mgr.unload() is False


def test_idle_watchdog_unloads():
    with patch.object(TribeManager, "_check_available", return_value=True):
        mgr = TribeManager(idle_timeout=1, min_available_gb=0)
    with patch("app.tribe_manager._load_tribe", side_effect=_mock_load):
        mgr.get()
    assert mgr.loaded
    time.sleep(2.5)
    assert not mgr.loaded


def test_concurrent_get_loads_once():
    with patch.object(TribeManager, "_check_available", return_value=True):
        mgr = TribeManager(idle_timeout=999, min_available_gb=0)
    call_count = 0

    def counting_load():
        nonlocal call_count
        time.sleep(0.05)
        call_count += 1
        return MagicMock()

    with patch("app.tribe_manager._load_tribe", side_effect=counting_load):
        threads = [threading.Thread(target=mgr.get) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    assert call_count == 1


def test_status_shape_when_unavailable():
    with patch.object(TribeManager, "_check_available", return_value=False):
        mgr = TribeManager(idle_timeout=120, min_available_gb=0)
    status = mgr.status()
    assert status["available"] is False
    assert status["loaded"] is False
    assert status["idle_timeout_seconds"] == 120
    assert "idle_for_seconds" in status
