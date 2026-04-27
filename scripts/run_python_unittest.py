#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path


class JsonTextTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.records: list[dict[str, object]] = []
        self._test_started_at: float | None = None

    def startTest(self, test):  # noqa: N802
        self._test_started_at = time.perf_counter()
        super().startTest(test)

    def _duration_seconds(self) -> float:
        if self._test_started_at is None:
            return 0.0
        return round(time.perf_counter() - self._test_started_at, 6)

    def _record(self, test, status: str, details: str | None = None) -> None:
        self.records.append(
            {
                "id": test.id(),
                "name": self.getDescription(test),
                "status": status,
                "duration_seconds": self._duration_seconds(),
                "details": details,
            }
        )

    def addSuccess(self, test):  # noqa: N802
        super().addSuccess(test)
        self._record(test, "passed")

    def addFailure(self, test, err):  # noqa: N802
        super().addFailure(test, err)
        self._record(test, "failed", self._exc_info_to_string(err, test))

    def addError(self, test, err):  # noqa: N802
        super().addError(test, err)
        self._record(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):  # noqa: N802
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addExpectedFailure(self, test, err):  # noqa: N802
        super().addExpectedFailure(test, err)
        self._record(test, "expected_failure", self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):  # noqa: N802
        super().addUnexpectedSuccess(test)
        self._record(test, "unexpected_success")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run unittest discovery and emit a JSON results artifact.")
    parser.add_argument("--suite-name", required=True)
    parser.add_argument("--start-dir", required=True)
    parser.add_argument("--pattern", default="test_*.py")
    parser.add_argument("--top-level-dir")
    parser.add_argument("--output", required=True)
    parser.add_argument("--verbosity", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started_at = datetime.now(UTC)
    started_perf = time.perf_counter()

    loader = unittest.defaultTestLoader
    discover_kwargs = {
        "start_dir": args.start_dir,
        "pattern": args.pattern,
    }
    if args.top_level_dir:
        discover_kwargs["top_level_dir"] = args.top_level_dir
    suite = loader.discover(**discover_kwargs)
    runner = unittest.TextTestRunner(verbosity=args.verbosity, resultclass=JsonTextTestResult)
    result: JsonTextTestResult = runner.run(suite)

    ended_at = datetime.now(UTC)
    payload = {
        "runner": "unittest",
        "suite_name": args.suite_name,
        "start_dir": args.start_dir,
        "pattern": args.pattern,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "ended_at": ended_at.isoformat().replace("+00:00", "Z"),
        "duration_seconds": round(time.perf_counter() - started_perf, 6),
        "successful": result.wasSuccessful(),
        "summary": {
            "total": result.testsRun,
            "passed": sum(1 for record in result.records if record["status"] == "passed"),
            "failed": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "expected_failures": len(result.expectedFailures),
            "unexpected_successes": len(result.unexpectedSuccesses),
        },
        "tests": result.records,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
