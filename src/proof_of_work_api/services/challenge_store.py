from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock

from proof_of_work_api.domain.challenge_record import ChallengeRecord


class ChallengeStore:
    def __init__(self) -> None:
        self._records: dict[str, ChallengeRecord] = {}
        self._lock = Lock()

    def save(self, record: ChallengeRecord) -> None:
        with self._lock:
            self._purge_expired_locked(datetime.now(timezone.utc))
            self._records[record.challenge_id] = record

    def get(self, challenge_id: str) -> ChallengeRecord | None:
        with self._lock:
            return self._records.get(challenge_id)

    def count_outstanding(self, session_id: str, current_time: datetime) -> int:
        normalized = current_time.astimezone(timezone.utc)
        with self._lock:
            self._purge_expired_locked(normalized)
            return sum(
                1
                for record in self._records.values()
                if record.session_id == session_id and not record.is_expired(normalized) and not record.is_consumed()
            )

    def consume(self, challenge_id: str, current_time: datetime) -> ChallengeRecord | None:
        normalized = current_time.astimezone(timezone.utc)
        with self._lock:
            record = self._records.get(challenge_id)
            if record is None:
                return None
            if record.is_expired(normalized) or record.is_consumed():
                return record
            record.consumed_at = normalized
            return record

    def _purge_expired_locked(self, current_time: datetime) -> None:
        expired_ids = [
            challenge_id
            for challenge_id, record in self._records.items()
            if record.is_expired(current_time) and record.is_consumed()
        ]
        for challenge_id in expired_ids:
            self._records.pop(challenge_id, None)
