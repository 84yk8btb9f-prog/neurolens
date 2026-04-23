import pytest


@pytest.fixture(autouse=True)
def _disable_memory_guard():
    """Tests don't respect the production memory guard."""
    from app.model_manager import _manager as vlm_manager
    original_vlm = vlm_manager._min_available_gb
    vlm_manager._min_available_gb = 0

    from app.tribe_manager import _manager as tribe_manager
    original_tribe = tribe_manager._min_available_gb
    tribe_manager._min_available_gb = 0

    yield

    vlm_manager._min_available_gb = original_vlm
    tribe_manager._min_available_gb = original_tribe
