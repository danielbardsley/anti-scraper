from __future__ import annotations

from pow_harness.run_guardrails import RunGuardrails


class RunGuardrailsFactory:
    def create(
        self,
        *,
        max_requests_per_run: int,
        max_duration_seconds: float,
        max_local_workers: int,
        require_authorized_ack: bool = True,
    ) -> RunGuardrails:
        return RunGuardrails(
            require_authorized_ack=require_authorized_ack,
            max_requests_per_run=max_requests_per_run,
            max_duration_seconds=max_duration_seconds,
            max_local_workers=max_local_workers,
        )
