import pytest
from unittest.mock import patch
from app.persona_storage import PersonaStorage
from app.personas import get_persona, list_personas, apply_persona
from app.recommendation_engine import Recommendation, get_recommendations


@pytest.fixture(autouse=True)
def mock_persona_storage(tmp_path):
    store = PersonaStorage(str(tmp_path / "test_personas.db"))
    store.init()
    with patch("app.personas.get_persona_storage", return_value=store):
        yield store


def _rec(region_key: str, priority: str = "medium") -> Recommendation:
    return Recommendation(
        region_key=region_key,
        region_name="Test Region",
        score=50,
        priority=priority,
        message="Test message",
        details="Test details",
        steps=["Generic step 1", "Generic step 2"],
    )


def test_list_personas_includes_known_creators():
    personas = list_personas()
    keys = [p["key"] for p in personas]
    assert "hormozi" in keys
    assert "garyvee" in keys
    assert "brunson" in keys
    assert "yadegari" in keys


def test_get_persona_returns_none_for_default():
    assert get_persona("default") is None
    assert get_persona(None) is None
    assert get_persona("") is None


def test_get_persona_returns_known():
    p = get_persona("hormozi")
    assert p is not None
    assert p.key == "hormozi"
    assert p.name == "Alex Hormozi"


def test_apply_persona_adds_steps_at_front():
    rec = _rec("amygdala")
    original_steps = list(rec.steps)
    apply_persona("hormozi", [rec])
    assert len(rec.steps) > len(original_steps)
    # Original steps must be at the tail (persona steps prepended at front)
    assert rec.steps[-len(original_steps):] == original_steps


def test_apply_persona_default_no_change():
    rec = _rec("amygdala")
    original_steps = list(rec.steps)
    apply_persona(None, [rec])
    assert rec.steps == original_steps


def test_apply_persona_unknown_no_change():
    rec = _rec("amygdala")
    original_steps = list(rec.steps)
    apply_persona("nonexistent", [rec])
    assert rec.steps == original_steps


def test_apply_persona_region_not_in_overlay_no_extra_steps():
    rec = _rec("hippocampus")
    original_steps = list(rec.steps)
    apply_persona("hormozi", [rec])
    assert rec.steps == original_steps


_SCORES = {
    "visual_cortex": 40, "face_social": 40, "amygdala": 40,
    "hippocampus": 40, "language_areas": 40, "reward_circuit": 40,
    "prefrontal": 40, "motor_action": 40,
}


def test_get_recommendations_with_persona():
    recs_default = get_recommendations(_SCORES, persona_key=None)
    recs_hormozi = get_recommendations(_SCORES, persona_key="hormozi")
    assert len(recs_default) == len(recs_hormozi)
    amygdala_default = next(r for r in recs_default if r.region_key == "amygdala")
    amygdala_hormozi = next(r for r in recs_hormozi if r.region_key == "amygdala")
    assert len(amygdala_hormozi.steps) > len(amygdala_default.steps)


def test_get_recommendations_unknown_persona_no_crash():
    recs = get_recommendations(_SCORES, persona_key="nonexistent_persona")
    assert len(recs) == 8
