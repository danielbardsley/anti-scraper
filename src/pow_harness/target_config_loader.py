from __future__ import annotations

import json
from pathlib import Path

from pow_harness.target_definition import TargetDefinition


class TargetConfigLoader:
    def load(self, config_file: str | Path) -> list[TargetDefinition]:
        payload = json.loads(Path(config_file).read_text(encoding="utf-8"))
        targets = payload.get("targets", payload)
        return [
            TargetDefinition(
                name=target["name"],
                base_url=target["baseUrl"],
                allowed=target["allowed"],
                challenge_endpoint=target["challengeEndpoint"],
                protected_endpoint=target["protectedEndpoint"],
                challenge_request_template=target.get("challengeRequestTemplate", {}),
                protected_request_template=target.get("protectedRequestTemplate", {}),
                session_cookie_name=target["sessionCookieName"],
                notes=target.get("notes"),
                tags=target.get("tags", []),
            )
            for target in targets
        ]
