from __future__ import annotations

import pytest

from pow_harness.authorized_testing_required_error import AuthorizedTestingRequiredError
from pow_harness.guardrail_violation_error import GuardrailViolationError
from pow_harness.run_guardrails import RunGuardrails
from pow_harness.target_definition import TargetDefinition
from pow_harness.target_policy import TargetPolicy


def build_policy() -> TargetPolicy:
    return TargetPolicy(
        targets=[
            TargetDefinition(
                name="demo",
                base_url="http://example.test",
                allowed=True,
                challenge_endpoint="/v1/pow/challenges",
                protected_endpoint="/v1/random-numbers",
                challenge_request_template={"resource": "random-numbers", "count": 1},
                protected_request_template={"count": 1},
                session_cookie_name="pow_session",
            )
        ],
        run_guardrails=RunGuardrails(max_requests_per_run=5, max_duration_seconds=60.0, max_local_workers=2),
    )


def test_policy_requires_authorized_acknowledgment() -> None:
    policy = build_policy()
    with pytest.raises(AuthorizedTestingRequiredError):
        policy.validate_execution(
            target_name="demo",
            authorized_acknowledged=False,
            worker_count=1,
            max_requests=5,
            max_duration_seconds=10.0,
        )


def test_policy_blocks_excessive_worker_count() -> None:
    policy = build_policy()
    with pytest.raises(GuardrailViolationError):
        policy.validate_execution(
            target_name="demo",
            authorized_acknowledged=True,
            worker_count=3,
            max_requests=5,
            max_duration_seconds=10.0,
        )


def test_policy_blocks_unlisted_target() -> None:
    policy = build_policy()
    with pytest.raises(GuardrailViolationError):
        policy.validate_execution(
            target_name="missing",
            authorized_acknowledged=True,
            worker_count=1,
            max_requests=5,
            max_duration_seconds=10.0,
        )
