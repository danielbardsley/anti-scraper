from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TargetDefinition:
    name: str
    base_url: str
    allowed: bool
    challenge_endpoint: str
    protected_endpoint: str
    challenge_request_template: dict
    protected_request_template: dict
    session_cookie_name: str
    notes: str | None = None
    tags: list[str] = field(default_factory=list)
