import json
import pytest
from unittest.mock import patch

from app.persona_generator import (
    REGION_KEYS,
    _parse_overlays,
    generate_persona,
    PersonaGeneratorError,
)


_VALID_LLM_OUTPUT = json.dumps({
    "visual_cortex": ["Use bold high-contrast hooks", "Lead with motion"],
    "face_social": ["Lead with founder's face"],
    "amygdala": ["Pain-then-relief framing", "Stack the value"],
    "hippocampus": ["3-act story arc"],
    "language_areas": ["Cut every word that doesn't earn its place"],
    "reward_circuit": ["Quantify the value", "Make the offer feel like a steal"],
    "prefrontal": ["Show specific numbers and proof"],
    "motor_action": ["Time-bound CTA"],
})


def test_parse_overlays_clean_json():
    overlays = _parse_overlays(_VALID_LLM_OUTPUT)
    assert set(overlays.keys()) == set(REGION_KEYS)
    assert overlays["visual_cortex"] == ["Use bold high-contrast hooks", "Lead with motion"]


def test_parse_overlays_fenced_json():
    overlays = _parse_overlays(f"```json\n{_VALID_LLM_OUTPUT}\n```")
    assert "amygdala" in overlays


def test_parse_overlays_with_preamble():
    raw = f"Sure, here's the JSON:\n\n{_VALID_LLM_OUTPUT}\n\nLet me know if you need more."
    overlays = _parse_overlays(raw)
    assert "reward_circuit" in overlays


def test_parse_overlays_drops_empty_regions():
    blob = json.dumps({**json.loads(_VALID_LLM_OUTPUT), "amygdala": []})
    overlays = _parse_overlays(blob)
    assert "amygdala" not in overlays


def test_parse_overlays_caps_at_four_steps():
    blob = json.dumps({"visual_cortex": ["a", "b", "c", "d", "e", "f"]})
    overlays = _parse_overlays(blob)
    assert len(overlays["visual_cortex"]) == 4


def test_parse_overlays_no_json_raises():
    with pytest.raises(PersonaGeneratorError, match="did not return JSON"):
        _parse_overlays("Sorry, I don't have access to that creator's content.")


def test_parse_overlays_malformed_json_raises():
    with pytest.raises(PersonaGeneratorError, match="malformed"):
        _parse_overlays("{ this is not: valid json }")


def test_generate_persona_requires_name():
    with pytest.raises(PersonaGeneratorError, match="name is required"):
        generate_persona("", "lorem " * 200)


def test_generate_persona_rejects_thin_source():
    with pytest.raises(PersonaGeneratorError, match="too short"):
        generate_persona("Hormozi", "x")


def test_generate_persona_happy_path():
    with patch("app.persona_generator._call_hf_inference", return_value=_VALID_LLM_OUTPUT):
        out = generate_persona("Alex Hormozi", "lorem ipsum dolor sit amet " * 30)
    assert out["name"] == "Alex Hormozi"
    assert out["tagline"]
    assert "amygdala" in out["step_overlays"]


def test_generate_persona_propagates_llm_error():
    with patch(
        "app.persona_generator._call_hf_inference",
        side_effect=PersonaGeneratorError("rate limited"),
    ):
        with pytest.raises(PersonaGeneratorError, match="rate limited"):
            generate_persona("X", "lorem " * 100)
