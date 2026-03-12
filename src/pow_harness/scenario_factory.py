from __future__ import annotations

from pow_harness.scenario_definition import ScenarioDefinition
from pow_harness.scenario_names import ScenarioName


class ScenarioFactory:
    def create(
        self,
        *,
        scenario_name: str,
        target_name: str,
        session_file: str,
        request_count: int,
        iteration_count: int,
        worker_count: int | None,
        max_requests: int,
        max_duration_seconds: float,
        authorized_acknowledged: bool,
    ) -> ScenarioDefinition:
        name = ScenarioName(scenario_name)
        if name is ScenarioName.SINGLE_SESSION_BASELINE:
            return ScenarioDefinition(
                name=name.value,
                target_name=target_name,
                session_file=session_file,
                request_count=request_count,
                iteration_count=iteration_count,
                worker_count=worker_count or 1,
                max_requests=max_requests,
                max_duration_seconds=max_duration_seconds,
                authorized_acknowledged=authorized_acknowledged,
            )
        if name is ScenarioName.SINGLE_SESSION_FAN_OUT:
            return ScenarioDefinition(
                name=name.value,
                target_name=target_name,
                session_file=session_file,
                request_count=request_count,
                iteration_count=iteration_count,
                worker_count=worker_count or 4,
                max_requests=max_requests,
                max_duration_seconds=max_duration_seconds,
                authorized_acknowledged=authorized_acknowledged,
                high_pressure_mode=True,
            )
        if name is ScenarioName.OUTSTANDING_CHALLENGE_PRESSURE:
            return ScenarioDefinition(
                name=name.value,
                target_name=target_name,
                session_file=session_file,
                request_count=request_count,
                iteration_count=iteration_count,
                worker_count=worker_count or 1,
                max_requests=max_requests,
                max_duration_seconds=max_duration_seconds,
                authorized_acknowledged=authorized_acknowledged,
                high_pressure_mode=True,
                challenge_burst_size=max(3, request_count),
            )
        if name is ScenarioName.STALE_CHALLENGE_SPEND:
            return ScenarioDefinition(
                name=name.value,
                target_name=target_name,
                session_file=session_file,
                request_count=request_count,
                iteration_count=max(iteration_count, 12),
                worker_count=worker_count or 1,
                max_requests=max_requests,
                max_duration_seconds=max_duration_seconds,
                authorized_acknowledged=authorized_acknowledged,
            )
        if name is ScenarioName.EXPIRY_EDGE:
            return ScenarioDefinition(
                name=name.value,
                target_name=target_name,
                session_file=session_file,
                request_count=request_count,
                iteration_count=iteration_count,
                worker_count=worker_count or 1,
                max_requests=max_requests,
                max_duration_seconds=max_duration_seconds,
                authorized_acknowledged=authorized_acknowledged,
                expiry_submit_margin_seconds=0.05,
            )
        raise ValueError(f"Unsupported scenario: {scenario_name}")

    def list_names(self) -> list[str]:
        return [name.value for name in ScenarioName]
