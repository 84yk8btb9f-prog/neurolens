"""Thin shim around the CLIP scorer that preserves the public surface
(`get_manager()`, `LowMemoryError`, `idle watchdog`, `unload`) used by the
rest of the app and the existing `/model/*` endpoints. Implementation now
delegates to `clip_scorer.CLIPScorer`."""
from __future__ import annotations

import gc
import logging
import threading
import time

from app.clip_scorer import CLIP_MODEL_ID, get_scorer

_log = logging.getLogger(__name__)

MODEL_ID = CLIP_MODEL_ID


class LowMemoryError(RuntimeError):
    """Kept for backwards compatibility with existing exception handlers."""


class ModelManager:
    def __init__(self, idle_timeout: int = 600):
        self._lock = threading.Lock()
        self._last_used: float = 0.0
        self._idle_timeout = idle_timeout
        self._watchdog = threading.Thread(target=self._idle_watchdog, daemon=True)
        self._watchdog.start()

    @property
    def loaded(self) -> bool:
        return get_scorer().loaded

    def get(self) -> tuple[object, object]:
        """Backwards compat — returns (scorer, scorer) so old call sites that
        unpacked (model, processor) still work without crashing. New code should
        call get_scorer() directly."""
        scorer = get_scorer()
        scorer.load()
        with self._lock:
            self._last_used = time.monotonic()
        return scorer, scorer

    def unload(self) -> bool:
        did = get_scorer().unload()
        gc.collect()
        return did

    def status(self) -> dict:
        with self._lock:
            last_used = self._last_used
        idle_for = time.monotonic() - last_used if last_used else None
        return {
            "loaded": self.loaded,
            "model_id": MODEL_ID,
            "idle_timeout_seconds": self._idle_timeout,
            "idle_for_seconds": round(idle_for, 1) if idle_for else None,
        }

    def _idle_watchdog(self) -> None:
        while True:
            time.sleep(30)
            with self._lock:
                last_used = self._last_used
            if not last_used or not self.loaded:
                continue
            if time.monotonic() - last_used > self._idle_timeout:
                _log.info("ModelManager idle for >%ds — unloading CLIP", self._idle_timeout)
                self.unload()


_manager: ModelManager | None = None


def get_manager() -> ModelManager:
    global _manager
    if _manager is None:
        _manager = ModelManager()
    return _manager
