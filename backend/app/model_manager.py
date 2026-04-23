from __future__ import annotations
import gc
import threading
import time
from typing import Any


MODEL_ID = "mlx-community/Qwen2-VL-7B-Instruct-8bit"


def _load_vlm(model_id: str) -> tuple[Any, Any]:
    from mlx_vlm import load
    return load(model_id)


class ModelManager:
    def __init__(self, idle_timeout: int = 300):
        self._model: Any = None
        self._processor: Any = None
        self._lock = threading.Lock()
        self._last_used: float = 0.0
        self._idle_timeout = idle_timeout
        self._watchdog = threading.Thread(target=self._idle_watchdog, daemon=True)
        self._watchdog.start()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def get(self) -> tuple[Any, Any]:
        self._last_used = time.monotonic()
        with self._lock:
            if self._model is None:
                self._model, self._processor = _load_vlm(MODEL_ID)
            model, processor = self._model, self._processor
        return model, processor

    def unload(self) -> None:
        with self._lock:
            if self._model is None:
                return
            self._model = None
            self._processor = None
        gc.collect()
        try:
            import mlx.core as mx
            mx.metal.clear_cache()
        except Exception:
            pass

    def status(self) -> dict:
        with self._lock:
            loaded = self._model is not None
            last_used = self._last_used
        idle_for = time.monotonic() - last_used if last_used else None
        return {
            "loaded": loaded,
            "idle_timeout_seconds": self._idle_timeout,
            "idle_for_seconds": round(idle_for, 1) if idle_for else None,
        }

    def _idle_watchdog(self) -> None:
        while True:
            time.sleep(min(self._idle_timeout, 60))
            if self.loaded and time.monotonic() - self._last_used > self._idle_timeout:
                self.unload()


_manager = ModelManager()


def get_manager() -> ModelManager:
    return _manager
