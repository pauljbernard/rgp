import unittest

from tests.performance import test_performance_scalability as performance_scalability


class PerformanceHarnessTest(unittest.TestCase):
    def test_p95_uses_upper_tail_of_sorted_durations(self) -> None:
        self.assertEqual(
            performance_scalability.PerformanceScalabilityTest._p95([10.0, 20.0, 30.0, 40.0, 50.0]),
            40.0,
        )

    def test_run_workload_summarizes_failures_and_throughput(self) -> None:
        performance_scalability.PerformanceScalabilityTest.report = {"scenarios": {}}
        callables = [
            lambda: {"status": 200, "error": None, "duration_ms": 10.0},
            lambda: {"status": 201, "error": None, "duration_ms": 20.0},
            lambda: {"status": 503, "error": "timeout", "duration_ms": 30.0},
        ]

        summary = performance_scalability.PerformanceScalabilityTest._run_workload(
            "harness_mix",
            callables,
            concurrency=2,
        )

        self.assertEqual(summary["requests"], 3)
        self.assertEqual(summary["concurrency"], 2)
        self.assertEqual(summary["error_count"], 1)
        self.assertEqual(summary["error_rate"], round((1 / 3) * 100, 2))
        self.assertEqual(summary["avg_duration_ms"], 20.0)
        self.assertEqual(summary["p95_duration_ms"], 20.0)
        self.assertEqual(summary["max_duration_ms"], 30.0)
        self.assertEqual(summary["errors"][0]["status"], 503)
        self.assertIn("harness_mix", performance_scalability.PerformanceScalabilityTest.report["scenarios"])
        self.assertGreater(summary["throughput_rps"], 0.0)


if __name__ == "__main__":
    unittest.main()
