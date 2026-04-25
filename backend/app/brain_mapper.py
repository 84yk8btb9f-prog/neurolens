from __future__ import annotations
from PIL import Image
from app.clip_scorer import score_inputs

REGIONS: dict[str, dict] = {
    "visual_cortex": {
        "name": "Visual Cortex",
        "description": "Visual richness, color, composition",
        "marketing": "Visual appeal and aesthetic impact",
    },
    "face_social": {
        "name": "Face & Social Areas",
        "description": "Human faces, social trust, connection",
        "marketing": "Human connection and social proof",
    },
    "amygdala": {
        "name": "Emotional Core",
        "description": "Emotional intensity, urgency, desire",
        "marketing": "Emotional impact and urgency",
    },
    "hippocampus": {
        "name": "Memory Encoding",
        "description": "Memorability, novelty, narrative",
        "marketing": "Brand recall and memorability",
    },
    "language_areas": {
        "name": "Language Processing",
        "description": "Verbal clarity, messaging, persuasion",
        "marketing": "Message clarity and persuasive copy",
    },
    "reward_circuit": {
        "name": "Reward Circuit",
        "description": "Desire, craving, purchase drive",
        "marketing": "Desire and purchase intent",
    },
    "prefrontal": {
        "name": "Decision Center",
        "description": "Rational appeal, credibility, logic",
        "marketing": "Trust, proof, and rational justification",
    },
    "motor_action": {
        "name": "Action & Drive",
        "description": "Energy, movement, call-to-action activation",
        "marketing": "Action drive and engagement activation",
    },
}


def get_brain_scores(
    image: Image.Image | None = None,
    text: str | None = None,
    images: list[Image.Image] | None = None,
    texts: list[str] | None = None,
) -> dict[str, int]:
    all_imgs: list[Image.Image] = list(images or []) + ([image] if image else [])
    all_txts: list[str] = list(texts or []) + ([text] if text else [])
    return score_inputs(images=all_imgs, texts=all_txts)
