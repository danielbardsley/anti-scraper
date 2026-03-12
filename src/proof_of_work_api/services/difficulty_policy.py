from __future__ import annotations

from proof_of_work_api.config.app_settings import AppSettings


class DifficultyPolicy:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def build_for_recent_successes(self, recent_successes: int) -> tuple[int, list[int]]:
        tier = recent_successes // self._settings.requests_per_tier
        base_target_bits = self._settings.base_target_bits + (tier * self._settings.tier_target_increment)
        stage_count = tier + 1
        stage_target_bits = [
            base_target_bits + (index * self._settings.stage_target_increment)
            for index in range(stage_count)
        ]
        return tier, stage_target_bits
