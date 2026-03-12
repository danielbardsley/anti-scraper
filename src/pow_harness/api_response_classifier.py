from __future__ import annotations

from http import HTTPStatus

from pow_harness.error_bucket import ErrorBucket


class ApiResponseClassifier:
    """Maps API outcomes into stable report buckets."""

    _ERROR_CODE_MAP = {
        "SESSION_REQUIRED": ErrorBucket.SESSION_REQUIRED,
        "IP_CHALLENGE_RATE_LIMITED": ErrorBucket.IP_CHALLENGE_RATE_LIMITED,
        "SESSION_CHALLENGE_RATE_LIMITED": ErrorBucket.SESSION_CHALLENGE_RATE_LIMITED,
        "TOO_MANY_OUTSTANDING_CHALLENGES": ErrorBucket.TOO_MANY_OUTSTANDING_CHALLENGES,
        "STALE_CHALLENGE_DIFFICULTY": ErrorBucket.STALE_CHALLENGE_DIFFICULTY,
        "CHALLENGE_EXPIRED": ErrorBucket.CHALLENGE_EXPIRED,
        "CHALLENGE_ALREADY_CONSUMED": ErrorBucket.CHALLENGE_ALREADY_CONSUMED,
        "REQUEST_BINDING_MISMATCH": ErrorBucket.REQUEST_BINDING_MISMATCH,
        "INVALID_PROOF": ErrorBucket.INVALID_PROOF,
    }

    def classify(self, status_code: int, payload: dict | None) -> ErrorBucket:
        if status_code == HTTPStatus.OK:
            return ErrorBucket.SUCCESS
        error_code = ((payload or {}).get("error") or {}).get("code")
        if error_code is not None:
            return self._ERROR_CODE_MAP.get(error_code, ErrorBucket.UNKNOWN)
        return ErrorBucket.UNKNOWN
