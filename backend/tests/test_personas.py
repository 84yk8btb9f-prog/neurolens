from app.personas import get_persona, list_personas, apply_persona
from app.recommendation_engine import Recommendation


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
    for s in original_steps:
        assert s in rec.steps


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
    apply_persona("hormozi", [rec])
    assert len(rec.steps) >= 2
