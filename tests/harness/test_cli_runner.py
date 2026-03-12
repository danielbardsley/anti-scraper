from __future__ import annotations

import json
from pathlib import Path

from pow_harness.cli_runner import CliRunner


def test_cli_runner_parses_inputs_and_writes_reports(tmp_path: Path, capsys) -> None:
    target_file = tmp_path / "targets.json"
    session_file = tmp_path / "session.json"
    report_dir = tmp_path / "reports"
    target_file.write_text(
        json.dumps(
            {
                "targets": [
                    {
                        "name": "demo",
                        "baseUrl": "http://127.0.0.1:1",
                        "allowed": True,
                        "challengeEndpoint": "/v1/pow/challenges",
                        "protectedEndpoint": "/v1/random-numbers",
                        "challengeRequestTemplate": {"resource": "random-numbers", "count": 1},
                        "protectedRequestTemplate": {"count": 1},
                        "sessionCookieName": "pow_session",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    session_file.write_text(
        json.dumps(
            {
                "baseUrl": "http://127.0.0.1:1",
                "cookieName": "pow_session",
                "cookieValue": "test-session",
            }
        ),
        encoding="utf-8",
    )

    exit_code = CliRunner().run(
        [
            "--target-config",
            str(target_file),
            "--target",
            "demo",
            "--scenario",
            "single-session-baseline",
            "--session-file",
            str(session_file),
            "--iterations",
            "1",
            "--max-requests",
            "1",
            "--max-duration-seconds",
            "1",
            "--report-dir",
            str(report_dir),
            "--authorized-testing-ack",
        ]
    )
    captured = capsys.readouterr()
    body = json.loads(captured.out)
    assert exit_code == 0
    assert body["summary"]["scenario"] == "single-session-baseline"
    assert Path(body["outputs"]["json"]).exists()
    assert Path(body["outputs"]["markdown"]).exists()
