from __future__ import annotations

import json
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from pow_harness.harness_app import HarnessApp
from pow_harness.run_guardrails import RunGuardrails
from pow_harness.scenario_definition import ScenarioDefinition
from pow_harness.target_definition import TargetDefinition
from proof_of_work_api.main import create_app


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


def test_harness_executes_baseline_run_and_writes_reports(tmp_path: Path) -> None:
    api_app = create_app()
    api_client = TestClient(api_app)
    challenge_response = api_client.post("/v1/pow/challenges", json={"resource": "random-numbers", "count": 1})
    session_cookie = api_client.cookies.get("pow_session")
    assert challenge_response.status_code == 200
    assert session_cookie is not None

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
        run_guardrails=RunGuardrails(max_requests_per_run=3, max_duration_seconds=30.0, max_local_workers=1),
        report_directory=tmp_path / "reports",
        transport=HarnessClientTransport(api_client),
    )

    result = app.execute(
        ScenarioDefinition(
            name="single_session_baseline",
            target_name="demo",
            session_file=str(session_file),
            request_count=1,
            iteration_count=2,
            worker_count=1,
            max_requests=3,
            max_duration_seconds=10.0,
            authorized_acknowledged=True,
        )
    )

    assert result["summary"]["totals"]["challengesRequested"] == 2
    assert result["summary"]["totals"]["proofsSubmitted"] == 2
    assert result["summary"]["totals"]["successes"] == 2
    assert Path(result["outputs"]["json"]).exists()
    assert Path(result["outputs"]["markdown"]).exists()
