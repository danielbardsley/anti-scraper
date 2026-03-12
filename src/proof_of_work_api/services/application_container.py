from __future__ import annotations

from proof_of_work_api.config.app_settings import AppSettings
from proof_of_work_api.services.challenge_rate_limiter import ChallengeRateLimiter
from proof_of_work_api.services.challenge_service import ChallengeService
from proof_of_work_api.services.challenge_store import ChallengeStore
from proof_of_work_api.services.client_ip_resolver import ClientIpResolver
from proof_of_work_api.services.difficulty_policy import DifficultyPolicy
from proof_of_work_api.services.proof_verifier import ProofVerifier
from proof_of_work_api.services.random_number_service import RandomNumberService
from proof_of_work_api.services.request_canonicalizer import RequestCanonicalizer
from proof_of_work_api.services.session_store import SessionStore
from proof_of_work_api.services.sliding_window_tracker import SlidingWindowTracker
from proof_of_work_api.services.telemetry_service import TelemetryService


class ApplicationContainer:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.challenge_store = ChallengeStore(settings)
        self.session_store = SessionStore(settings)
        self.request_canonicalizer = RequestCanonicalizer()
        self.session_success_tracker = SlidingWindowTracker(settings.success_window_seconds)
        self.source_success_tracker = SlidingWindowTracker(settings.success_window_seconds)
        self.challenge_rate_limiter = ChallengeRateLimiter(settings)
        self.difficulty_policy = DifficultyPolicy(settings)
        self.client_ip_resolver = ClientIpResolver(settings)
        self.telemetry_service = TelemetryService()
        self.challenge_service = ChallengeService(
            settings=settings,
            challenge_store=self.challenge_store,
            difficulty_policy=self.difficulty_policy,
            session_success_tracker=self.session_success_tracker,
            source_success_tracker=self.source_success_tracker,
            request_canonicalizer=self.request_canonicalizer,
            rate_limiter=self.challenge_rate_limiter,
        )
        self.proof_verifier = ProofVerifier(
            settings=settings,
            challenge_store=self.challenge_store,
            request_canonicalizer=self.request_canonicalizer,
            difficulty_policy=self.difficulty_policy,
            session_success_tracker=self.session_success_tracker,
            source_success_tracker=self.source_success_tracker,
        )
        self.random_number_service = RandomNumberService()
