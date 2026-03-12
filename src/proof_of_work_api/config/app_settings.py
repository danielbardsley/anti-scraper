from __future__ import annotations

import os
from pathlib import Path


class AppSettings:
    def __init__(self) -> None:
        self.requests_per_tier = int(os.getenv("POW_REQUESTS_PER_TIER", "10"))
        self.source_requests_per_tier = int(os.getenv("POW_SOURCE_REQUESTS_PER_TIER", "20"))
        self.success_window_seconds = int(os.getenv("POW_SUCCESS_WINDOW_SECONDS", "600"))
        self.challenge_ttl_seconds = int(os.getenv("POW_CHALLENGE_TTL_SECONDS", "90"))
        self.base_target_bits = int(os.getenv("POW_BASE_TARGET_BITS", "13"))
        self.tier_target_increment = int(os.getenv("POW_TIER_TARGET_INCREMENT", "1"))
        self.stage_target_increment = int(os.getenv("POW_STAGE_TARGET_INCREMENT", "1"))
        self.min_random_count = int(os.getenv("POW_MIN_RANDOM_COUNT", "1"))
        self.max_random_count = int(os.getenv("POW_MAX_RANDOM_COUNT", "64"))
        self.default_random_count = int(os.getenv("POW_DEFAULT_RANDOM_COUNT", "10"))
        self.challenge_seed_bytes = int(os.getenv("POW_CHALLENGE_SEED_BYTES", "16"))
        self.session_idle_ttl_seconds = int(os.getenv("POW_SESSION_IDLE_TTL_SECONDS", str(24 * 60 * 60)))
        self.session_absolute_ttl_seconds = int(os.getenv("POW_SESSION_ABSOLUTE_TTL_SECONDS", str(7 * 24 * 60 * 60)))
        self.ip_challenge_limit = int(os.getenv("POW_IP_CHALLENGE_LIMIT", "60"))
        self.session_challenge_limit = int(os.getenv("POW_SESSION_CHALLENGE_LIMIT", "30"))
        self.challenge_rate_window_seconds = int(os.getenv("POW_CHALLENGE_RATE_WINDOW_SECONDS", "600"))
        self.max_outstanding_challenges = int(os.getenv("POW_MAX_OUTSTANDING_CHALLENGES", "2"))
        self.expired_challenge_retention_seconds = int(os.getenv("POW_EXPIRED_CHALLENGE_RETENTION_SECONDS", "300"))
        self.session_cookie_name = os.getenv("POW_SESSION_COOKIE_NAME", "pow_session")
        self.secure_cookie = os.getenv("POW_SECURE_COOKIE", "false").lower() == "true"
        self.base_path = self._normalize_base_path(os.getenv("POW_BASE_PATH", ""))
        self.trusted_proxy_ips = {
            value.strip() for value in os.getenv("POW_TRUSTED_PROXY_IPS", "").split(",") if value.strip()
        }
        self.forwarded_for_header = os.getenv("POW_FORWARDED_FOR_HEADER", "x-forwarded-for").lower()
        self.project_root = Path(__file__).resolve().parents[3]
        self.web_root = self.project_root / "src" / "proof_of_work_api" / "web"
        self._validate()

    def _normalize_base_path(self, value: str) -> str:
        cleaned = value.strip()
        if cleaned in {"", "/"}:
            return ""
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        return cleaned.rstrip("/")

    def _validate(self) -> None:
        positive_values = {
            "POW_REQUESTS_PER_TIER": self.requests_per_tier,
            "POW_SOURCE_REQUESTS_PER_TIER": self.source_requests_per_tier,
            "POW_SUCCESS_WINDOW_SECONDS": self.success_window_seconds,
            "POW_CHALLENGE_TTL_SECONDS": self.challenge_ttl_seconds,
            "POW_BASE_TARGET_BITS": self.base_target_bits,
            "POW_SESSION_IDLE_TTL_SECONDS": self.session_idle_ttl_seconds,
            "POW_SESSION_ABSOLUTE_TTL_SECONDS": self.session_absolute_ttl_seconds,
            "POW_IP_CHALLENGE_LIMIT": self.ip_challenge_limit,
            "POW_SESSION_CHALLENGE_LIMIT": self.session_challenge_limit,
            "POW_CHALLENGE_RATE_WINDOW_SECONDS": self.challenge_rate_window_seconds,
            "POW_MAX_OUTSTANDING_CHALLENGES": self.max_outstanding_challenges,
            "POW_EXPIRED_CHALLENGE_RETENTION_SECONDS": self.expired_challenge_retention_seconds,
        }
        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive.")
        if self.min_random_count <= 0 or self.max_random_count < self.min_random_count:
            raise ValueError("Random count bounds are invalid.")
        if not self.web_root.exists():
            raise ValueError(f"Web root does not exist: {self.web_root}")
