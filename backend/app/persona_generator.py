"""LLM-driven persona generation.

Takes a chunk of creator content (book excerpts, transcripts, NotebookLM exports,
tweet threads) and asks an LLM to extract per-brain-region tactical steps. Returns
a draft persona structure ready to review and save.

Default backend is the Hugging Face Inference API (free tier with rate limits).
Reads HF_TOKEN from env. If absent, raises a clear error.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

_log = logging.getLogger(__name__)

REGION_KEYS = [
    "visual_cortex", "face_social", "amygdala", "hippocampus",
    "language_areas", "reward_circuit", "prefrontal", "motor_action",
]

REGION_LABELS = {
    "visual_cortex": "Visual Cortex (visual hook, composition, contrast)",
    "face_social": "Face & Social (human presence, trust signals)",
    "amygdala": "Amygdala (emotion, urgency, fear, desire)",
    "hippocampus": "Hippocampus (memorability, narrative, distinctiveness)",
    "language_areas": "Language Areas (copy clarity, voice, persuasive language)",
    "reward_circuit": "Reward Circuit (payoff signal, value, transformation)",
    "prefrontal": "Prefrontal Cortex (logical proof, credibility, reasons to believe)",
    "motor_action": "Motor Action (call to action, urgency to click/buy)",
}

DEFAULT_HF_MODEL = os.environ.get(
    "HF_GENERATOR_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct"
)
HF_API_URL = "https://api-inference.huggingface.co/models/{model}"

MAX_SOURCE_CHARS = 30_000


class PersonaGeneratorError(RuntimeError):
    pass


def _build_prompt(name: str, source: str) -> str:
    regions_block = "\n".join(f"- {k}: {v}" for k, v in REGION_LABELS.items())
    return f"""You are extracting a creator's tactical playbook from their content for a marketing-analysis tool.

Creator name: {name}

Source content (book excerpts, transcripts, threads, or summary notes):
\"\"\"
{source[:MAX_SOURCE_CHARS]}
\"\"\"

Read the source and extract this creator's specific, actionable tactical advice for each of these 8 brain regions. For each region, give 2-4 short imperative steps written in this creator's voice and style. Be concrete and quote their phrasing where possible. Do NOT invent advice the source does not support — if the source has nothing for a region, return an empty list for that region.

Brain regions to fill:
{regions_block}

Return ONLY valid JSON with exactly these 8 keys, no other text:
{{
  "visual_cortex": ["step 1", "step 2"],
  "face_social": ["..."],
  "amygdala": ["..."],
  "hippocampus": ["..."],
  "language_areas": ["..."],
  "reward_circuit": ["..."],
  "prefrontal": ["..."],
  "motor_action": ["..."]
}}"""


def _parse_overlays(raw: str) -> dict[str, list[str]]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    obj_match = re.search(r"\{[\s\S]*\}", text)
    if not obj_match:
        raise PersonaGeneratorError(f"LLM did not return JSON: {raw[:300]}")
    try:
        data = json.loads(obj_match.group())
    except json.JSONDecodeError as exc:
        raise PersonaGeneratorError(f"LLM JSON malformed ({exc}): {raw[:300]}") from exc

    overlays: dict[str, list[str]] = {}
    for region in REGION_KEYS:
        steps = data.get(region, [])
        if not isinstance(steps, list):
            continue
        clean = [str(s).strip() for s in steps if str(s).strip()]
        if clean:
            overlays[region] = clean[:4]  # cap at 4 per region
    return overlays


def _call_hf_inference(prompt: str, model: str = DEFAULT_HF_MODEL) -> str:
    """Call the HF text-generation Inference API. Returns raw model output."""
    import httpx

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise PersonaGeneratorError(
            "HF_TOKEN env var not set. Add it as a Space secret to enable persona generation."
        )

    url = HF_API_URL.format(model=model)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.3,
            "return_full_text": False,
        },
    }
    try:
        with httpx.Client(timeout=120) as client:
            r = client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise PersonaGeneratorError(f"HF Inference network error: {exc}") from exc

    if r.status_code == 503:
        raise PersonaGeneratorError(
            "Model is loading on HF (cold start). Try again in 30 seconds."
        )
    if r.status_code == 429:
        raise PersonaGeneratorError(
            "HF Inference rate limit hit. Wait a few minutes or upgrade your HF plan."
        )
    if not r.is_success:
        raise PersonaGeneratorError(f"HF Inference error {r.status_code}: {r.text[:300]}")

    body = r.json()
    if isinstance(body, list) and body and isinstance(body[0], dict):
        return body[0].get("generated_text", "")
    if isinstance(body, dict):
        return body.get("generated_text", "") or json.dumps(body)
    return str(body)


def generate_persona(name: str, source: str, model: str | None = None) -> dict[str, Any]:
    """Generate a draft persona from creator source content.

    Returns a dict shaped like:
        {"name": str, "tagline": str, "step_overlays": {region: [steps...]}}

    Caller decides whether to save it (POST /personas) and is expected to let
    the user review/edit before persisting.
    """
    if not name.strip():
        raise PersonaGeneratorError("name is required")
    if len(source.strip()) < 50:
        raise PersonaGeneratorError("source content too short — paste at least a paragraph")

    prompt = _build_prompt(name.strip(), source.strip())
    raw = _call_hf_inference(prompt, model=model or DEFAULT_HF_MODEL)
    overlays = _parse_overlays(raw)

    if not overlays:
        raise PersonaGeneratorError(
            "LLM returned no usable steps. The source may be too thin or off-topic."
        )

    # Tagline derived from the first non-empty region's first step (best-effort).
    tagline = ""
    for region in REGION_KEYS:
        if region in overlays and overlays[region]:
            tagline = overlays[region][0][:120]
            break

    return {
        "name": name.strip(),
        "tagline": tagline,
        "step_overlays": overlays,
    }
