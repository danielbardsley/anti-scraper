from __future__ import annotations

from dataclasses import dataclass

from pow_harness.solver_metrics import SolverMetrics


@dataclass(frozen=True)
class SolverResult:
    nonces: list[str]
    metrics: SolverMetrics
