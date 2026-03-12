from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from proof_of_work_api.config.app_settings import AppSettings
from proof_of_work_api.models.random_numbers_request import RandomNumbersRequest
from proof_of_work_api.services.api_error import ApiError
from proof_of_work_api.services.challenge_store import ChallengeStore
from proof_of_work_api.services.difficulty_policy import DifficultyPolicy
from proof_of_work_api.services.request_canonicalizer import RequestCanonicalizer
from proof_of_work_api.services.sliding_window_tracker import SlidingWindowTracker


class ProofVerifier:
    def __init__(
        self,
        settings: AppSettings,
        challenge_store: ChallengeStore,
        request_canonicalizer: RequestCanonicalizer,
        difficulty_policy: DifficultyPolicy,
        session_success_tracker: SlidingWindowTracker,
        source_success_tracker: SlidingWindowTracker,
    ) -> None:
        self._settings = settings
        self._challenge_store = challenge_store
        self._request_canonicalizer = request_canonicalizer
        self._difficulty_policy = difficulty_policy
        self._session_success_tracker = session_success_tracker
        self._source_success_tracker = source_success_tracker

    def verify_and_consume(self, request: RandomNumbersRequest, session_id: str, source_key: str) -> dict:
        count = request.count or self._settings.default_random_count
        self._validate_count(count)

        challenge = self._challenge_store.get(request.challenge_id)
        if challenge is None:
            raise ApiError(404, "CHALLENGE_NOT_FOUND", "Challenge was not found.")

        current_time = datetime.now(timezone.utc)
        if challenge.is_expired(current_time):
            raise ApiError(410, "CHALLENGE_EXPIRED", "Challenge expired before proof submission.")
        if challenge.is_consumed():
            raise ApiError(409, "CHALLENGE_ALREADY_CONSUMED", "Challenge was already used.")
        if challenge.session_id != session_id:
            raise ApiError(401, "SESSION_MISMATCH", "Challenge does not belong to this session.")
        if challenge.resource != "random-numbers":
            raise ApiError(400, "RESOURCE_MISMATCH", "Challenge is not valid for this resource.")

        request_hash = self._request_canonicalizer.hash_random_numbers_request(count)
        if challenge.request_hash != request_hash:
            raise ApiError(401, "REQUEST_BINDING_MISMATCH", "Proof is not valid for this request body.")

        current_session_successes = self._session_success_tracker.count(session_id, current_time)
        current_source_successes = self._source_success_tracker.count(source_key, current_time)
        current_required_tier, current_stage_targets = self._difficulty_policy.build_for_session_and_source_successes(
            current_session_successes,
            current_source_successes,
        )
        if challenge.tier < current_required_tier or challenge.stage_target_bits != current_stage_targets:
            raise ApiError(409, "STALE_CHALLENGE_DIFFICULTY", "Challenge difficulty is now below the current required tier.")

        nonces = request.proof.nonces
        if len(nonces) != len(challenge.stage_target_bits):
            raise ApiError(400, "INVALID_PROOF", "Incorrect number of nonces for the current challenge tier.")

        previous_value = challenge.seed
        for index, nonce in enumerate(nonces):
            digest_hex = hashlib.sha256(f"{previous_value}:{index}:{nonce}".encode("utf-8")).hexdigest()
            target_bits = challenge.stage_target_bits[index]
            if self._leading_zero_bits(bytes.fromhex(digest_hex)) < target_bits:
                raise ApiError(401, "INVALID_PROOF", f"Proof failed at stage {index}.", {"stageIndex": index})
            previous_value = digest_hex

        consumed = self._challenge_store.consume(challenge.challenge_id, current_time)
        if consumed is None:
            raise ApiError(404, "CHALLENGE_NOT_FOUND", "Challenge was not found during consumption.")
        if consumed.is_expired(current_time):
            raise ApiError(410, "CHALLENGE_EXPIRED", "Challenge expired before proof consumption.")
        if consumed.consumed_at != current_time:
            raise ApiError(409, "CHALLENGE_ALREADY_CONSUMED", "Challenge was already used.")

        return {
            "count": count,
            "challengeId": challenge.challenge_id,
            "tier": challenge.tier,
            "stages": len(challenge.stage_target_bits),
            "sessionId": session_id,
            "sourceKey": source_key,
        }

    def _validate_count(self, count: int) -> None:
        if count < self._settings.min_random_count or count > self._settings.max_random_count:
            raise ApiError(
                400,
                "INVALID_COUNT",
                f"Count must be between {self._settings.min_random_count} and {self._settings.max_random_count}.",
                {"minCount": self._settings.min_random_count, "maxCount": self._settings.max_random_count},
            )

    @staticmethod
    def _leading_zero_bits(digest: bytes) -> int:
        bit_count = 0
        for value in digest:
            if value == 0:
                bit_count += 8
                continue
            return bit_count + (8 - value.bit_length())
        return bit_count
