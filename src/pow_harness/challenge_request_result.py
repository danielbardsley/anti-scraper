from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from pow_harness.error_bucket import ErrorBucket


@dataclass(frozen=True)
class ChallengeRequestResult:
    started_at: float
    finished_at: float
    latency_seconds: float
    bucket: ErrorBucket
    payload: dict | None

    @classmethod
    def from_result(cls, started_at: float, bucket: ErrorBucket, payload: dict | None) -> "ChallengeRequestResult":
        finished_at = perf_counter()
        return cls(
            started_at=started_at,
            finished_at=finished_at,
            latency_seconds=finished_at - started_at,
            bucket=bucket,
            payload=payload,
        )
