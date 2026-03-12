from __future__ import annotations

from datetime import datetime

from proof_of_work_api.config.app_settings import AppSettings
from proof_of_work_api.services.api_error import ApiError
from proof_of_work_api.services.sliding_window_tracker import SlidingWindowTracker


class ChallengeRateLimiter:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._ip_tracker = SlidingWindowTracker(settings.challenge_rate_window_seconds)
        self._session_tracker = SlidingWindowTracker(settings.challenge_rate_window_seconds)

    def enforce(self, ip_address: str, session_id: str, current_time: datetime) -> None:
        ip_count = self._ip_tracker.count(ip_address, current_time)
        if ip_count >= self._settings.ip_challenge_limit:
            raise ApiError(429, "IP_CHALLENGE_RATE_LIMITED", "IP-based challenge issuance limit exceeded.")
        session_count = self._session_tracker.count(session_id, current_time)
        if session_count >= self._settings.session_challenge_limit:
            raise ApiError(429, "SESSION_CHALLENGE_RATE_LIMITED", "Session-based challenge issuance limit exceeded.")

    def record(self, ip_address: str, session_id: str, current_time: datetime) -> None:
        self._ip_tracker.record(ip_address, current_time)
        self._session_tracker.record(session_id, current_time)
