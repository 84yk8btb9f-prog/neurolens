import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from app.tribe_manager import TribeNotAvailableError


def _make_mock_model(n_timesteps=10, n_vertices=20484):
    model = MagicMock()
    model.get_events_dataframe.return_value = MagicMock()
    preds = np.random.default_rng(0).standard_normal((n_timesteps, n_vertices))
    model.predict.return_value = (preds, MagicMock())
    return model


def _fake_masks():
    return {
        "visual_cortex": np.array([True] * 100 + [False] * (20484 - 100)),
        "face_social": np.array([False] * 100 + [True] * 100 + [False] * (20484 - 200)),
        "language_areas": np.array([False] * 200 + [True] * 100 + [False] * (20484 - 300)),
        "motor_action": np.array([False] * 300 + [True] * 100 + [False] * (20484 - 400)),
        "prefrontal": np.array([False] * 400 + [True] * 100 + [False] * (20484 - 500)),
    }


def test_tribe_scorer_unavailable_path(tmp_path):
    fake_video = tmp_path / "test.mp4"
    fake_video.write_bytes(b"fake")
    with patch("app.tribe_scorer.get_tribe_manager") as mock_fn:
        mock_mgr = MagicMock()
        mock_mgr.available = False
        mock_mgr.get.side_effect = TribeNotAvailableError("not installed")
        mock_fn.return_value = mock_mgr
        from app.tribe_scorer import score_video
        result = score_video(str(fake_video))
    assert result is None


def test_tribe_scorer_five_regions(tmp_path):
    fake_video = tmp_path / "test.mp4"
    fake_video.write_bytes(b"fake")
    with patch("app.tribe_scorer.get_tribe_manager") as mock_fn, \
         patch("app.tribe_scorer._get_masks", return_value=_fake_masks()):
        mock_mgr = MagicMock()
        mock_mgr.available = True
        mock_mgr.get.return_value = _make_mock_model()
        mock_fn.return_value = mock_mgr
        from app.tribe_scorer import score_video
        result = score_video(str(fake_video))
    assert result is not None
    assert set(result.keys()) == {
        "visual_cortex", "face_social", "language_areas", "motor_action", "prefrontal"
    }


def test_tribe_scorer_valid_range(tmp_path):
    fake_video = tmp_path / "test.mp4"
    fake_video.write_bytes(b"fake")
    all_masks = {k: np.ones(20484, dtype=bool)
                 for k in ["visual_cortex", "face_social", "language_areas", "motor_action", "prefrontal"]}
    with patch("app.tribe_scorer.get_tribe_manager") as mock_fn, \
         patch("app.tribe_scorer._get_masks", return_value=all_masks):
        mock_mgr = MagicMock()
        mock_mgr.available = True
        mock_mgr.get.return_value = _make_mock_model()
        mock_fn.return_value = mock_mgr
        from app.tribe_scorer import score_video
        result = score_video(str(fake_video))
    for region, val in result.items():
        assert isinstance(val, int), f"{region} not int"
        assert 0 <= val <= 100, f"{region}={val} out of range"


def test_tribe_scorer_handles_error(tmp_path):
    fake_video = tmp_path / "test.mp4"
    fake_video.write_bytes(b"fake")
    with patch("app.tribe_scorer.get_tribe_manager") as mock_fn:
        mock_mgr = MagicMock()
        mock_mgr.available = True
        broken = MagicMock()
        broken.get_events_dataframe.side_effect = RuntimeError("MPS error")
        mock_mgr.get.return_value = broken
        mock_fn.return_value = mock_mgr
        from app.tribe_scorer import score_video
        result = score_video(str(fake_video))
    assert result is None
