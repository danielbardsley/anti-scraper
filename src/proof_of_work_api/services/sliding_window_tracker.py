from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock


class SlidingWindowTracker:
    def __init__(self, window_seconds: int) -> None:
        self._window_seconds = window_seconds
        self._events: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = Lock()

    def count(self, key: str, current_time: datetime) -> int:
        normalized = current_time.astimezone(timezone.utc)
        with self._lock:
            queue = self._events[key]
            self._trim(queue, normalized)
            return len(queue)

    def record(self, key: str, completed_at: datetime) -> None:
        normalized = completed_at.astimezone(timezone.utc)
        with self._lock:
            queue = self._events[key]
            self._trim(queue, normalized)
            queue.append(normalized)

    def _trim(self, queue: deque[datetime], reference_time: datetime) -> None:
        threshold = reference_time - timedelta(seconds=self._window_seconds)
        while queue and queue[0] <= threshold:
            queue.popleft()
