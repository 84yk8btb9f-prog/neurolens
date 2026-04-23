import pytest


@pytest.fixture(autouse=True)
def _disable_memory_guard():
    """Tests don't respect the production memory guard — they mock the loader
    and may run on machines where the VLM is already resident in RAM."""
    from app.model_manager import _manager
    original = _manager._min_available_gb
    _manager._min_available_gb = 0
    yield
    _manager._min_available_gb = original
