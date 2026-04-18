import json
import os
import subprocess
import tempfile
from urllib import error, request
from pathlib import Path

from app.core.config import settings
from app.db.models import IntegrationTable
from app.services.integration_security_service import integration_security_service


class RuntimeDispatchService:
    @staticmethod
    def _safe_ref(value: str | None, fallback: str) -> str:
        candidate = (value or fallback).strip()
        return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in candidate) or fallback

    @staticmethod
    def _sbcl_agent_cli_path() -> str:
        return settings.sbcl_agent_runtime_cli_path

    @staticmethod
    def _sbcl_agent_state_root() -> Path:
        root = Path(settings.sbcl_agent_runtime_state_root)
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _sbcl_agent_environment_path(self, payload: dict) -> Path:
        binding = payload.get("binding") or {}
        reference = binding.get("agent_session_id") or payload.get("run_id") or payload.get("request_id") or "runtime"
        safe_ref = self._safe_ref(str(reference), "runtime")
        return self._sbcl_agent_state_root() / f"{safe_ref}.sexp"

    def sbcl_agent_environment_ref(self, request_id: str, agent_session_id: str) -> str:
        return str(
            self._sbcl_agent_environment_path(
                {
                    "request_id": request_id,
                    "binding": {"agent_session_id": agent_session_id},
                }
            )
        )

    @staticmethod
    def _parse_json_output(stdout: str) -> dict:
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        if not lines:
            return {}
        return json.loads(lines[-1])

    def _run_sbcl_agent_command(self, arguments: list[str]) -> dict:
        command = [self._sbcl_agent_cli_path(), "rgp", *arguments]
        cache_root = self._sbcl_agent_state_root() / "cache"
        cache_root.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["XDG_CACHE_HOME"] = str(cache_root)
        try:
            completed = subprocess.run(  # noqa: S603
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                env=env,
            )
        except FileNotFoundError as exc:
            raise ValueError(f"sbcl-agent runtime CLI unavailable: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit={completed.returncode}"
            raise ValueError(f"sbcl-agent runtime command failed: {detail}")
        return self._parse_json_output(completed.stdout)

    @staticmethod
    def resolve_endpoint(integration: IntegrationTable) -> str:
        if integration.endpoint.startswith("http://") or integration.endpoint.startswith("https://"):
            return integration_security_service.validate_outbound_target(
                integration.endpoint,
                allowed_hosts=settings.integration_runtime_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )
        if integration.endpoint.startswith("foundry://"):
            configured_base_url = integration_security_service.setting(integration, "base_url")
            base_url = integration_security_service.normalize_runtime_mock_base_url(
                configured_base_url,
                fallback_url=settings.runtime_adapter_base_url,
            )
            base_url = integration_security_service.validate_outbound_target(
                base_url,
                allowed_hosts=settings.integration_runtime_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )
            return f"{base_url}/runs/foundry"
        if integration.endpoint.startswith("sbcl://"):
            return integration.endpoint
        raise ValueError(f"Unsupported runtime integration endpoint: {integration.endpoint}")

    def _dispatch_sbcl_agent(self, integration: IntegrationTable, payload: dict) -> dict:
        environment_path = self._sbcl_agent_environment_path(payload)
        binding = payload.get("binding") or {}
        command = [
            "bind",
            "--environment",
            str(environment_path),
            "--request-id",
            str(binding.get("request_id") or payload.get("request_id") or ""),
            "--agent-session-id",
            str(binding.get("agent_session_id") or payload.get("run_id") or payload.get("request_id") or "runtime"),
        ]
        for option, value in (
            ("--tenant-id", binding.get("tenant_id")),
            ("--integration-id", binding.get("integration_id") or getattr(integration, "id", None)),
            ("--projection-id", binding.get("projection_id")),
            ("--cwd", (integration.settings or {}).get("working_directory")),
        ):
            if value:
                command.extend([option, str(value)])
        result = self._run_sbcl_agent_command(command)
        return {
            "status": result.get("status", "accepted"),
            "external_reference": str(environment_path),
            "summary": "sbcl-agent governed runtime binding established",
            "binding": result.get("binding") or {},
            "governed_runtime": result.get("governed_runtime") or {},
        }

    def dispatch(self, integration: IntegrationTable, payload: dict) -> dict:
        url = self.resolve_endpoint(integration)
        if url.startswith("sbcl://"):
            return self._dispatch_sbcl_agent(integration, payload)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=10) as response:  # nosec B310 - URL is validated by resolve_endpoint()
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"Runtime dispatch rejected: {detail or exc.reason}") from exc
        except error.URLError as exc:
            raise ValueError(f"Runtime dispatch unavailable: {exc.reason}") from exc

    def export_sbcl_agent_snapshot(self, environment_ref: str) -> dict:
        with tempfile.NamedTemporaryFile(prefix="rgp-sbcl-agent-", suffix=".json", delete=False) as handle:
            output_path = handle.name
        result = self._run_sbcl_agent_command(
            ["export", "--environment", environment_ref, "--output", output_path]
        )
        snapshot = result.get("snapshot")
        if isinstance(snapshot, dict):
            return snapshot
        return json.loads(Path(output_path).read_text(encoding="utf-8"))

    def list_sbcl_agent_artifacts(self, environment_ref: str) -> list[dict]:
        result = self._run_sbcl_agent_command(["artifacts", "--environment", environment_ref])
        return result if isinstance(result, list) else list(result.get("artifacts") or [])

    def list_sbcl_agent_approvals(self, environment_ref: str) -> list[dict]:
        result = self._run_sbcl_agent_command(["approvals", "--environment", environment_ref])
        return result if isinstance(result, list) else list(result.get("approvals") or [])

    def resume_sbcl_agent_session(self, environment_ref: str, work_item_id: str, *, note: str | None = None) -> dict:
        command = ["resume", "--environment", environment_ref, "--work-item-id", work_item_id]
        if note:
            command.extend(["--note", note])
        return self._run_sbcl_agent_command(command)

    def approve_sbcl_agent_checkpoint(
        self,
        environment_ref: str,
        work_item_id: str,
        *,
        policy: str = "process-run",
        reason: str | None = None,
    ) -> dict:
        command = [
            "approve",
            "--environment",
            environment_ref,
            "--work-item-id",
            work_item_id,
            "--policy",
            policy,
        ]
        if reason:
            command.extend(["--reason", reason])
        return self._run_sbcl_agent_command(command)


runtime_dispatch_service = RuntimeDispatchService()
