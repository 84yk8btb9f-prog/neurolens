# backend/tests/test_brain_mapper.py
import pytest
from PIL import Image
import numpy as np
from app.brain_mapper import get_brain_scores, REGIONS, normalize_score


def test_regions_has_eight_entries():
    assert len(REGIONS) == 8


def test_normalize_score_clamps_low():
    assert normalize_score(0.05) == 0


def test_normalize_score_clamps_high():
    assert normalize_score(0.45) == 100


def test_normalize_score_midpoint():
    score = normalize_score(0.225)
    assert 45 <= score <= 55


def test_brain_scores_image_has_all_keys():
    img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    scores = get_brain_scores(image=img)
    assert set(scores.keys()) == set(REGIONS.keys())
    for v in scores.values():
        assert 0 <= v <= 100


def test_brain_scores_text_has_all_keys():
    scores = get_brain_scores(text="Buy our amazing product today. Limited time offer.")
    assert set(scores.keys()) == set(REGIONS.keys())
    for v in scores.values():
        assert 0 <= v <= 100


def test_emotional_copy_scores_above_bland_on_amygdala():
    emotional = get_brain_scores(text="Act NOW — life-changing. Do not miss out. Fear and desire.")
    bland = get_brain_scores(text="This spreadsheet has columns and rows for data entry.")
    assert emotional["amygdala"] > bland["amygdala"]


from app.recommendation_engine import get_recommendations, Recommendation

_ALL_KEYS = ["visual_cortex", "amygdala", "face_social", "hippocampus", "language_areas", "reward_circuit", "prefrontal", "motor_action"]


def test_get_recs_has_one_per_region():
    scores = {k: 50 for k in _ALL_KEYS}
    recs = get_recommendations(scores)
    assert len(recs) == 8


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
