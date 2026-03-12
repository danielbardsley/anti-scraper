from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunMetrics:
    scenario_name: str
    target_name: str
    solver_strategy: str
    worker_count: int
    total_challenges_requested: int = 0
    total_proofs_submitted: int = 0
    total_successes: int = 0
    challenge_latency_seconds: list[float] = field(default_factory=list)
    submit_latency_seconds: list[float] = field(default_factory=list)
    solve_time_seconds: list[float] = field(default_factory=list)
    hashes_attempted: list[int] = field(default_factory=list)
    success_tiers: list[int] = field(default_factory=list)
    error_counts: dict[str, int] = field(default_factory=dict)

    def increment_error(self, bucket: str) -> None:
        self.error_counts[bucket] = self.error_counts.get(bucket, 0) + 1
