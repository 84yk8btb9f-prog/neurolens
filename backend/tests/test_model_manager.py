import time
import threading
from unittest.mock import patch, MagicMock
import pytest
from app.model_manager import ModelManager


def _mock_load(path):
    return MagicMock(name="model"), MagicMock(name="processor")


def test_model_not_loaded_at_startup():
    mgr = ModelManager(idle_timeout=999)
    assert not mgr.loaded


def test_get_triggers_load():
    mgr = ModelManager(idle_timeout=999)
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        model, proc = mgr.get()
    assert mgr.loaded
    assert model is not None


def test_get_returns_same_instance_on_second_call():
    mgr = ModelManager(idle_timeout=999)
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        m1, p1 = mgr.get()
        m2, p2 = mgr.get()
    assert m1 is m2


def test_unload_clears_model():
    mgr = ModelManager(idle_timeout=999)
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        mgr.get()
    mgr.unload()
    assert not mgr.loaded


def test_idle_watchdog_unloads_after_timeout():
    mgr = ModelManager(idle_timeout=1)  # 1 second for test
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        mgr.get()
    assert mgr.loaded
    time.sleep(2.5)  # wait past timeout + watchdog cycle
    assert not mgr.loaded


def test_status_dict():
    mgr = ModelManager(idle_timeout=300)
    status = mgr.status()
    assert status["loaded"] is False
    assert status["idle_timeout_seconds"] == 300
    with patch("app.model_manager._load_vlm", side_effect=_mock_load):
        mgr.get()
    assert mgr.status()["loaded"] is True
