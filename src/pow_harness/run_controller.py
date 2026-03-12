from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import Lock
from time import perf_counter, sleep

import httpx

from pow_harness.challenge_client import ChallengeClient
from pow_harness.error_bucket import ErrorBucket
from pow_harness.metrics_collector import MetricsCollector
from pow_harness.pow_solver import PowSolver
from pow_harness.protected_endpoint_client import ProtectedEndpointClient
from pow_harness.scenario_definition import ScenarioDefinition
from pow_harness.scenario_names import ScenarioName
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
        scenario_name = self._normalize_scenario_name(scenario.name)
        if scenario_name is ScenarioName.SINGLE_SESSION_BASELINE:
            return self._run_serial_loop(scenario, target)
        if scenario_name is ScenarioName.SINGLE_SESSION_FAN_OUT:
            return self._run_fan_out_loop(scenario, target)
        if scenario_name is ScenarioName.OUTSTANDING_CHALLENGE_PRESSURE:
            return self._run_outstanding_pressure(scenario, target)
        if scenario_name is ScenarioName.STALE_CHALLENGE_SPEND:
            return self._run_stale_challenge_scenario(scenario, target)
        if scenario_name is ScenarioName.EXPIRY_EDGE:
            return self._run_expiry_edge_scenario(scenario, target)
        raise ValueError(f"Unsupported scenario execution: {scenario.name}")

    def _run_serial_loop(self, scenario: ScenarioDefinition, target: TargetDefinition) -> dict:
        session_material = self._session_provider.load_from_file(scenario.session_file)
        collector = self._create_collector(scenario, target)
        started_at = perf_counter()
        iterations_completed = 0
        stop_reason = ScenarioStopReason.ITERATION_TARGET_REACHED
        with self._build_client(session_material) as client:
            while iterations_completed < scenario.iteration_count:
                stop_reason = self._evaluate_stop_reason(collector, started_at, scenario)
                if stop_reason is not None:
                    break
                self._execute_single_fetch_solve_submit(collector, client, target, scenario.request_count)
                iterations_completed += 1
        return collector.build_summary(perf_counter() - started_at, (stop_reason or ScenarioStopReason.ITERATION_TARGET_REACHED).value)

    def _run_fan_out_loop(self, scenario: ScenarioDefinition, target: TargetDefinition) -> dict:
        collector = self._create_collector(scenario, target)
        started_at = perf_counter()
        stop_reason: ScenarioStopReason | None = None
        completed_iterations = 0
        lock = Lock()

        def worker() -> int:
            local_completed = 0
            session_material = self._session_provider.load_from_file(scenario.session_file)
            with self._build_client(session_material) as client:
                while True:
                    with lock:
                        current_stop = self._evaluate_stop_reason(collector, started_at, scenario)
                        if current_stop is not None:
                            return local_completed
                        nonlocal completed_iterations
                        if completed_iterations >= scenario.iteration_count:
                            return local_completed
                        completed_iterations += 1
                    self._execute_single_fetch_solve_submit(collector, client, target, scenario.request_count, lock)
                    local_completed += 1

        with ThreadPoolExecutor(max_workers=scenario.worker_count) as executor:
            futures = [executor.submit(worker) for _ in range(scenario.worker_count)]
            for future in as_completed(futures):
                future.result()

        stop_reason = self._evaluate_stop_reason(collector, started_at, scenario)
        return collector.build_summary(perf_counter() - started_at, (stop_reason or ScenarioStopReason.ITERATION_TARGET_REACHED).value)

    def _run_outstanding_pressure(self, scenario: ScenarioDefinition, target: TargetDefinition) -> dict:
        session_material = self._session_provider.load_from_file(scenario.session_file)
        collector = self._create_collector(scenario, target)
        started_at = perf_counter()
        stop_reason: ScenarioStopReason | None = None
        with self._build_client(session_material) as client:
            while True:
                stop_reason = self._evaluate_stop_reason(collector, started_at, scenario)
                if stop_reason is not None:
                    break
                fetched_payloads: list[dict] = []
                for _ in range(scenario.challenge_burst_size):
                    challenge_result = self._request_challenge(collector, client, target, scenario.request_count)
                    if challenge_result.bucket == ErrorBucket.SUCCESS and challenge_result.payload is not None:
                        fetched_payloads.append(challenge_result.payload)
                if not fetched_payloads:
                    break
                challenge = fetched_payloads[0]
                solver_result = self._solver.solve(challenge)
                collector.record_solver(solver_result)
                submit_result = self._protected_endpoint_client.submit_proof(
                    client=client,
                    target=target,
                    request_body={
                        "count": scenario.request_count,
                        "challengeId": challenge["challengeId"],
                        "proof": {"nonces": solver_result.nonces},
                    },
                )
                collector.record_submission(submit_result)
        return collector.build_summary(perf_counter() - started_at, (stop_reason or ScenarioStopReason.ITERATION_TARGET_REACHED).value)

    def _run_stale_challenge_scenario(self, scenario: ScenarioDefinition, target: TargetDefinition) -> dict:
        session_material = self._session_provider.load_from_file(scenario.session_file)
        collector = self._create_collector(scenario, target)
        started_at = perf_counter()
        with self._build_client(session_material) as client:
            stockpiled_result = self._request_challenge(collector, client, target, scenario.request_count)
            if stockpiled_result.bucket != ErrorBucket.SUCCESS or stockpiled_result.payload is None:
                return collector.build_summary(perf_counter() - started_at, ScenarioStopReason.ITERATION_TARGET_REACHED.value)
            stockpiled_payload = stockpiled_result.payload
            stockpiled_solution = self._solver.solve(stockpiled_payload)
            collector.record_solver(stockpiled_solution)

            successful_spends = 0
            issue_retries = 0
            while successful_spends < scenario.stale_success_target:
                stop_reason = self._evaluate_stop_reason(collector, started_at, scenario)
                if stop_reason is not None:
                    return collector.build_summary(perf_counter() - started_at, stop_reason.value)

                challenge_result = self._request_challenge(collector, client, target, scenario.request_count)
                if challenge_result.bucket == ErrorBucket.SUCCESS and challenge_result.payload is not None:
                    issue_retries = 0
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
                    if submit_result.bucket == ErrorBucket.SUCCESS:
                        successful_spends += 1
                    continue

                if challenge_result.bucket in {
                    ErrorBucket.IP_CHALLENGE_RATE_LIMITED,
                    ErrorBucket.SESSION_CHALLENGE_RATE_LIMITED,
                    ErrorBucket.TOO_MANY_OUTSTANDING_CHALLENGES,
                }:
                    issue_retries += 1
                    if issue_retries > scenario.stale_issue_retry_limit:
                        return collector.build_summary(perf_counter() - started_at, ScenarioStopReason.ITERATION_TARGET_REACHED.value)
                    sleep(scenario.stale_retry_sleep_seconds)
                    continue

                return collector.build_summary(perf_counter() - started_at, ScenarioStopReason.ITERATION_TARGET_REACHED.value)

            stale_submit = self._protected_endpoint_client.submit_proof(
                client=client,
                target=target,
                request_body={
                    "count": scenario.request_count,
                    "challengeId": stockpiled_payload["challengeId"],
                    "proof": {"nonces": stockpiled_solution.nonces},
                },
            )
            collector.record_submission(stale_submit)
        return collector.build_summary(perf_counter() - started_at, ScenarioStopReason.ITERATION_TARGET_REACHED.value)

    def _run_expiry_edge_scenario(self, scenario: ScenarioDefinition, target: TargetDefinition) -> dict:
        session_material = self._session_provider.load_from_file(scenario.session_file)
        collector = self._create_collector(scenario, target)
        started_at = perf_counter()
        iterations_completed = 0
        stop_reason: ScenarioStopReason | None = None
        with self._build_client(session_material) as client:
            while iterations_completed < scenario.iteration_count:
                stop_reason = self._evaluate_stop_reason(collector, started_at, scenario)
                if stop_reason is not None:
                    break
                challenge_result = self._request_challenge(collector, client, target, scenario.request_count)
                if challenge_result.bucket != ErrorBucket.SUCCESS or challenge_result.payload is None:
                    iterations_completed += 1
                    continue
                solver_result = self._solver.solve(challenge_result.payload)
                collector.record_solver(solver_result)
                self._sleep_until_expiry_margin(challenge_result.payload, scenario.expiry_submit_margin_seconds)
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
        return collector.build_summary(perf_counter() - started_at, (stop_reason or ScenarioStopReason.ITERATION_TARGET_REACHED).value)

    def _execute_single_fetch_solve_submit(
        self,
        collector: MetricsCollector,
        client: httpx.Client,
        target: TargetDefinition,
        request_count: int,
        lock: Lock | None = None,
    ) -> None:
        challenge_result = self._request_challenge(collector, client, target, request_count, lock)
        if challenge_result.bucket != ErrorBucket.SUCCESS or challenge_result.payload is None:
            return
        solver_result = self._solver.solve(challenge_result.payload)
        self._record_with_optional_lock(lock, lambda: collector.record_solver(solver_result))
        submit_result = self._protected_endpoint_client.submit_proof(
            client=client,
            target=target,
            request_body={
                "count": request_count,
                "challengeId": challenge_result.payload["challengeId"],
                "proof": {"nonces": solver_result.nonces},
            },
        )
        self._record_with_optional_lock(lock, lambda: collector.record_submission(submit_result))

    def _request_challenge(
        self,
        collector: MetricsCollector,
        client: httpx.Client,
        target: TargetDefinition,
        request_count: int,
        lock: Lock | None = None,
    ):
        challenge_result = self._challenge_client.request_challenge(
            client=client,
            target=target,
            request_body={"resource": "random-numbers", "count": request_count},
        )
        self._record_with_optional_lock(lock, lambda: collector.record_challenge(challenge_result))
        return challenge_result

    def _create_collector(self, scenario: ScenarioDefinition, target: TargetDefinition) -> MetricsCollector:
        return MetricsCollector(
            scenario_name=scenario.name,
            target_name=target.name,
            solver_strategy=self._solver.strategy_name,
            worker_count=scenario.worker_count,
        )

    def _build_client(self, session_material) -> httpx.Client:
        return httpx.Client(
            timeout=30.0,
            transport=self._transport,
            cookies={session_material.cookie_name: session_material.cookie_value},
        )

    def _evaluate_stop_reason(
        self,
        collector: MetricsCollector,
        started_at: float,
        scenario: ScenarioDefinition,
    ) -> ScenarioStopReason | None:
        elapsed = perf_counter() - started_at
        totals = collector.build_summary(elapsed, ScenarioStopReason.ITERATION_TARGET_REACHED.value)["totals"]
        if totals["proofsSubmitted"] >= scenario.max_requests:
            return ScenarioStopReason.REQUEST_CAP_REACHED
        if elapsed >= scenario.max_duration_seconds:
            return ScenarioStopReason.DURATION_CAP_REACHED
        return None

    def _sleep_until_expiry_margin(self, challenge_payload: dict, margin_seconds: float) -> None:
        expires_at_raw = challenge_payload.get("expiresAt")
        if expires_at_raw is None:
            return
        expires_at = datetime.fromisoformat(expires_at_raw)
        now = datetime.now(timezone.utc)
        seconds_until_submit = (expires_at - now).total_seconds() - margin_seconds
        if seconds_until_submit > 0:
            sleep(min(seconds_until_submit, 2.0))

    def _record_with_optional_lock(self, lock: Lock | None, callback) -> None:
        if lock is None:
            callback()
            return
        with lock:
            callback()

    def _normalize_scenario_name(self, scenario_name: str) -> ScenarioName:
        return ScenarioName(scenario_name.replace("_", "-"))
