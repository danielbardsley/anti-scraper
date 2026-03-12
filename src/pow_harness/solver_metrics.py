from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolverMetrics:
    total_solve_seconds: float
    stage_durations_seconds: list[float]
    hashes_attempted: int
    worker_count: int
