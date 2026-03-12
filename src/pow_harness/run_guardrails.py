from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunGuardrails:
    require_authorized_ack: bool = True
    max_requests_per_run: int = 250
    max_duration_seconds: float = 300.0
    max_local_workers: int = 8
