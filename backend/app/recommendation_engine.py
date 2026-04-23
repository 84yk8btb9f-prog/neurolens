# backend/app/recommendation_engine.py
from dataclasses import dataclass

@dataclass
class Recommendation:
    region_key: str
    region_name: str
    score: int
    priority: str  # "high" | "medium" | "ok"
    message: str


_ADVICE: dict[str, dict[str, str]] = {
    "visual_cortex": {
        "high": "Strong visual appeal — your content is aesthetically engaging.",
        "medium": "Visual impact is moderate. Try bolder composition or richer imagery.",
        "low": "Weak visual engagement. Upgrade image quality and use high-contrast design.",
    },
    "face_social": {
        "high": "Excellent human connection — faces and social proof are landing well.",
        "medium": "Add a real human face or testimonial to strengthen trust.",
        "low": "No human connection. Include a face, social proof, or people-focused visuals.",
    },
    "amygdala": {
        "high": "High emotional impact — your content creates a strong feeling response.",
        "medium": "Emotional resonance is moderate. Sharpen your hook — deeper desire or fear.",
        "low": "Low emotional impact. Add urgency, a pain point, or an aspirational outcome.",
    },
    "hippocampus": {
        "high": "Highly memorable — this content will stick.",
        "medium": "Memorability is average. Add a unique hook or unexpected element.",
        "low": "Easily forgotten. Use a surprising twist, strong story, or distinctive visual.",
    },
    "language_areas": {
        "high": "Clear, persuasive messaging — your language is working.",
        "medium": "Messaging clarity is moderate. Make the headline more direct and benefit-focused.",
        "low": "Weak messaging. Rewrite your headline for clarity and add a strong CTA.",
    },
    "reward_circuit": {
        "high": "Strong desire — your content makes people want it.",
        "medium": "Moderate desire. Make the value and transformation more tangible.",
        "low": "Low desire activation. Show the transformation clearly. Make the offer feel exclusive.",
    },
    "prefrontal": {
        "high": "Strong rational justification — trust signals are well established.",
        "medium": "Add more proof: statistics, guarantees, or reviews.",
        "low": "No rational justification. Add social proof, data, or credibility indicators.",
    },
    "motor_action": {
        "high": "Strong action drive — your content activates and moves people.",
        "medium": "Action drive is moderate. Use more energetic CTA words.",
        "low": "No action drive. Add an explicit, urgent CTA with action verbs.",
    },
}


def get_recommendations(scores: dict[str, int]) -> list[Recommendation]:
    from app.brain_mapper import REGIONS

    def level(s: int) -> tuple[str, str]:
        if s < 35:
            return "low", "high"
        if s < 65:
            return "medium", "medium"
        return "high", "ok"

    recs = []
    for key, score in scores.items():
        lvl, priority = level(score)
        recs.append(Recommendation(
            region_key=key,
            region_name=REGIONS[key]["name"],
            score=score,
            priority=priority,
            message=_ADVICE[key][lvl],
        ))

    recs.sort(key=lambda r: ({"high": 0, "medium": 1, "ok": 2}[r.priority], r.score))
    return recs
