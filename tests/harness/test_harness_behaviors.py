from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from pow_harness.harness_app import HarnessApp
from pow_harness.run_guardrails import RunGuardrails
from pow_harness.scenario_definition import ScenarioDefinition
from pow_harness.scenario_names import ScenarioName
from pow_harness.target_definition import TargetDefinition
from proof_of_work_api.main import create_app




def leading_zero_bits(digest: bytes) -> int:
    bit_count = 0
    for value in digest:
        if value == 0:
            bit_count += 8
            continue
        return bit_count + (8 - value.bit_length())
    return bit_count


def solve_challenge(challenge: dict) -> list[str]:
    import hashlib

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


class HarnessClientTransport(httpx.BaseTransport):
    def __init__(self, test_client: TestClient):
        self._test_client = test_client

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = self._test_client.request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            content=request.content,
        )
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )


def build_app(tmp_path: Path) -> tuple[HarnessApp, str]:
    api_client = TestClient(create_app())
    challenge_response = api_client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
    session_cookie = api_client.cookies.get("pow_session")
    assert challenge_response.status_code == 200
    assert session_cookie is not None
    bootstrap_submit = api_client.post(
        "/v1/random-numbers",
        json={
            "count": 1,
            "challengeId": challenge_response.json()["challengeId"],
            "proof": {"nonces": solve_challenge(challenge_response.json())},
        },
    )
    assert bootstrap_submit.status_code == 200
    session_file = tmp_path / "session.json"
    session_file.write_text(
        json.dumps(
            {
                "baseUrl": str(api_client.base_url).rstrip("/"),
                "cookieName": "pow_session",
                "cookieValue": session_cookie,
            }
        ),
        encoding="utf-8",
    )
    app = HarnessApp(
        targets=[
            TargetDefinition(
                name="demo",
                base_url=str(api_client.base_url).rstrip("/"),
                allowed=True,
                challenge_endpoint="/v1/pow/challenges",
                protected_endpoint="/v1/random-numbers",
                challenge_request_template={"resource": "random-numbers", "count": 1},
                protected_request_template={"count": 1},
                session_cookie_name="pow_session",
            )
        ],
        run_guardrails=RunGuardrails(max_requests_per_run=20, max_duration_seconds=30.0, max_local_workers=4),
        report_directory=tmp_path / "reports",
        transport=HarnessClientTransport(api_client),
    )
    return app, str(session_file)


def test_fan_out_scenario_submits_work_in_parallel_shape(tmp_path: Path) -> None:
    app, session_file = build_app(tmp_path)
    result = app.execute(
        ScenarioDefinition(
            name=ScenarioName.SINGLE_SESSION_FAN_OUT.value,
            target_name="demo",
            session_file=session_file,
            request_count=1,
            iteration_count=4,
            worker_count=2,
            max_requests=10,
            max_duration_seconds=10.0,
            authorized_acknowledged=True,
        )
    )
    assert result["summary"]["totals"]["proofsSubmitted"] >= 1
    assert result["summary"]["workerCount"] == 2


def test_pressure_scenario_records_outstanding_challenge_rejections(tmp_path: Path) -> None:
    app, session_file = build_app(tmp_path)
    result = app.execute(
        ScenarioDefinition(
            name=ScenarioName.OUTSTANDING_CHALLENGE_PRESSURE.value,
            target_name="demo",
            session_file=session_file,
            request_count=1,
            iteration_count=3,
            worker_count=1,
            max_requests=10,
            max_duration_seconds=10.0,
            authorized_acknowledged=True,
            high_pressure_mode=True,
            challenge_burst_size=4,
        )
    )
    assert result["summary"]["errorCounts"].get("too_many_outstanding_challenges", 0) >= 1


def test_stale_scenario_records_stale_difficulty_rejection(tmp_path: Path) -> None:
    app, session_file = build_app(tmp_path)
    result = app.execute(
        ScenarioDefinition(
            name=ScenarioName.STALE_CHALLENGE_SPEND.value,
            target_name="demo",
            session_file=session_file,
            request_count=1,
            iteration_count=12,
            worker_count=1,
            max_requests=20,
            max_duration_seconds=10.0,
            authorized_acknowledged=True,
        )
    )
    assert result["summary"]["errorCounts"].get("stale_challenge_difficulty", 0) >= 1
