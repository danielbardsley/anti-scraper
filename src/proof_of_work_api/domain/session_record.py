from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    created_at: datetime
    last_seen_at: datetime
    issued_by_ip: str
    idle_expires_at: datetime
    absolute_expires_at: datetime

    def is_expired(self, current_time: datetime) -> bool:
        normalized = current_time.astimezone(timezone.utc)
        return normalized >= self.idle_expires_at or normalized >= self.absolute_expires_at
