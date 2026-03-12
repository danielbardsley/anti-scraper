from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class ChallengeRecord:
    challenge_id: str
    session_id: str
    resource: str
    request_hash: str
    tier: int
    stage_target_bits: list[int]
    seed: str
    issued_at: datetime
    expires_at: datetime
    issued_ip: str
    consumed_at: datetime | None = field(default=None)

    def is_expired(self, current_time: datetime) -> bool:
        normalized = current_time.astimezone(timezone.utc)
        return normalized >= self.expires_at

    def is_consumed(self) -> bool:
        return self.consumed_at is not None
