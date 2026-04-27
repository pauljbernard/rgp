import fs from "node:fs";
import path from "node:path";

const root = "/Volumes/data/development/rgp/coverage";
const resultsDir = path.join(root, "test-results");

function fileExists(filePath) {
  return fs.existsSync(filePath);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function safeReadJson(filePath) {
  return fileExists(filePath) ? readJson(filePath) : null;
}

function normalizeVitestReport(label, filePath) {
  const report = safeReadJson(filePath);
  if (!report) {
    return null;
  }

  const files = Array.isArray(report.testResults) ? report.testResults : [];
  const suiteStartedAt = files.length > 0 ? Math.min(...files.map((file) => file.startTime).filter((value) => typeof value === "number")) : null;
  const suiteEndedAt = files.length > 0 ? Math.max(...files.map((file) => file.endTime).filter((value) => typeof value === "number")) : null;
  const tests = files.flatMap((file) =>
    Array.isArray(file.assertionResults)
      ? file.assertionResults.map((test) => ({
          id: `${file.name}::${test.fullName ?? test.title ?? "unnamed test"}`,
          name: test.fullName ?? test.title ?? "unnamed test",
          status: test.status,
          duration_seconds: typeof test.duration === "number" ? Number((test.duration / 1000).toFixed(6)) : null,
          details: Array.isArray(test.failureMessages) && test.failureMessages.length > 0 ? test.failureMessages.join("\n\n") : null
        }))
      : []
  );

  return {
    runner: "vitest",
    suite_name: label,
    started_at: typeof suiteStartedAt === "number" ? new Date(suiteStartedAt).toISOString() : null,
    ended_at: typeof suiteEndedAt === "number" ? new Date(suiteEndedAt).toISOString() : null,
    duration_seconds: typeof suiteStartedAt === "number" && typeof suiteEndedAt === "number"
      ? Number(((suiteEndedAt - suiteStartedAt) / 1000).toFixed(6))
      : null,
    successful: Boolean(report.success),
    summary: {
      total: report.numTotalTests ?? tests.length,
      passed: report.numPassedTests ?? tests.filter((test) => test.status === "passed").length,
      failed: report.numFailedTests ?? tests.filter((test) => test.status === "failed").length,
      errors: 0,
      skipped: report.numPendingTests ?? tests.filter((test) => test.status === "skipped").length,
      expected_failures: 0,
      unexpected_successes: 0
    },
    tests
  };
}

function normalizePythonReport(filePath) {
  return safeReadJson(filePath);
}

function summarizeCoverage() {
  const unit = safeReadJson(path.join(root, "unit-coverage-summary.json"));
  const performance = safeReadJson(path.join(root, "performance-summary.json"));
  const security = safeReadJson(path.join(root, "security-summary.json"));
  return { unit, performance, security };
}

function statusForSuite(report) {
  if (!report) {
    return "not_run";
  }
  return report.successful ? "passed" : "failed";
}

function suiteCounts(report) {
  if (!report) {
    return {
      total: 0,
      passed: 0,
      failed: 0,
      errors: 0,
      skipped: 0,
      expected_failures: 0,
      unexpected_successes: 0
    };
  }
  return report.summary;
}

const suites = [
  normalizeVitestReport("ui", path.join(resultsDir, "ui.json")),
  normalizeVitestReport("web", path.join(resultsDir, "web.json")),
  normalizePythonReport(path.join(resultsDir, "api-unit.json")),
  normalizePythonReport(path.join(resultsDir, "functional.json")),
  normalizePythonReport(path.join(resultsDir, "integration.json")),
  normalizePythonReport(path.join(resultsDir, "compliance.json")),
  normalizePythonReport(path.join(resultsDir, "performance.json"))
].filter(Boolean);

const knownSuites = [
  ["ui", normalizeVitestReport("ui", path.join(resultsDir, "ui.json"))],
  ["web", normalizeVitestReport("web", path.join(resultsDir, "web.json"))],
  ["api-unit", normalizePythonReport(path.join(resultsDir, "api-unit.json"))],
  ["functional", normalizePythonReport(path.join(resultsDir, "functional.json"))],
  ["integration", normalizePythonReport(path.join(resultsDir, "integration.json"))],
  ["compliance", normalizePythonReport(path.join(resultsDir, "compliance.json"))],
  ["performance", normalizePythonReport(path.join(resultsDir, "performance.json"))]
];

const totals = knownSuites.reduce(
  (accumulator, [, report]) => {
    const summary = suiteCounts(report);
    accumulator.total += summary.total;
    accumulator.passed += summary.passed;
    accumulator.failed += summary.failed;
    accumulator.errors += summary.errors;
    accumulator.skipped += summary.skipped;
    accumulator.expected_failures += summary.expected_failures;
    accumulator.unexpected_successes += summary.unexpected_successes;
    return accumulator;
  },
  {
    total: 0,
    passed: 0,
    failed: 0,
    errors: 0,
    skipped: 0,
    expected_failures: 0,
    unexpected_successes: 0
  }
);

const coverage = summarizeCoverage();
const failedTests = knownSuites.flatMap(([suiteName, report]) =>
  (report?.tests ?? [])
    .filter((test) => ["failed", "error", "unexpected_success"].includes(test.status))
    .map((test) => ({
      suite: suiteName,
      id: test.id,
      name: test.name,
      status: test.status,
      duration_seconds: test.duration_seconds,
      details: test.details
    }))
);

const slowestTests = knownSuites
  .flatMap(([suiteName, report]) =>
    (report?.tests ?? []).map((test) => ({
      suite: suiteName,
      id: test.id,
      name: test.name,
      status: test.status,
      duration_seconds: typeof test.duration_seconds === "number" ? test.duration_seconds : 0
    }))
  )
  .filter((test) => test.status === "passed" || test.status === "failed" || test.status === "error")
  .sort((left, right) => right.duration_seconds - left.duration_seconds)
  .slice(0, 10);

const aggregate = {
  generated_at: new Date().toISOString(),
  overview: {
    status: failedTests.length === 0 ? "passed" : "failed",
    suites_recorded: knownSuites.filter(([, report]) => Boolean(report)).length,
    totals
  },
  suites: knownSuites.map(([suiteName, report]) => ({
    suite_name: suiteName,
    status: statusForSuite(report),
    duration_seconds: report?.duration_seconds ?? null,
    started_at: report?.started_at ?? null,
    ended_at: report?.ended_at ?? null,
    summary: suiteCounts(report),
    artifact: report ? path.join(resultsDir, `${suiteName}.json`) : null
  })),
  failed_tests: failedTests,
  slowest_tests: slowestTests,
  coverage
};

const markdown = [
  "# Test Suite Results Report",
  "",
  `Generated: ${aggregate.generated_at}`,
  "",
  "## Overview",
  "",
  `- Status: ${aggregate.overview.status}`,
  `- Suites recorded: ${aggregate.overview.suites_recorded}`,
  `- Total tests: ${totals.total}`,
  `- Passed: ${totals.passed}`,
  `- Failed: ${totals.failed}`,
  `- Errors: ${totals.errors}`,
  `- Skipped: ${totals.skipped}`,
  "",
  "## Suite Status",
  "",
  "| Suite | Status | Total | Passed | Failed | Errors | Skipped | Duration (s) |",
  "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
  ...aggregate.suites.map(
    (suite) =>
      `| ${suite.suite_name} | ${suite.status} | ${suite.summary.total} | ${suite.summary.passed} | ${suite.summary.failed} | ${suite.summary.errors} | ${suite.summary.skipped} | ${suite.duration_seconds ?? "n/a"} |`
  ),
  "",
  "## Coverage And Artifacts",
  "",
  `- Unit coverage summary: ${coverage.unit ? JSON.stringify(coverage.unit.combined) : "not available"}`,
  `- Performance summary artifact: ${coverage.performance ? "available" : "not available"}`,
  `- Security summary artifact: ${coverage.security ? "available" : "not available"}`,
  ""
];

if (slowestTests.length > 0) {
  markdown.push("## Slowest Tests", "");
  markdown.push("| Suite | Test | Status | Duration (s) |");
  markdown.push("| --- | --- | --- | ---: |");
  for (const slowTest of slowestTests) {
    markdown.push(`| ${slowTest.suite} | ${slowTest.name} | ${slowTest.status} | ${slowTest.duration_seconds.toFixed(6)} |`);
  }
  markdown.push("");
}

if (failedTests.length > 0) {
  markdown.push("## Failures", "");
  for (const failedTest of failedTests) {
    markdown.push(`### ${failedTest.suite}: ${failedTest.name}`);
    markdown.push("");
    markdown.push(`- Status: ${failedTest.status}`);
    markdown.push(`- Test ID: ${failedTest.id}`);
    markdown.push(`- Duration: ${failedTest.duration_seconds ?? "n/a"}s`);
    if (failedTest.details) {
      markdown.push("");
      markdown.push("```text");
      markdown.push(String(failedTest.details).trim());
      markdown.push("```");
    }
    markdown.push("");
  }
}

const jsonPath = path.join(root, "test-results-report.json");
const mdPath = path.join(root, "test-results-report.md");
fs.mkdirSync(root, { recursive: true });
fs.writeFileSync(jsonPath, `${JSON.stringify(aggregate, null, 2)}\n`);
fs.writeFileSync(mdPath, `${markdown.join("\n")}\n`);

console.log(JSON.stringify(aggregate, null, 2));
