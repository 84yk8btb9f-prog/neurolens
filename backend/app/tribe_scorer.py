from __future__ import annotations
import logging
import threading
import numpy as np
from app.tribe_manager import get_tribe_manager, TribeNotAvailableError
from app.atlas_mapper import get_vertex_masks, vertex_activations_to_scores

_log = logging.getLogger(__name__)

_masks: dict | None = None
_masks_lock = threading.Lock()


def _get_masks() -> dict:
    global _masks
    if _masks is None:
        with _masks_lock:
            if _masks is None:
                _masks = get_vertex_masks()
    return _masks


def score_video(video_path: str) -> dict[str, int] | None:
    """
    Run TRIBE v2 on a video file; return 5 cortical region scores (0-100) or None.
    None signals the caller to fall back to VLM for all 8 regions.
    """
    mgr = get_tribe_manager()
    try:
        model = mgr.get()
    except TribeNotAvailableError as exc:
        _log.warning("TRIBE v2 not available: %s", exc)
        return None
    try:
        events = model.get_events_dataframe(video_path=video_path)
        preds, _segments = model.predict(events=events)
        return vertex_activations_to_scores(np.asarray(preds), _get_masks())
    except Exception as exc:
        _log.warning("TRIBE v2 scoring failed for %s: %s", video_path, exc)
        return None
