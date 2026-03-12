from __future__ import annotations

from urllib.parse import urlparse

from pow_harness.authorized_testing_required_error import AuthorizedTestingRequiredError
from pow_harness.guardrail_violation_error import GuardrailViolationError
from pow_harness.run_guardrails import RunGuardrails
from pow_harness.target_definition import TargetDefinition


class TargetPolicy:
    """Enforces allowlists and run-level guardrails."""

    def __init__(self, targets: list[TargetDefinition], run_guardrails: RunGuardrails):
        self._targets = {target.name: target for target in targets}
        self._run_guardrails = run_guardrails

    def resolve_target(self, target_name: str) -> TargetDefinition:
        target = self._targets.get(target_name)
        if target is None:
            raise GuardrailViolationError(f"Target '{target_name}' is not configured.")
        if not target.allowed:
            raise GuardrailViolationError(f"Target '{target_name}' is configured but not approved for execution.")
        return target

    def validate_execution(
        self,
        *,
        target_name: str,
        authorized_acknowledged: bool,
        worker_count: int,
        max_requests: int,
        max_duration_seconds: float,
    ) -> TargetDefinition:
        target = self.resolve_target(target_name)
        if self._run_guardrails.require_authorized_ack and not authorized_acknowledged:
            raise AuthorizedTestingRequiredError(
                "Run blocked. Pass the explicit authorized-testing acknowledgment before executing scenarios."
            )
        if worker_count > self._run_guardrails.max_local_workers:
            raise GuardrailViolationError(
                f"Worker count {worker_count} exceeds local limit {self._run_guardrails.max_local_workers}."
            )
        if max_requests > self._run_guardrails.max_requests_per_run:
            raise GuardrailViolationError(
                f"Requested max_requests {max_requests} exceeds policy limit {self._run_guardrails.max_requests_per_run}."
            )
        if max_duration_seconds > self._run_guardrails.max_duration_seconds:
            raise GuardrailViolationError(
                f"Requested duration {max_duration_seconds}s exceeds policy limit {self._run_guardrails.max_duration_seconds}s."
            )
        parsed = urlparse(target.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise GuardrailViolationError(f"Target '{target_name}' has an invalid base URL: {target.base_url}")
        return target
