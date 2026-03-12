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

    def enforce_and_record(self, ip_address: str, session_id: str, current_time: datetime) -> None:
        try:
            self._ip_tracker.check_and_record_if_below_limit(ip_address, self._settings.ip_challenge_limit, current_time)
        except ValueError as error:
            raise ApiError(429, "IP_CHALLENGE_RATE_LIMITED", "IP-based challenge issuance limit exceeded.") from error

        try:
            self._session_tracker.check_and_record_if_below_limit(
                session_id,
                self._settings.session_challenge_limit,
                current_time,
            )
        except ValueError as error:
            self._ip_tracker.rollback_last(ip_address)
            raise ApiError(429, "SESSION_CHALLENGE_RATE_LIMITED", "Session-based challenge issuance limit exceeded.") from error
