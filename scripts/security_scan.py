import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Volumes/data/development/rgp")
COVERAGE = ROOT / "coverage"
COVERAGE.mkdir(parents=True, exist_ok=True)
SELF_FILE = ROOT / "scripts" / "security_scan.py"
IGNORED_PIP_AUDIT_PACKAGES = {"pip"}

CRYPTO_PATTERNS = {
    "python-md5": re.compile(r"hashlib\.md5\s*\("),
    "python-sha1": re.compile(r"hashlib\.sha1\s*\("),
    "python-weak-cipher": re.compile(r"(algorithms|Crypto\.Cipher)\.(DES|TripleDES|ARC4|Blowfish)\b"),
    "python-ecb": re.compile(r"modes\.ECB\b"),
    "python-unverified-ssl": re.compile(r"ssl\._create_unverified_context\s*\("),
    "js-md5": re.compile(r"createHash\s*\(\s*['\"]md5['\"]"),
    "js-sha1": re.compile(r"createHash\s*\(\s*['\"]sha1['\"]"),
    "js-weak-cipher": re.compile(r"createCipher(iv)?\s*\("),
    "js-ecb": re.compile(r"\bECB\b"),
    "js-sha1-subtle": re.compile(r"subtle\.digest\s*\(\s*['\"]SHA-1['\"]"),
}

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "coverage",
    ".venv",
    "__pycache__",
    "dist",
    "build",
}


def run_command(command: list[str], *, cwd: Path | None = None, capture_json_file: Path | None = None, allow_nonzero: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd or ROOT),
        text=True,
        capture_output=True,
    )
    if capture_json_file is not None and result.stdout.strip():
        capture_json_file.write_text(result.stdout, encoding="utf-8")
    if not allow_nonzero and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    return result


def crypto_review() -> dict:
    findings: list[dict] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
            continue
        if path == SELF_FILE:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for rule_name, pattern in CRYPTO_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(
                    {
                        "rule": rule_name,
                        "file": str(path),
                        "line": line,
                        "match": match.group(0),
                    }
                )
    report = {
        "findings": findings,
        "summary": {
            "total_findings": len(findings),
        },
    }
    (COVERAGE / "crypto-review.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def parse_pnpm_audit(stdout: str) -> dict:
    advisories: list[dict] = []
    counts = {"info": 0, "low": 0, "moderate": 0, "high": 0, "critical": 0}
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        data = payload.get("data") or {}
        advisory = data.get("advisory") or data.get("vulnerability")
        if advisory:
            severity = advisory.get("severity", "unknown")
            if severity in counts:
                counts[severity] += 1
            advisories.append(advisory)
        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            severities = metadata.get("vulnerabilities")
            if isinstance(severities, dict):
                for key in counts:
                    counts[key] = max(counts[key], int(severities.get(key, 0)))
    report = {"summary": counts, "advisories": advisories}
    (COVERAGE / "pnpm-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    reports: dict[str, object] = {}

    bandit_file = COVERAGE / "bandit.json"
    bandit = run_command(
        ["python", "-m", "bandit", "-r", "apps/api/app", "-f", "json"],
        allow_nonzero=True,
    )
    bandit_file.write_text(bandit.stdout or bandit.stderr, encoding="utf-8")
    reports["bandit"] = json.loads(bandit.stdout or "{\"results\": []}")

    pip_audit_file = COVERAGE / "pip-audit.json"
    pip_audit = run_command(
        ["python", "-m", "pip_audit", "-f", "json"],
        allow_nonzero=True,
    )
    pip_audit_file.write_text(pip_audit.stdout or pip_audit.stderr, encoding="utf-8")
    reports["pip_audit"] = json.loads(pip_audit.stdout or "[]")

    pnpm_audit = run_command(
        ["pnpm", "audit", "--json", "--audit-level", "high"],
        allow_nonzero=True,
    )
    reports["pnpm_audit"] = parse_pnpm_audit(pnpm_audit.stdout)

    reports["crypto_review"] = crypto_review()

    summary = {
        "bandit_findings": len((reports["bandit"] or {}).get("results", [])),
        "pip_audit_vulnerabilities": sum(
            len(item.get("vulns") or [])
            for item in (reports["pip_audit"] or {}).get("dependencies", [])
            if item.get("name") not in IGNORED_PIP_AUDIT_PACKAGES
        ),
        "pnpm_high_or_critical": int((reports["pnpm_audit"] or {}).get("summary", {}).get("high", 0))
        + int((reports["pnpm_audit"] or {}).get("summary", {}).get("critical", 0)),
        "crypto_findings": int((reports["crypto_review"] or {}).get("summary", {}).get("total_findings", 0)),
    }
    (COVERAGE / "security-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    has_failures = any(summary.values())
    if has_failures:
        print(json.dumps(summary, indent=2))
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
