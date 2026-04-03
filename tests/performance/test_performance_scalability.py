import json
import os
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean
from time import perf_counter
from uuid import uuid4


API_BASE = os.environ.get("RGP_API_BASE", "http://127.0.0.1:8001")
COVERAGE_DIR = Path("/Volumes/data/development/rgp/coverage")
COVERAGE_DIR.mkdir(parents=True, exist_ok=True)


class ApiError(AssertionError):
    def __init__(self, status: int, payload, path: str) -> None:
        self.status = status
        self.payload = payload
        self.path = path
        super().__init__(f"{status} for {path}: {payload}")


class PerformanceScalabilityTest(unittest.TestCase):
    token: str
    report: dict[str, object] = {"scenarios": {}}

    @classmethod
    def setUpClass(cls) -> None:
        cls.token = cls._issue_dev_token()
        health = cls._request("GET", "/healthz", token=None)
        cls._assert_equal(health["status"], "ok")

    @classmethod
    def tearDownClass(cls) -> None:
        (COVERAGE_DIR / "performance-summary.json").write_text(json.dumps(cls.report, indent=2), encoding="utf-8")

    @staticmethod
    def _assert_equal(left, right, message: str | None = None) -> None:
        if left != right:
            raise AssertionError(message or f"Expected {right!r}, got {left!r}")

    @classmethod
    def _issue_dev_token(cls) -> str:
        response = cls._request(
            "POST",
            "/api/v1/auth/dev-token",
            token=None,
            body={
                "user_id": "perf_runner",
                "tenant_id": "tenant_demo",
                "roles": ["admin", "operator", "reviewer", "submitter"],
                "expires_in_seconds": 3600,
            },
            expected_statuses={201},
        )
        return response["access_token"]

    @classmethod
    def _request(
        cls,
        method: str,
        path: str,
        *,
        token: str | None = None,
        body: dict | list | None = None,
        query: dict[str, str | int | None] | None = None,
        expected_statuses: set[int] | None = None,
    ):
        expected_statuses = expected_statuses or {200}
        url = f"{API_BASE}{path}"
        if query:
            filtered = {key: value for key, value in query.items() if value is not None}
            if filtered:
                url = f"{url}?{urllib.parse.urlencode(filtered)}"
        data = None
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read().decode("utf-8")
                if response.status not in expected_statuses:
                    raise ApiError(response.status, payload, path)
                if not payload:
                    return None
                return json.loads(payload)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                payload = raw
            if exc.code in expected_statuses:
                return payload
            raise ApiError(exc.code, payload, path) from exc

    @classmethod
    def _timed_request(
        cls,
        method: str,
        path: str,
        *,
        token: str | None = None,
        body: dict | list | None = None,
        query: dict[str, str | int | None] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict:
        started = perf_counter()
        status = 200
        error_message = None
        try:
            cls._request(method, path, token=token, body=body, query=query, expected_statuses=expected_statuses)
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status", 500)
            error_message = str(exc)
        duration_ms = (perf_counter() - started) * 1000
        return {"status": status, "error": error_message, "duration_ms": duration_ms}

    @staticmethod
    def _p95(durations: list[float]) -> float:
        if not durations:
            return 0.0
        ordered = sorted(durations)
        index = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95) - 1))
        return ordered[index]

    @classmethod
    def _run_workload(cls, name: str, callables: list, *, concurrency: int) -> dict:
        started = perf_counter()
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(fn) for fn in callables]
            for future in as_completed(futures):
                results.append(future.result())
        elapsed = perf_counter() - started
        durations = [item["duration_ms"] for item in results]
        failures = [item for item in results if item["status"] >= 400]
        summary = {
            "name": name,
            "requests": len(results),
            "concurrency": concurrency,
            "elapsed_seconds": round(elapsed, 3),
            "throughput_rps": round(len(results) / elapsed, 2) if elapsed else 0.0,
            "avg_duration_ms": round(mean(durations), 2) if durations else 0.0,
            "p95_duration_ms": round(cls._p95(durations), 2),
            "max_duration_ms": round(max(durations), 2) if durations else 0.0,
            "error_count": len(failures),
            "error_rate": round((len(failures) / len(results)) * 100, 2) if results else 0.0,
            "errors": failures[:5],
        }
        cls.report["scenarios"][name] = summary
        return summary

    def test_read_path_scalability(self) -> None:
        scenarios = []
        endpoints = [
            ("GET", "/healthz", None, None, {200}),
            ("GET", "/api/v1/requests", {"page_size": 10}, None, {200}),
            ("GET", "/api/v1/runs", {"page_size": 10}, None, {200}),
            ("GET", "/api/v1/analytics/performance/routes", {"page_size": 10, "days": 30}, None, {200}),
        ]
        for concurrency in (1, 5, 10):
            callables = []
            for _ in range(5):
                for method, path, query, body, statuses in endpoints:
                    callables.append(
                        lambda m=method, p=path, q=query, b=body, s=statuses: self._timed_request(
                            m,
                            p,
                            token=self.token if p != "/healthz" else None,
                            query=q,
                            body=b,
                            expected_statuses=s,
                        )
                    )
            summary = self._run_workload(f"read_paths_c{concurrency}", callables, concurrency=concurrency)
            scenarios.append(summary)
            self.assertEqual(summary["error_count"], 0, f"Read workload had failures: {summary['errors']}")
            self.assertLess(summary["p95_duration_ms"], 1500.0, f"Read workload p95 too high at c={concurrency}")
            self.assertGreater(summary["throughput_rps"], 5.0, f"Read workload throughput too low at c={concurrency}")
        self.report["read_path_scalability"] = scenarios

    def test_write_path_scalability(self) -> None:
        def create_callable(index: int):
            suffix = uuid4().hex[:8]
            body = {
                "template_id": "tmpl_assessment",
                "template_version": "1.4.0",
                "title": f"Perf Draft {index}-{suffix}",
                "summary": "Performance scalability request draft.",
                "priority": "medium",
                "input_payload": {
                    "assessment_id": f"asm_perf_{suffix}",
                    "revision_reason": "Standards alignment",
                    "target_window": "Spring 2026",
                },
            }
            return lambda: self._timed_request("POST", "/api/v1/requests", token=self.token, body=body, expected_statuses={201})

        callables = [create_callable(index) for index in range(12)]
        summary = self._run_workload("create_request_drafts_c4", callables, concurrency=4)
        self.assertEqual(summary["error_count"], 0, f"Create workload had failures: {summary['errors']}")
        self.assertLess(summary["p95_duration_ms"], 2500.0, "Create draft p95 latency exceeded threshold")
        self.assertGreater(summary["throughput_rps"], 2.0, "Create draft throughput was unexpectedly low")

    def test_performance_analytics_capture_workload(self) -> None:
        routes = self._request(
            "GET",
            "/api/v1/analytics/performance/routes",
            token=self.token,
            query={"page_size": 25, "days": 30},
        )
        items = routes.get("items", [])
        request_route = next((item for item in items if item["route"] == "/api/v1/requests"), None)
        self.assertIsNotNone(request_route, "Expected /api/v1/requests in performance route summaries")
        self.assertGreaterEqual(int(request_route["request_count"]), 1)


if __name__ == "__main__":
    unittest.main()
