from app.headline import generate_headline


_HIGH_SCORES = {
    "visual_cortex": 85, "face_social": 80, "amygdala": 75,
    "hippocampus": 78, "language_areas": 82, "reward_circuit": 79,
    "prefrontal": 81, "motor_action": 76,
}


def test_high_scores_returns_positive_headline():
    out = generate_headline(_HIGH_SCORES)
    assert "Strong activation" in out
    assert "/100" in out


def test_low_amygdala_returns_emotional_headline():
    scores = {**_HIGH_SCORES, "amygdala": 22}
    out = generate_headline(scores)
    assert "Emotionally flat" in out
    assert "Amygdala" in out
    assert "22/100" in out


def test_lowest_region_drives_headline():
    scores = {**_HIGH_SCORES, "motor_action": 18, "prefrontal": 25}
    out = generate_headline(scores)
    assert "no clear next step" in out.lower()
    assert "18/100" in out


def test_unknown_region_does_not_crash():
    scores = {"made_up_region": 10}
    out = generate_headline(scores)
    assert "10/100" in out


def test_empty_scores_returns_no_signal():
    assert generate_headline({}) == "No signal detected."


def test_all_eight_regions_have_templates():
    keys = ["visual_cortex", "face_social", "amygdala", "hippocampus",
            "language_areas", "reward_circuit", "prefrontal", "motor_action"]
    for k in keys:
        scores = {other: 80 for other in keys}
        scores[k] = 20
        out = generate_headline(scores)
        assert "20/100" in out
        assert "Strong activation" not in out
