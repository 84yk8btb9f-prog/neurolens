from __future__ import annotations
import json
import logging
import re
from PIL import Image
from app.model_manager import get_manager

_log = logging.getLogger(__name__)

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

_SYSTEM_PROMPT = """\
You are a neuroscience-informed marketing analyst. Your task is to rate how strongly \
the provided content would activate each of the following brain regions in a typical viewer.

Score each region 0–100. Be discriminating — most scores should differ from each other. \
A score of 50 is average; 0 means the region is not engaged at all; 100 means maximum engagement.

Brain regions and what drives their activation:
- visual_cortex: Visual richness, color variety, high contrast, strong composition, aesthetic beauty
- face_social: Human faces, eye contact, social scenes, community, belonging, trust signals
- amygdala: Emotional intensity — fear, urgency, joy, excitement, aspiration, pain points, desire
- hippocampus: Memorability, novelty, surprise, distinctive storytelling, things that stand out
- language_areas: Text clarity, compelling copy, strong CTA, persuasive language, value proposition
- reward_circuit: Desire triggers, exclusivity, premium feel, transformation promise, "must-have" feeling
- prefrontal: Trust signals, data, proof, logical reasoning, credibility, guarantees, expertise
- motor_action: Energy, urgency, movement, "act now" signals, dynamic pacing, call-to-action strength

Return ONLY valid JSON with exactly these 8 keys, no other text:
{"visual_cortex": <int>, "face_social": <int>, "amygdala": <int>, "hippocampus": <int>, \
"language_areas": <int>, "reward_circuit": <int>, "prefrontal": <int>, "motor_action": <int>}"""

_FALLBACK = {k: 50 for k in REGIONS}

_config_cache: dict | None = None


def _get_config() -> dict:
    global _config_cache
    if _config_cache is None:
        from mlx_vlm.utils import load_config
        from app.model_manager import MODEL_ID
        _config_cache = load_config(MODEL_ID)
    return _config_cache


def _parse_scores(raw: str) -> dict[str, int]:
    text = raw.strip()
    # Strip markdown code fences if present
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    # Find first JSON object in the output
    obj = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if not obj:
        _log.warning("_parse_scores: no JSON found in VLM output: %r", raw[:200])
        return dict(_FALLBACK)
    try:
        data = json.loads(obj.group())
    except json.JSONDecodeError as exc:
        _log.warning("_parse_scores: JSON decode failed (%s): %r", exc, raw[:200])
        return dict(_FALLBACK)
    result: dict[str, int] = {}
    for key in REGIONS:
        raw_val = data.get(key, 50)
        try:
            result[key] = max(0, min(100, int(round(float(raw_val)))))
        except (ValueError, TypeError):
            result[key] = 50
    return result


def _generate_scores(model, processor, prompt: str, image: Image.Image | None = None) -> str:
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template

    config = _get_config()
    formatted = apply_chat_template(
        processor, config, prompt,
        num_images=1 if image else 0,
    )
    kwargs: dict = {"max_tokens": 256, "verbose": False}
    if image is not None:
        kwargs["image"] = image
    return generate(model, processor, formatted, **kwargs)


def _score_image(model, processor, image: Image.Image) -> dict[str, int]:
    prompt = f"{_SYSTEM_PROMPT}\n\nAnalyze the image above."
    raw = _generate_scores(model, processor, prompt, image=image)
    return _parse_scores(raw)


def _score_text(model, processor, text: str) -> dict[str, int]:
    prompt = f"{_SYSTEM_PROMPT}\n\nAnalyze the following marketing content:\n\n{text[:2000]}"
    raw = _generate_scores(model, processor, prompt)
    return _parse_scores(raw)


def get_brain_scores(
    image: Image.Image | None = None,
    text: str | None = None,
    images: list[Image.Image] | None = None,
    texts: list[str] | None = None,
) -> dict[str, int]:
    all_imgs: list[Image.Image] = list(images or []) + ([image] if image else [])
    all_txts: list[str] = list(texts or []) + ([text] if text else [])
    if not all_imgs and not all_txts:
        raise ValueError("get_brain_scores requires at least one image or text input")

    model, processor = get_manager().get()

    all_scores: list[dict[str, int]] = []
    for img in all_imgs:
        all_scores.append(_score_image(model, processor, img))
    for t in all_txts:
        all_scores.append(_score_text(model, processor, t))

    return {
        key: round(sum(s[key] for s in all_scores) / len(all_scores))
        for key in REGIONS
    }
