from __future__ import annotations

from threading import Lock


class TelemetryService:
    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._lock = Lock()

    def increment(self, key: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[key] = self._counters.get(key, 0) + amount

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(sorted(self._counters.items()))
