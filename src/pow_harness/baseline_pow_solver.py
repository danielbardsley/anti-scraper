from __future__ import annotations

import hashlib
from time import perf_counter

from pow_harness.leading_zero_counter import LeadingZeroCounter
from pow_harness.pow_solver import PowSolver
from pow_harness.solver_metrics import SolverMetrics
from pow_harness.solver_result import SolverResult


class BaselinePowSolver(PowSolver):
    def __init__(self, leading_zero_counter: LeadingZeroCounter | None = None):
        self._leading_zero_counter = leading_zero_counter or LeadingZeroCounter()

    @property
    def strategy_name(self) -> str:
        return "baseline-python"

    def solve(self, challenge: dict) -> SolverResult:
        started_at = perf_counter()
        hashes_attempted = 0
        stage_durations: list[float] = []
        nonces: list[str] = []
        previous_value = challenge["seed"]
        for stage in challenge["algorithm"]["stages"]:
            stage_started_at = perf_counter()
            nonce = 0
            while True:
                hashes_attempted += 1
                digest_hex = hashlib.sha256(f"{previous_value}:{stage['index']}:{nonce}".encode("utf-8")).hexdigest()
                if self._leading_zero_counter.count(bytes.fromhex(digest_hex)) >= stage["targetBits"]:
                    nonces.append(str(nonce))
                    previous_value = digest_hex
                    stage_durations.append(perf_counter() - stage_started_at)
                    break
                nonce += 1
        total_solve_seconds = perf_counter() - started_at
        return SolverResult(
            nonces=nonces,
            metrics=SolverMetrics(
                total_solve_seconds=total_solve_seconds,
                stage_durations_seconds=stage_durations,
                hashes_attempted=hashes_attempted,
                worker_count=1,
            ),
        )
