from __future__ import annotations
import os
import subprocess
import cv2
from PIL import Image
import app.brain_mapper as brain_mapper
from app.brain_mapper import REGIONS
from app.whisper_manager import get_whisper_manager
from app.tribe_scorer import score_video
from app.tribe_manager import get_tribe_manager
from app.atlas_mapper import CORTICAL_REGIONS as _TRIBE_CORTICAL

_VLM_SUBCORTICAL = frozenset(REGIONS) - _TRIBE_CORTICAL


def extract_frames(video_path: str, fps: float = 0.5, max_frames: int = 24) -> list[Image.Image]:
    cap = cv2.VideoCapture(video_path)
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    interval = max(1, int(video_fps / fps))
    frames: list[Image.Image] = []
    idx = 0
    while cap.isOpened() and len(frames) < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % interval == 0:
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        idx += 1
    cap.release()
    return frames


def transcribe_audio(video_path: str) -> str:
    audio_path = video_path.rsplit(".", 1)[0] + "_audio.wav"
    subprocess.run(
        ["ffmpeg", "-i", video_path, "-ar", "16000", "-ac", "1", "-y", audio_path],
        capture_output=True,
    )
    if not os.path.exists(audio_path):
        return ""
    result = get_whisper_manager().get().transcribe(audio_path)
    os.remove(audio_path)
    return result.get("text", "")


def process_video(file_path: str) -> dict:
    frames = extract_frames(file_path)
    transcript = transcribe_audio(file_path)

    tribe_scores = score_video(file_path)
    get_tribe_manager().unload()

    if not frames and not transcript.strip():
        vlm_scores: dict[str, int] = {k: 0 for k in REGIONS}
    else:
        vlm_scores = brain_mapper.get_brain_scores(
            images=frames or None,
            text=transcript.strip() or None,
        )

    if tribe_scores is not None:
        scores: dict[str, int] = {
            **{k: tribe_scores.get(k, vlm_scores.get(k, 0)) for k in _TRIBE_CORTICAL},
            **{k: vlm_scores.get(k, 0) for k in _VLM_SUBCORTICAL},
        }
    else:
        scores = vlm_scores

    return {
        "type": "video",
        "scores": scores,
        "meta": {
            "frame_count": len(frames),
            "transcript_preview": transcript[:200],
            "tribe_used": tribe_scores is not None,
        },
    }
