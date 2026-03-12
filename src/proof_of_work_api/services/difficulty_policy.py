from __future__ import annotations

from proof_of_work_api.config.app_settings import AppSettings


class DifficultyPolicy:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def build_for_recent_successes(self, recent_successes: int) -> tuple[int, list[int]]:
        tier = recent_successes // self._settings.requests_per_tier
        return self._build_for_tier(tier)

    def build_for_session_and_source_successes(
        self,
        session_recent_successes: int,
        source_recent_successes: int,
    ) -> tuple[int, list[int]]:
        session_tier = session_recent_successes // self._settings.requests_per_tier
        source_tier = source_recent_successes // self._settings.source_requests_per_tier
        return self._build_for_tier(max(session_tier, source_tier))

    def _build_for_tier(self, tier: int) -> tuple[int, list[int]]:
        base_target_bits = self._settings.base_target_bits + (tier * self._settings.tier_target_increment)
        stage_count = tier + 1
        stage_target_bits = [
            base_target_bits + (index * self._settings.stage_target_increment)
            for index in range(stage_count)
        ]
        return tier, stage_target_bits
