# backend/app/brain_mapper.py
from __future__ import annotations
import threading
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

_lock = threading.Lock()
_model: CLIPModel | None = None
_processor: CLIPProcessor | None = None
_MODEL_ID = "openai/clip-vit-base-patch32"

REGIONS: dict[str, dict] = {
    "visual_cortex": {
        "name": "Visual Cortex",
        "description": "Visual richness, color, composition",
        "marketing": "Visual appeal and aesthetic impact",
        "probes": [
            "vivid colors, rich visual detail, beautiful imagery",
            "striking composition, high contrast, detailed texture",
            "aesthetically pleasing, visually stunning design",
        ],
    },
    "face_social": {
        "name": "Face & Social Areas",
        "description": "Human faces, social trust, connection",
        "marketing": "Human connection and social proof",
        "probes": [
            "human face, portrait, eye contact, personal connection",
            "people together, social interaction, community, belonging",
            "trust, authenticity, real person, genuine emotion",
        ],
    },
    "amygdala": {
        "name": "Emotional Core",
        "description": "Emotional intensity, urgency, desire",
        "marketing": "Emotional impact and urgency",
        "probes": [
            "intense emotion, fear, urgency, excitement, powerful feeling",
            "joy, happiness, love, aspiration, dream, hope",
            "missing out, problem, pain point, frustration, anxiety",
        ],
    },
    "hippocampus": {
        "name": "Memory Encoding",
        "description": "Memorability, novelty, narrative",
        "marketing": "Brand recall and memorability",
        "probes": [
            "memorable story, unique narrative, unforgettable moment",
            "unexpected surprise, novelty, stands out, distinctive",
            "before and after transformation, journey, sequence of events",
        ],
    },
    "language_areas": {
        "name": "Language Processing",
        "description": "Verbal clarity, messaging, persuasion",
        "marketing": "Message clarity and persuasive copy",
        "probes": [
            "clear message, compelling words, persuasive language, call to action",
            "headline, tagline, benefit statement, value proposition",
            "storytelling, dialogue, conversation, written communication",
        ],
    },
    "reward_circuit": {
        "name": "Reward Circuit",
        "description": "Desire, craving, purchase drive",
        "marketing": "Desire and purchase intent",
        "probes": [
            "desire, craving, want, need, must have, exclusive, premium",
            "reward, achievement, satisfaction, success, transformation",
            "deal, offer, save, get it now, own it, limited availability",
        ],
    },
    "prefrontal": {
        "name": "Decision Center",
        "description": "Rational appeal, credibility, logic",
        "marketing": "Trust, proof, and rational justification",
        "probes": [
            "proof, evidence, data, statistics, credible, trustworthy, verified",
            "logical reason, benefit, feature, how it works, why choose this",
            "guarantee, safety, reliable, quality, professional, expert",
        ],
    },
    "motor_action": {
        "name": "Action & Drive",
        "description": "Energy, movement, call-to-action activation",
        "marketing": "Action drive and engagement activation",
        "probes": [
            "action, movement, energy, dynamic, do it now, start today",
            "motion, fast, momentum, progress, change happening",
            "click, buy, sign up, get started, take action, join now",
        ],
    },
}


def _load() -> tuple[CLIPModel, CLIPProcessor]:
    global _model, _processor
    with _lock:
        if _model is None:
            _model = CLIPModel.from_pretrained(_MODEL_ID)
            _model.eval()
            _processor = CLIPProcessor.from_pretrained(_MODEL_ID)
    return _model, _processor


def normalize_score(raw: float, lo: float = 0.10, hi: float = 0.38) -> int:
    return max(0, min(100, round((raw - lo) / (hi - lo) * 100)))


def _get_image_features(model: CLIPModel, proc: CLIPProcessor, image: Image.Image) -> torch.Tensor:
    img_in = proc(images=image, return_tensors="pt")
    vision_out = model.vision_model(**img_in)
    feat = model.visual_projection(vision_out.pooler_output)
    return feat / feat.norm(dim=-1, keepdim=True)


def _get_text_features(model: CLIPModel, proc: CLIPProcessor, texts: list[str]) -> torch.Tensor:
    txt_in = proc(text=texts, return_tensors="pt", padding=True, truncation=True)
    text_out = model.text_model(**txt_in)
    feat = model.text_projection(text_out.pooler_output)
    return feat / feat.norm(dim=-1, keepdim=True)


def _img_score(image: Image.Image, probes: list[str], model: CLIPModel, proc: CLIPProcessor) -> float:
    with torch.no_grad():
        img_feat = _get_image_features(model, proc, image)
        txt_feat = _get_text_features(model, proc, probes)
        return (img_feat @ txt_feat.T).squeeze(0).reshape(-1).max().item()


def _txt_score(content: str, probes: list[str], model: CLIPModel, proc: CLIPProcessor) -> float:
    all_texts = [content[:300]] + probes
    with torch.no_grad():
        feats = _get_text_features(model, proc, all_texts)
        return (feats[0:1] @ feats[1:].T).squeeze(0).reshape(-1).max().item()


def get_brain_scores(
    image: Image.Image | None = None,
    text: str | None = None,
    images: list[Image.Image] | None = None,
    texts: list[str] | None = None,
) -> dict[str, int]:
    model, proc = _load()
    all_imgs: list[Image.Image] = list(images or []) + ([image] if image else [])
    all_txts: list[str] = list(texts or []) + ([text] if text else [])

    scores: dict[str, int] = {}
    for key, region in REGIONS.items():
        probes = region["probes"]
        # Image-text similarity range: 0.10–0.38 (CLIP cross-modal)
        # Text-text similarity range: 0.60–0.95 (CLIP same-modal)
        normalized: list[int] = []
        for img in all_imgs:
            raw = _img_score(img, probes, model, proc)
            normalized.append(normalize_score(raw, lo=0.10, hi=0.38))
        for t in all_txts:
            raw = _txt_score(t, probes, model, proc)
            normalized.append(normalize_score(raw, lo=0.60, hi=0.95))
        scores[key] = round(sum(normalized) / len(normalized)) if normalized else 0
    return scores
