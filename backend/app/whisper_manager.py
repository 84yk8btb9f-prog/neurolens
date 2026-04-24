from __future__ import annotations
import gc
import logging
import threading
import time
from typing import Any

_log = logging.getLogger(__name__)

WHISPER_MODEL = "tiny"


def _load_whisper(name: str) -> Any:
    import whisper
    return whisper.load_model(name)


class WhisperManager:
    def __init__(self, idle_timeout: int = 120):
        self._model: Any = None
        self._lock = threading.Lock()
        self._last_used: float = 0.0
        self._idle_timeout = idle_timeout
        self._watchdog = threading.Thread(target=self._idle_watchdog, daemon=True)
        self._watchdog.start()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def get(self) -> Any:
        with self._lock:
            if self._model is None:
                _log.info("Loading Whisper %s", WHISPER_MODEL)
                self._model = _load_whisper(WHISPER_MODEL)
            self._last_used = time.monotonic()
            model = self._model
        return model

    def unload(self) -> bool:
        with self._lock:
            if self._model is None:
                return False
            self._model = None
        gc.collect()
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass
        return True

    def status(self) -> dict:
        with self._lock:
            loaded = self._model is not None
            last_used = self._last_used
        idle_for = (time.monotonic() - last_used) if last_used > 0.0 else None
        return {
            "loaded": loaded,
            "idle_timeout_seconds": self._idle_timeout,
            "idle_for_seconds": round(idle_for, 1) if idle_for is not None else None,
        }

    def _idle_watchdog(self) -> None:
        while True:
            time.sleep(min(self._idle_timeout, 60))
            with self._lock:
                if self._model is None:
                    continue
                if time.monotonic() - self._last_used <= self._idle_timeout:
                    continue
            self.unload()


_manager = WhisperManager()


def get_whisper_manager() -> WhisperManager:
    return _manager
