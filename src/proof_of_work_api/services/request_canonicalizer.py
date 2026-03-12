from __future__ import annotations

import hashlib
import json


class RequestCanonicalizer:
    def hash_random_numbers_request(self, count: int) -> str:
        canonical_payload = {
            "count": count,
        }
        canonical_json = json.dumps(canonical_payload, separators=(",", ":"), sort_keys=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
