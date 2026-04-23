from __future__ import annotations
import gc
import logging
import threading
import time
from typing import Any

import psutil

_log = logging.getLogger(__name__)

_MIN_AVAILABLE_GB = 8.0


def _load_tribe() -> Any:
    try:
        from tribev2 import TribeModel
    except ImportError:
        from tribe import TribeModel  # type: ignore[no-redef]
    return TribeModel.from_pretrained("facebook/tribev2")


class TribeNotAvailableError(RuntimeError):
    """Raised when TRIBE v2 is not installed or memory is too low."""


class TribeManager:
    def __init__(self, idle_timeout: int = 120, min_available_gb: float = _MIN_AVAILABLE_GB):
        self._model: Any = None
        self._lock = threading.Lock()
        self._last_used: float = 0.0
        self._idle_timeout = idle_timeout
        self._min_available_gb = min_available_gb
        self._available = self._check_available()
        if self._available:
            threading.Thread(target=self._idle_watchdog, daemon=True).start()

    @staticmethod
    def _check_available() -> bool:
        try:
            import tribev2  # noqa: F401
            return True
        except ImportError:
            pass
        try:
            import tribe  # noqa: F401
            return True
        except ImportError:
            return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def get(self) -> Any:
        if not self._available:
            raise TribeNotAvailableError("tribev2 package is not installed.")
        with self._lock:
            if self._model is None:
                avail_gb = psutil.virtual_memory().available / (1024 ** 3)
                if avail_gb < self._min_available_gb:
                    raise TribeNotAvailableError(
                        f"Only {avail_gb:.1f} GB free; need {self._min_available_gb} GB to load TRIBE v2."
                    )
                _log.info("Loading TRIBE v2 (%.1f GB free)", avail_gb)
                self._model = _load_tribe()
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
        idle_for = time.monotonic() - last_used if last_used else None
        return {
            "available": self._available,
            "loaded": loaded,
            "idle_timeout_seconds": self._idle_timeout,
            "idle_for_seconds": round(idle_for, 1) if idle_for else None,
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


_manager = TribeManager()


def get_tribe_manager() -> TribeManager:
    return _manager
