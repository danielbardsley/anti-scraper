from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from proof_of_work_api.config.app_settings import AppSettings
from proof_of_work_api.domain.challenge_record import ChallengeRecord
from proof_of_work_api.models.challenge_issue_request import ChallengeIssueRequest
from proof_of_work_api.services.api_error import ApiError
from proof_of_work_api.services.challenge_rate_limiter import ChallengeRateLimiter
from proof_of_work_api.services.challenge_store import ChallengeStore
from proof_of_work_api.services.difficulty_policy import DifficultyPolicy
from proof_of_work_api.services.request_canonicalizer import RequestCanonicalizer
from proof_of_work_api.services.sliding_window_tracker import SlidingWindowTracker


class ChallengeService:
    def __init__(
        self,
        settings: AppSettings,
        challenge_store: ChallengeStore,
        difficulty_policy: DifficultyPolicy,
        success_tracker: SlidingWindowTracker,
        request_canonicalizer: RequestCanonicalizer,
        rate_limiter: ChallengeRateLimiter,
    ) -> None:
        self._settings = settings
        self._challenge_store = challenge_store
        self._difficulty_policy = difficulty_policy
        self._success_tracker = success_tracker
        self._request_canonicalizer = request_canonicalizer
        self._rate_limiter = rate_limiter

    def issue_challenge(self, request: ChallengeIssueRequest, session_id: str, issued_ip: str) -> dict:
        if request.resource != "random-numbers":
            raise ApiError(400, "UNSUPPORTED_RESOURCE", "Only the random-numbers resource is supported.")

        count = request.count or self._settings.default_random_count
        self._validate_count(count)

        issued_at = datetime.now(timezone.utc)
        self._rate_limiter.enforce_and_record(issued_ip, session_id, issued_at)

        recent_successes = self._success_tracker.count(session_id, issued_at)
        tier, stage_target_bits = self._difficulty_policy.build_for_recent_successes(recent_successes)

        challenge_id = uuid.uuid4().hex
        request_hash = self._request_canonicalizer.hash_random_numbers_request(count)
        seed = secrets.token_hex(self._settings.challenge_seed_bytes)
        expires_at = issued_at + timedelta(seconds=self._settings.challenge_ttl_seconds)

        record = ChallengeRecord(
            challenge_id=challenge_id,
            session_id=session_id,
            resource=request.resource,
            request_hash=request_hash,
            tier=tier,
            stage_target_bits=stage_target_bits,
            seed=seed,
            issued_at=issued_at,
            expires_at=expires_at,
            issued_ip=issued_ip,
        )
        try:
            outstanding_after_save = self._challenge_store.save_if_outstanding_below_limit(
                record,
                self._settings.max_outstanding_challenges,
                issued_at,
            )
        except ValueError as error:
            raise ApiError(429, "TOO_MANY_OUTSTANDING_CHALLENGES", "Session has too many outstanding challenges.") from error

        return {
            "challengeId": challenge_id,
            "resource": request.resource,
            "requestHash": request_hash,
            "issuedAt": issued_at.isoformat(),
            "expiresAt": expires_at.isoformat(),
            "tier": tier,
            "algorithm": {
                "name": "sequential-leading-zero-sha256",
                "hashFunction": "SHA-256",
                "stages": [
                    {"index": index, "targetBits": target_bits}
                    for index, target_bits in enumerate(stage_target_bits)
                ],
            },
            "seed": seed,
            "session": {
                "outstandingChallenges": outstanding_after_save,
            },
        }

    def _validate_count(self, count: int) -> None:
        if count < self._settings.min_random_count or count > self._settings.max_random_count:
            raise ApiError(
                400,
                "INVALID_COUNT",
                f"Count must be between {self._settings.min_random_count} and {self._settings.max_random_count}.",
                {"minCount": self._settings.min_random_count, "maxCount": self._settings.max_random_count},
            )
