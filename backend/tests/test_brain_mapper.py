import pytest
from unittest.mock import MagicMock
import numpy as np
from PIL import Image

from app import brain_mapper, clip_scorer
from app.recommendation_engine import get_recommendations


_ALL_KEYS = ["visual_cortex", "amygdala", "face_social", "hippocampus",
             "language_areas", "reward_circuit", "prefrontal", "motor_action"]


def _make_image() -> Image.Image:
    return Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))


@pytest.fixture
def mock_scorer(monkeypatch):
    """Replace the global CLIP scorer with a mock that returns deterministic scores."""
    fake = MagicMock()
    fake.loaded = True
    fake.score_image.return_value = {k: 60 for k in _ALL_KEYS}
    fake.score_text.return_value = {k: 40 for k in _ALL_KEYS}
    monkeypatch.setattr(clip_scorer, "_scorer", fake)
    return fake


def test_regions_has_eight_entries():
    assert len(brain_mapper.REGIONS) == 8


def test_get_brain_scores_image(mock_scorer):
    scores = brain_mapper.get_brain_scores(image=_make_image())
    assert set(scores.keys()) == set(brain_mapper.REGIONS.keys())
    assert all(0 <= v <= 100 for v in scores.values())
    assert all(v == 60 for v in scores.values())


def test_get_brain_scores_text(mock_scorer):
    scores = brain_mapper.get_brain_scores(text="Buy now!")
    assert len(scores) == 8
    assert all(v == 40 for v in scores.values())


def test_get_brain_scores_requires_input():
    with pytest.raises(ValueError, match="requires at least one"):
        brain_mapper.get_brain_scores()


def test_get_brain_scores_multiple_images_averaged(mock_scorer):
    mock_scorer.score_image.side_effect = [
        {k: 80 for k in _ALL_KEYS},
        {k: 40 for k in _ALL_KEYS},
    ]
    result = brain_mapper.get_brain_scores(images=[_make_image(), _make_image()])
    assert result["visual_cortex"] == 60


def test_get_brain_scores_image_and_text_combined(mock_scorer):
    result = brain_mapper.get_brain_scores(image=_make_image(), text="hello")
    # mean of 60 (image) and 40 (text) = 50
    assert result["visual_cortex"] == 50


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
