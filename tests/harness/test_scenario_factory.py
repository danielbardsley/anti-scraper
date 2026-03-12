from __future__ import annotations

from pow_harness.scenario_factory import ScenarioFactory
from pow_harness.scenario_names import ScenarioName


def test_factory_creates_baseline_with_safe_defaults() -> None:
    scenario = ScenarioFactory().create(
        scenario_name=ScenarioName.SINGLE_SESSION_BASELINE.value,
        target_name="demo",
        session_file="session.json",
        request_count=1,
        iteration_count=5,
        worker_count=None,
        max_requests=10,
        max_duration_seconds=60.0,
        authorized_acknowledged=True,
    )
    assert scenario.worker_count == 1
    assert scenario.high_pressure_mode is False


def test_factory_marks_pressure_scenario_as_high_pressure() -> None:
    scenario = ScenarioFactory().create(
        scenario_name=ScenarioName.OUTSTANDING_CHALLENGE_PRESSURE.value,
        target_name="demo",
        session_file="session.json",
        request_count=1,
        iteration_count=5,
        worker_count=None,
        max_requests=10,
        max_duration_seconds=60.0,
        authorized_acknowledged=True,
    )
    assert scenario.high_pressure_mode is True


def test_factory_enforces_stale_scenario_minimum_iterations() -> None:
    scenario = ScenarioFactory().create(
        scenario_name=ScenarioName.STALE_CHALLENGE_SPEND.value,
        target_name="demo",
        session_file="session.json",
        request_count=1,
        iteration_count=2,
        worker_count=None,
        max_requests=20,
        max_duration_seconds=60.0,
        authorized_acknowledged=True,
    )
    assert scenario.iteration_count >= 12
