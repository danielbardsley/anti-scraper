from __future__ import annotations

import secrets


class RandomNumberService:
    def generate(self, count: int) -> list[int]:
        return [secrets.randbits(32) for _ in range(count)]
