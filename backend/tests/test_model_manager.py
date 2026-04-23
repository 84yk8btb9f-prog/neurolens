import time
import threading
from unittest.mock import patch, MagicMock
import pytest
from app.model_manager import ModelManager, LowMemoryError


def _mock_load(path):
    return MagicMock(name="model"), MagicMock(name="processor")


def _mgr(idle_timeout: int = 999) -> ModelManager:
    return ModelManager(idle_timeout=idle_timeout, min_available_gb=0)


def test_model_not_loaded_at_startup():
    mgr = _mgr()
    assert not mgr.loaded


def test_get_triggers_load():
    mgr = _mgr()
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        model, proc = mgr.get()
    assert mgr.loaded
    assert model is not None


def test_get_returns_same_instance_on_second_call():
    mgr = _mgr()
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        m1, p1 = mgr.get()
        m2, p2 = mgr.get()
    assert m1 is m2


def test_unload_clears_model():
    mgr = _mgr()
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        mgr.get()
    mgr.unload()
    assert not mgr.loaded


def test_idle_watchdog_unloads_after_timeout():
    mgr = _mgr(idle_timeout=1)
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        mgr.get()
    assert mgr.loaded
    time.sleep(2.5)
    assert not mgr.loaded


def test_status_dict():
    mgr = ModelManager(idle_timeout=300, min_available_gb=0)
    status = mgr.status()
    assert status["loaded"] is False
    assert status["idle_timeout_seconds"] == 300
    assert "available_memory_gb" in status
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        mgr.get()
    assert mgr.status()["loaded"] is True


def test_concurrent_get_loads_only_once():
    mgr = _mgr()
    call_count = 0

    def counting_load(path):
        nonlocal call_count
        time.sleep(0.05)
        call_count += 1
        return MagicMock(), MagicMock()

    with patch("app.model_manager._load_vlm", side_effect=counting_load):
        threads = [threading.Thread(target=mgr.get) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert call_count == 1


def test_low_memory_raises_before_load():
    # Require more memory than any machine will plausibly have free.
    mgr = ModelManager(idle_timeout=999, min_available_gb=10_000)
    with patch("app.model_manager._load_vlm", side_effect=_mock_load) as mock_load:
        with pytest.raises(LowMemoryError):
            mgr.get()
    mock_load.assert_not_called()
    assert not mgr.loaded
