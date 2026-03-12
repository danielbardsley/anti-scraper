from __future__ import annotations

import json
from pathlib import Path

from pow_harness.session_material import SessionMaterial


class SessionProvider:
    """Loads explicitly provided authorized session material."""

    def load_from_file(self, session_file: str | Path) -> SessionMaterial:
        payload = json.loads(Path(session_file).read_text(encoding="utf-8"))
        return SessionMaterial(
            base_url=payload["baseUrl"],
            cookie_name=payload["cookieName"],
            cookie_value=payload["cookieValue"],
        )
