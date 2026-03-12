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
    challenge_burst_size: int = 1
    expiry_submit_margin_seconds: float = 0.2
    stale_success_target: int = 10
    stale_issue_retry_limit: int = 5
    stale_retry_sleep_seconds: float = 0.25
