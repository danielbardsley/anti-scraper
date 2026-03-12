from __future__ import annotations

from time import perf_counter

import httpx

from pow_harness.challenge_client import ChallengeClient
from pow_harness.error_bucket import ErrorBucket
from pow_harness.metrics_collector import MetricsCollector
from pow_harness.pow_solver import PowSolver
from pow_harness.protected_endpoint_client import ProtectedEndpointClient
from pow_harness.scenario_definition import ScenarioDefinition
from pow_harness.scenario_stop_reason import ScenarioStopReason
from pow_harness.session_provider import SessionProvider
from pow_harness.target_definition import TargetDefinition


class RunController:
    def __init__(
        self,
        session_provider: SessionProvider,
        challenge_client: ChallengeClient,
        protected_endpoint_client: ProtectedEndpointClient,
        solver: PowSolver,
        transport: httpx.BaseTransport | None = None,
    ):
        self._session_provider = session_provider
        self._challenge_client = challenge_client
        self._protected_endpoint_client = protected_endpoint_client
        self._solver = solver
        self._transport = transport

    def run(self, scenario: ScenarioDefinition, target: TargetDefinition) -> dict:
        session_material = self._session_provider.load_from_file(scenario.session_file)
        collector = MetricsCollector(
            scenario_name=scenario.name,
            target_name=target.name,
            solver_strategy=self._solver.strategy_name,
            worker_count=scenario.worker_count,
        )
        started_at = perf_counter()
        iterations_completed = 0
        stop_reason = ScenarioStopReason.ITERATION_TARGET_REACHED
        with httpx.Client(
            timeout=30.0,
            transport=self._transport,
            cookies={session_material.cookie_name: session_material.cookie_value},
        ) as client:
            while iterations_completed < scenario.iteration_count:
                elapsed = perf_counter() - started_at
                if collector.build_summary(elapsed, stop_reason.value)["totals"]["proofsSubmitted"] >= scenario.max_requests:
                    stop_reason = ScenarioStopReason.REQUEST_CAP_REACHED
                    break
                if elapsed >= scenario.max_duration_seconds:
                    stop_reason = ScenarioStopReason.DURATION_CAP_REACHED
                    break
                challenge_result = self._challenge_client.request_challenge(
                    client=client,
                    target=target,
                    request_body={"resource": "random-numbers", "count": scenario.request_count},
                )
                collector.record_challenge(challenge_result)
                if challenge_result.bucket != ErrorBucket.SUCCESS or challenge_result.payload is None:
                    iterations_completed += 1
                    continue
                solver_result = self._solver.solve(challenge_result.payload)
                collector.record_solver(solver_result)
                submit_result = self._protected_endpoint_client.submit_proof(
                    client=client,
                    target=target,
                    request_body={
                        "count": scenario.request_count,
                        "challengeId": challenge_result.payload["challengeId"],
                        "proof": {"nonces": solver_result.nonces},
                    },
                )
                collector.record_submission(submit_result)
                iterations_completed += 1
        elapsed = perf_counter() - started_at
        return collector.build_summary(elapsed, stop_reason.value)
