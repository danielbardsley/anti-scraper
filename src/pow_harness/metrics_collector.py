from __future__ import annotations

from statistics import median

from pow_harness.challenge_request_result import ChallengeRequestResult
from pow_harness.protected_request_result import ProtectedRequestResult
from pow_harness.run_metrics import RunMetrics
from pow_harness.solver_result import SolverResult


class MetricsCollector:
    def __init__(self, scenario_name: str, target_name: str, solver_strategy: str, worker_count: int):
        self._metrics = RunMetrics(
            scenario_name=scenario_name,
            target_name=target_name,
            solver_strategy=solver_strategy,
            worker_count=worker_count,
        )

    def record_challenge(self, result: ChallengeRequestResult) -> None:
        self._metrics.total_challenges_requested += 1
        self._metrics.challenge_latency_seconds.append(result.latency_seconds)
        self._metrics.increment_error(result.bucket.value)

    def record_solver(self, result: SolverResult) -> None:
        self._metrics.solve_time_seconds.append(result.metrics.total_solve_seconds)
        self._metrics.hashes_attempted.append(result.metrics.hashes_attempted)

    def record_submission(self, result: ProtectedRequestResult) -> None:
        self._metrics.total_proofs_submitted += 1
        self._metrics.submit_latency_seconds.append(result.latency_seconds)
        self._metrics.increment_error(result.bucket.value)
        if result.bucket.value == "success":
            self._metrics.total_successes += 1
            tier = (((result.payload or {}).get("meta") or {}).get("tier"))
            if isinstance(tier, int):
                self._metrics.success_tiers.append(tier)

    def build_summary(self, elapsed_seconds: float, stop_reason: str) -> dict:
        successes_per_minute = 0.0 if elapsed_seconds <= 0 else (self._metrics.total_successes / elapsed_seconds) * 60.0
        return {
            "scenario": self._metrics.scenario_name,
            "target": self._metrics.target_name,
            "solverStrategy": self._metrics.solver_strategy,
            "workerCount": self._metrics.worker_count,
            "elapsedSeconds": round(elapsed_seconds, 6),
            "stopReason": stop_reason,
            "totals": {
                "challengesRequested": self._metrics.total_challenges_requested,
                "proofsSubmitted": self._metrics.total_proofs_submitted,
                "successes": self._metrics.total_successes,
            },
            "rates": {
                "successesPerMinute": round(successes_per_minute, 4),
            },
            "timings": {
                "challengeMedianSeconds": self._median_or_none(self._metrics.challenge_latency_seconds),
                "submitMedianSeconds": self._median_or_none(self._metrics.submit_latency_seconds),
                "solveMedianSeconds": self._median_or_none(self._metrics.solve_time_seconds),
            },
            "solver": {
                "medianHashesAttempted": self._median_or_none(self._metrics.hashes_attempted),
            },
            "tierDistribution": self._distribution(self._metrics.success_tiers),
            "errorCounts": dict(sorted(self._metrics.error_counts.items())),
        }

    def _distribution(self, values: list[int]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for value in values:
            key = str(value)
            counts[key] = counts.get(key, 0) + 1
        return counts

    def _median_or_none(self, values: list[float] | list[int]) -> float | None:
        if not values:
            return None
        return round(float(median(values)), 6)
