from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class ReportWriter:
    def __init__(self, report_directory: str | Path):
        self._report_directory = Path(report_directory)
        self._report_directory.mkdir(parents=True, exist_ok=True)

    def write(self, summary: dict) -> dict[str, str]:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        slug = summary["scenario"].replace("_", "-")
        json_path = self._report_directory / f"{timestamp}-{slug}.json"
        markdown_path = self._report_directory / f"{timestamp}-{slug}.md"
        json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        markdown_path.write_text(self._to_markdown(summary), encoding="utf-8")
        return {"json": str(json_path), "markdown": str(markdown_path)}

    def _to_markdown(self, summary: dict) -> str:
        totals = summary["totals"]
        rates = summary["rates"]
        timings = summary["timings"]
        return "\n".join(
            [
                f"# Harness Report — {summary['scenario']}",
                "",
                f"- Target: {summary['target']}",
                f"- Solver: {summary['solverStrategy']}",
                f"- Workers: {summary['workerCount']}",
                f"- Stop reason: {summary['stopReason']}",
                f"- Elapsed seconds: {summary['elapsedSeconds']}",
                "",
                "## Totals",
                f"- Challenges requested: {totals['challengesRequested']}",
                f"- Proofs submitted: {totals['proofsSubmitted']}",
                f"- Successes: {totals['successes']}",
                f"- Successes per minute: {rates['successesPerMinute']}",
                "",
                "## Timings",
                f"- Challenge median seconds: {timings['challengeMedianSeconds']}",
                f"- Submit median seconds: {timings['submitMedianSeconds']}",
                f"- Solve median seconds: {timings['solveMedianSeconds']}",
                "",
                "## Error Counts",
                *[f"- {key}: {value}" for key, value in summary["errorCounts"].items()],
                "",
                "## Tier Distribution",
                *[f"- tier {key}: {value}" for key, value in summary["tierDistribution"].items()],
            ]
        )
