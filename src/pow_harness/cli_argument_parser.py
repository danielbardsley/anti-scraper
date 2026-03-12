from __future__ import annotations

import argparse

from pow_harness.scenario_factory import ScenarioFactory


class CliArgumentParser:
    def build(self) -> argparse.ArgumentParser:
        scenario_factory = ScenarioFactory()
        parser = argparse.ArgumentParser(
            prog="pow-harness",
            description="Authorized defensive evaluation harness for the proof-of-work demo.",
        )
        parser.add_argument("--target-config", required=True, help="Path to the target config JSON file.")
        parser.add_argument("--target", required=True, help="Target name from the allowlisted config.")
        parser.add_argument("--scenario", required=True, choices=scenario_factory.list_names())
        parser.add_argument("--session-file", required=True, help="Path to operator-provided authorized session JSON.")
        parser.add_argument("--request-count", type=int, default=1)
        parser.add_argument("--iterations", type=int, default=5)
        parser.add_argument("--workers", type=int, default=None)
        parser.add_argument("--max-requests", type=int, default=25)
        parser.add_argument("--max-duration-seconds", type=float, default=60.0)
        parser.add_argument("--max-local-workers", type=int, default=8)
        parser.add_argument("--report-dir", default="artifacts/reports")
        parser.add_argument(
            "--authorized-testing-ack",
            action="store_true",
            help="Required acknowledgment that this run targets a system you are explicitly authorized to test.",
        )
        return parser
