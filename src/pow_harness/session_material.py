from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionMaterial:
    base_url: str
    cookie_name: str
    cookie_value: str
