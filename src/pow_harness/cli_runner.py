from __future__ import annotations

import json

from pow_harness.cli_argument_parser import CliArgumentParser
from pow_harness.harness_app import HarnessApp
from pow_harness.run_guardrails_factory import RunGuardrailsFactory
from pow_harness.scenario_factory import ScenarioFactory
from pow_harness.target_config_loader import TargetConfigLoader


class CliRunner:
    def run(self, argv: list[str] | None = None) -> int:
        parser = CliArgumentParser().build()
        args = parser.parse_args(argv)
        targets = TargetConfigLoader().load(args.target_config)
        guardrails = RunGuardrailsFactory().create(
            max_requests_per_run=args.max_requests,
            max_duration_seconds=args.max_duration_seconds,
            max_local_workers=args.max_local_workers,
        )
        scenario = ScenarioFactory().create(
            scenario_name=args.scenario,
            target_name=args.target,
            session_file=args.session_file,
            request_count=args.request_count,
            iteration_count=args.iterations,
            worker_count=args.workers,
            max_requests=args.max_requests,
            max_duration_seconds=args.max_duration_seconds,
            authorized_acknowledged=args.authorized_testing_ack,
        )
        result = HarnessApp(targets=targets, run_guardrails=guardrails, report_directory=args.report_dir).execute(scenario)
        print(json.dumps(result, indent=2))
        return 0
