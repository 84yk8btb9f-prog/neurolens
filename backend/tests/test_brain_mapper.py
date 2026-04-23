import json
import re
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np

# Patch model_manager before importing brain_mapper so no real model loads
_MOCK_SCORES = {
    "visual_cortex": 72, "face_social": 45, "amygdala": 68,
    "hippocampus": 55, "language_areas": 80, "reward_circuit": 61,
    "prefrontal": 49, "motor_action": 77,
}
_VALID_JSON = json.dumps(_MOCK_SCORES)


def _make_image() -> Image.Image:
    return Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))


def _mock_get(model_id=None):
    return MagicMock(name="model"), MagicMock(name="processor")


def test_regions_has_eight_entries():
    from app.brain_mapper import REGIONS
    assert len(REGIONS) == 8


def test_parse_vlm_output_clean_json():
    from app.brain_mapper import _parse_scores
    result = _parse_scores(_VALID_JSON)
    assert result["visual_cortex"] == 72
    assert all(0 <= v <= 100 for v in result.values())


def test_parse_vlm_output_fenced_json():
    from app.brain_mapper import _parse_scores
    fenced = f"```json\n{_VALID_JSON}\n```"
    result = _parse_scores(fenced)
    assert result["amygdala"] == 68


def test_parse_vlm_output_malformed_returns_fallback():
    from app.brain_mapper import _parse_scores
    result = _parse_scores("Sorry, I cannot analyze this.")
    assert len(result) == 8
    assert all(v == 50 for v in result.values())


def test_parse_vlm_output_clamps_out_of_range():
    from app.brain_mapper import _parse_scores
    bad = dict(_MOCK_SCORES)
    bad["visual_cortex"] = 150
    bad["amygdala"] = -10
    result = _parse_scores(json.dumps(bad))
    assert result["visual_cortex"] == 100
    assert result["amygdala"] == 0


def test_get_brain_scores_image(monkeypatch):
    from app import brain_mapper, model_manager
    monkeypatch.setattr(model_manager._manager, "get", _mock_get)
    with patch("app.brain_mapper._generate_scores", return_value=_VALID_JSON):
        scores = brain_mapper.get_brain_scores(image=_make_image())
    assert set(scores.keys()) == set(brain_mapper.REGIONS.keys())
    assert all(0 <= v <= 100 for v in scores.values())


def test_get_brain_scores_text(monkeypatch):
    from app import brain_mapper, model_manager
    monkeypatch.setattr(model_manager._manager, "get", _mock_get)
    with patch("app.brain_mapper._generate_scores", return_value=_VALID_JSON):
        scores = brain_mapper.get_brain_scores(text="Buy now!")
    assert len(scores) == 8


def test_get_brain_scores_requires_input():
    from app.brain_mapper import get_brain_scores
    with pytest.raises(ValueError, match="requires at least one"):
        get_brain_scores()


def test_get_brain_scores_multiple_images_averaged(monkeypatch):
    from app import brain_mapper, model_manager
    monkeypatch.setattr(model_manager._manager, "get", _mock_get)
    scores_a = dict(_MOCK_SCORES)
    scores_b = {k: 50 for k in _MOCK_SCORES}
    responses = [json.dumps(scores_a), json.dumps(scores_b)]
    with patch("app.brain_mapper._generate_scores", side_effect=responses):
        result = brain_mapper.get_brain_scores(images=[_make_image(), _make_image()])
    assert result["visual_cortex"] == round((72 + 50) / 2)


from app.recommendation_engine import get_recommendations, Recommendation

_ALL_KEYS = ["visual_cortex", "amygdala", "face_social", "hippocampus",
             "language_areas", "reward_circuit", "prefrontal", "motor_action"]


def test_get_recs_has_one_per_region():
    scores = {k: 50 for k in _ALL_KEYS}
    recs = get_recommendations(scores)
    assert len(recs) == 8
    assert len({r.region_key for r in recs}) == 8


def test_low_amygdala_shows_high_priority():
    scores = {k: 80 for k in _ALL_KEYS}
    scores["amygdala"] = 10
    recs = get_recommendations(scores)
    amygdala = [r for r in recs if r.region_key == "amygdala"]
    assert amygdala[0].priority == "high"


def test_all_high_scores_produce_no_high_priority():
    scores = {k: 90 for k in _ALL_KEYS}
    recs = get_recommendations(scores)
    assert all(r.priority != "high" for r in recs)
