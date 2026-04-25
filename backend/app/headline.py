from __future__ import annotations

_REGION_TEMPLATES: dict[str, tuple[str, str]] = {
    "visual_cortex": (
        "Visual Cortex",
        "Viewers will scroll past — the visual hook isn't pulling enough attention",
    ),
    "face_social": (
        "Face & Social",
        "Trust signal is missing — no human face for the brain to anchor on",
    ),
    "amygdala": (
        "Amygdala",
        "Emotionally flat — viewers feel nothing strong enough to act on",
    ),
    "hippocampus": (
        "Hippocampus",
        "Forgettable — this won't stick in memory five minutes after viewing",
    ),
    "language_areas": (
        "Language Areas",
        "The copy is muted — language isn't carrying the message",
    ),
    "reward_circuit": (
        "Reward Circuit",
        "No payoff — viewers don't see what's in it for them",
    ),
    "prefrontal": (
        "Prefrontal Cortex",
        "Logical buyers aren't convinced — no proof or reasons to believe",
    ),
    "motor_action": (
        "Motor Action",
        "No clear next step — viewers won't know what to do",
    ),
}


def generate_headline(scores: dict[str, int]) -> str:
    if not scores:
        return "No signal detected."

    lowest_key = min(scores, key=lambda k: scores[k])
    lowest_score = scores[lowest_key]
    average = sum(scores.values()) / len(scores)

    if lowest_score >= 70:
        return f"Strong activation across the board — average {round(average)}/100."

    region_name, message = _REGION_TEMPLATES.get(
        lowest_key, (lowest_key.replace("_", " ").title(), "Weak activation in this region")
    )
    return f"{message} ({region_name}: {lowest_score}/100)."
