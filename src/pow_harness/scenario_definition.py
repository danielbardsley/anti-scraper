from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioDefinition:
    name: str
    target_name: str
    session_file: str
    request_count: int
    iteration_count: int
    worker_count: int
    max_requests: int
    max_duration_seconds: float
    authorized_acknowledged: bool
    high_pressure_mode: bool = False
