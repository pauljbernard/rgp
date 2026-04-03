import fs from "node:fs";

const root = "/Volumes/data/development/rgp/coverage";

function readJson(path) {
  return JSON.parse(fs.readFileSync(path, "utf8"));
}

function getVitestLines(summaryPath) {
  const summary = readJson(summaryPath);
  const total = summary.total?.lines;
  if (!total) {
    throw new Error(`Missing line totals in ${summaryPath}`);
  }
  return {
    covered: total.covered,
    total: total.total,
    pct: total.pct
  };
}

function getPythonLines(summaryPath) {
  const summary = readJson(summaryPath);
  return {
    covered: summary.totals.covered_lines,
    total: summary.totals.num_statements,
    pct: summary.totals.percent_covered
  };
}

const ui = getVitestLines(`${root}/ui/coverage-summary.json`);
const web = getVitestLines(`${root}/web/coverage-summary.json`);
const api = getPythonLines(`${root}/api-unit-coverage.json`);

const combinedCovered = ui.covered + web.covered + api.covered;
const combinedTotal = ui.total + web.total + api.total;
const combinedPct = combinedTotal === 0 ? 0 : (combinedCovered / combinedTotal) * 100;

const report = {
  ui,
  web,
  api,
  combined: {
    covered: combinedCovered,
    total: combinedTotal,
    pct: Number(combinedPct.toFixed(2))
  }
};

fs.writeFileSync(`${root}/unit-coverage-summary.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
