from __future__ import annotations

from pow_harness.api_response_classifier import ApiResponseClassifier
from pow_harness.baseline_pow_solver import BaselinePowSolver
from pow_harness.error_bucket import ErrorBucket


def test_classifier_maps_known_api_errors() -> None:
    classifier = ApiResponseClassifier()
    assert classifier.classify(429, {"error": {"code": "IP_CHALLENGE_RATE_LIMITED"}}) == ErrorBucket.IP_CHALLENGE_RATE_LIMITED
    assert classifier.classify(410, {"error": {"code": "CHALLENGE_EXPIRED"}}) == ErrorBucket.CHALLENGE_EXPIRED


def test_baseline_solver_solves_known_vector() -> None:
    challenge = {
        "seed": "seed-1",
        "algorithm": {
            "stages": [
                {"index": 0, "targetBits": 4},
                {"index": 1, "targetBits": 4},
            ]
        },
    }
    result = BaselinePowSolver().solve(challenge)
    assert len(result.nonces) == 2
    assert result.metrics.total_solve_seconds >= 0
    assert result.metrics.hashes_attempted >= 2
