from __future__ import annotations

import hashlib
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from proof_of_work_api.main import create_app


@contextmanager
def temporary_env(**values: str):
    original = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def solve_challenge(challenge: dict) -> list[str]:
    nonces: list[str] = []
    previous_value = challenge["seed"]
    for stage in challenge["algorithm"]["stages"]:
        nonce = 0
        while True:
            digest_hex = hashlib.sha256(f"{previous_value}:{stage['index']}:{nonce}".encode("utf-8")).hexdigest()
            if leading_zero_bits(bytes.fromhex(digest_hex)) >= stage["targetBits"]:
                nonces.append(str(nonce))
                previous_value = digest_hex
                break
            nonce += 1
    return nonces


def leading_zero_bits(digest: bytes) -> int:
    bit_count = 0
    for value in digest:
        if value == 0:
            bit_count += 8
            continue
        return bit_count + (8 - value.bit_length())
    return bit_count


def issue_challenge(client: TestClient, count: int = 4) -> dict:
    response = client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": count})
    assert response.status_code == 200
    return response.json()


def submit_proof(client: TestClient, challenge: dict, count: int = 4):
    proof = solve_challenge(challenge)
    return client.post(
        "/v1/random-numbers",
        json={
            "count": count,
            "challengeId": challenge["challengeId"],
            "proof": {"nonces": proof},
        },
    )


def test_session_cookie_bootstrap_and_success_flow() -> None:
    client = TestClient(create_app())
    challenge = issue_challenge(client, 4)
    assert "pow_session" in client.cookies

    response = submit_proof(client, challenge, 4)
    assert response.status_code == 200
    body = response.json()
    assert len(body["numbers"]) == 4
    assert body["meta"]["tier"] == 0
    assert body["meta"]["stages"] == 1


def test_replay_is_rejected() -> None:
    client = TestClient(create_app())
    challenge = issue_challenge(client, 2)
    proof = solve_challenge(challenge)
    payload = {
        "count": 2,
        "challengeId": challenge["challengeId"],
        "proof": {"nonces": proof},
    }
    first = client.post("/v1/random-numbers", json=payload)
    second = client.post("/v1/random-numbers", json=payload)
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CHALLENGE_ALREADY_CONSUMED"


