from __future__ import annotations

from pathlib import Path

import httpx

from pow_harness.api_response_classifier import ApiResponseClassifier
from pow_harness.baseline_pow_solver import BaselinePowSolver
from pow_harness.challenge_client import ChallengeClient
from pow_harness.protected_endpoint_client import ProtectedEndpointClient
from pow_harness.report_writer import ReportWriter
from pow_harness.run_controller import RunController
from pow_harness.run_guardrails import RunGuardrails
from pow_harness.scenario_definition import ScenarioDefinition
from pow_harness.session_provider import SessionProvider
from pow_harness.target_definition import TargetDefinition
from pow_harness.target_policy import TargetPolicy


class HarnessApp:
    def __init__(self, targets: list[TargetDefinition], run_guardrails: RunGuardrails, report_directory: str | Path, transport: httpx.BaseTransport | None = None):
        self._policy = TargetPolicy(targets=targets, run_guardrails=run_guardrails)
        classifier = ApiResponseClassifier()
        self._controller = RunController(
            session_provider=SessionProvider(),
            challenge_client=ChallengeClient(classifier),
            protected_endpoint_client=ProtectedEndpointClient(classifier),
            solver=BaselinePowSolver(),
            transport=transport,
        )
        self._writer = ReportWriter(report_directory)

    def execute(self, scenario: ScenarioDefinition) -> dict:
        target = self._policy.validate_execution(
            target_name=scenario.target_name,
            authorized_acknowledged=scenario.authorized_acknowledged,
            worker_count=scenario.worker_count,
            max_requests=scenario.max_requests,
            max_duration_seconds=scenario.max_duration_seconds,
        )
        summary = self._controller.run(scenario, target)
        output_paths = self._writer.write(summary)
        return {"summary": summary, "outputs": output_paths}
