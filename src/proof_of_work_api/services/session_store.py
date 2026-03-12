from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock

from proof_of_work_api.config.app_settings import AppSettings
from proof_of_work_api.domain.session_record import SessionRecord


class SessionStore:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._records: dict[str, SessionRecord] = {}
        self._lock = Lock()

    def get_or_create(self, session_id: str | None, issued_ip: str, current_time: datetime) -> tuple[SessionRecord, bool]:
        normalized = current_time.astimezone(timezone.utc)
        with self._lock:
            self._purge_locked(normalized)
            if session_id:
                record = self._records.get(session_id)
                if record and not record.is_expired(normalized):
                    record.last_seen_at = normalized
                    record.idle_expires_at = normalized + timedelta(seconds=self._settings.session_idle_ttl_seconds)
                    return record, False
            fresh = self._create_locked(issued_ip, normalized)
            return fresh, True

    def get_required(self, session_id: str | None, current_time: datetime) -> SessionRecord | None:
        if not session_id:
            return None
        normalized = current_time.astimezone(timezone.utc)
        with self._lock:
            self._purge_locked(normalized)
            record = self._records.get(session_id)
            if record is None or record.is_expired(normalized):
                return None
            record.last_seen_at = normalized
            record.idle_expires_at = normalized + timedelta(seconds=self._settings.session_idle_ttl_seconds)
            return record

    def _create_locked(self, issued_ip: str, current_time: datetime) -> SessionRecord:
        session_id = secrets.token_urlsafe(32)
        record = SessionRecord(
            session_id=session_id,
            created_at=current_time,
            last_seen_at=current_time,
            issued_by_ip=issued_ip,
            idle_expires_at=current_time + timedelta(seconds=self._settings.session_idle_ttl_seconds),
            absolute_expires_at=current_time + timedelta(seconds=self._settings.session_absolute_ttl_seconds),
        )
        self._records[session_id] = record
        return record

    def _purge_locked(self, current_time: datetime) -> None:
        expired = [key for key, record in self._records.items() if record.is_expired(current_time)]
        for key in expired:
            self._records.pop(key, None)