def test_request_binding_mismatch_is_rejected() -> None:
    client = TestClient(create_app())
    challenge = issue_challenge(client, 2)
    proof = solve_challenge(challenge)
    response = client.post(
        "/v1/random-numbers",
        json={
            "count": 3,
            "challengeId": challenge["challengeId"],
            "proof": {"nonces": proof},
        },
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "REQUEST_BINDING_MISMATCH"


def test_session_mismatch_is_rejected() -> None:
    client_one = TestClient(create_app())
    client_two = TestClient(create_app())
    challenge = issue_challenge(client_one, 2)
    response = submit_proof(client_two, challenge, 2)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_REQUIRED"


def test_tier_increases_after_ten_successes() -> None:
    client = TestClient(create_app())
    for _ in range(10):
        challenge = issue_challenge(client, 1)
        result = submit_proof(client, challenge, 1)
        assert result.status_code == 200
    elevated = client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
    assert elevated.status_code == 200
    challenge = elevated.json()
    assert challenge["tier"] == 1
    assert len(challenge["algorithm"]["stages"]) == 2


def test_expired_challenge_is_rejected() -> None:
    app = create_app()
    client = TestClient(app)
    challenge = issue_challenge(client, 1)
    proof = solve_challenge(challenge)
    container = app.state.container
    record = container.challenge_store.get(challenge["challengeId"])
    assert record is not None
    record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    response = client.post(
        "/v1/random-numbers",
        json={"count": 1, "challengeId": challenge["challengeId"], "proof": {"nonces": proof}},
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "CHALLENGE_EXPIRED"


def test_too_many_outstanding_challenges_are_rejected() -> None:
    app = create_app()
    client = TestClient(app)
    issue_challenge(client, 1)
    issue_challenge(client, 1)
    third = client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
    assert third.status_code == 429
    assert third.json()["error"]["code"] == "TOO_MANY_OUTSTANDING_CHALLENGES"


def test_stockpiled_low_tier_challenge_becomes_stale() -> None:
    client = TestClient(create_app())
    stockpiled = issue_challenge(client, 1)
    for _ in range(10):
        challenge = issue_challenge(client, 1)
        result = submit_proof(client, challenge, 1)
        assert result.status_code == 200
    stale = submit_proof(client, stockpiled, 1)
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_CHALLENGE_DIFFICULTY"


def test_protected_endpoint_requires_session() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/v1/random-numbers",
        json={"count": 1, "challengeId": "missing", "proof": {"nonces": ["1"]}},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "SESSION_REQUIRED"


def test_ip_challenge_rate_limit_is_enforced() -> None:
    with temporary_env(POW_IP_CHALLENGE_LIMIT="1", POW_MAX_OUTSTANDING_CHALLENGES="10"):
        client = TestClient(create_app())
        first = client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
        second = client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
        assert first.status_code == 200
        assert second.status_code == 429
        assert second.json()["error"]["code"] == "IP_CHALLENGE_RATE_LIMITED"


def test_session_challenge_rate_limit_is_enforced() -> None:
    with temporary_env(POW_SESSION_CHALLENGE_LIMIT="1", POW_IP_CHALLENGE_LIMIT="10", POW_MAX_OUTSTANDING_CHALLENGES="10"):
        client = TestClient(create_app())
        first = client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
        second = client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
        assert first.status_code == 200
        assert second.status_code == 429
        assert second.json()["error"]["code"] == "SESSION_CHALLENGE_RATE_LIMITED"


def test_trusted_proxy_header_is_used_only_for_trusted_proxy() -> None:
    with temporary_env(POW_IP_CHALLENGE_LIMIT="1", POW_MAX_OUTSTANDING_CHALLENGES="10", POW_TRUSTED_PROXY_IPS="testclient"):
        client = TestClient(create_app())
        first = client.post(
            "/v1/pow/challenges",
            json={"resource": "random-numbers", "count": 1},
            headers={"x-forwarded-for": "198.51.100.10"},
        )
        second = client.post(
            "/v1/pow/challenges",
            json={"resource": "random-numbers", "count": 1},
            headers={"x-forwarded-for": "198.51.100.11"},
        )
        assert first.status_code == 200
        assert second.status_code == 200

    with temporary_env(POW_IP_CHALLENGE_LIMIT="1", POW_MAX_OUTSTANDING_CHALLENGES="10"):
        client = TestClient(create_app())
        first = client.post(
            "/v1/pow/challenges",
            json={"resource": "random-numbers", "count": 1},
            headers={"x-forwarded-for": "198.51.100.10"},
        )
        second = client.post(
            "/v1/pow/challenges",
            json={"resource": "random-numbers", "count": 1},
            headers={"x-forwarded-for": "198.51.100.11"},
        )
        assert first.status_code == 200
        assert second.status_code == 429
        assert second.json()["error"]["code"] == "IP_CHALLENGE_RATE_LIMITED"


def test_old_expired_challenges_are_eventually_purged() -> None:
    with temporary_env(POW_EXPIRED_CHALLENGE_RETENTION_SECONDS="1"):
        app = create_app()
        client = TestClient(app)
        challenge = issue_challenge(client, 1)
        record = app.state.container.challenge_store.get(challenge["challengeId"])
        assert record is not None
        record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=5)
        client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
        assert app.state.container.challenge_store.get(challenge["challengeId"]) is None


def test_telemetry_endpoint_reports_counters() -> None:
    client = TestClient(create_app())
    challenge = issue_challenge(client, 1)
    response = submit_proof(client, challenge, 1)
    assert response.status_code == 200
    telemetry = client.get("/v1/telemetry")
    assert telemetry.status_code == 200
    counters = telemetry.json()["counters"]
    assert counters["sessions.created"] >= 1
    assert counters["challenges.issued"] >= 1
    assert counters["protected.success"] >= 1
