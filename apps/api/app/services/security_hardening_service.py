"""Security hardening service -- prompt sanitization, context boundaries, and execution limits."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.services.event_store_service import event_store_service


# ---------------------------------------------------------------------------
# Injection patterns to strip from user-supplied prompts
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?prior\s+(instructions|context)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\s*/?system\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"\[/INST\]", re.IGNORECASE),
    re.compile(r"<<\s*SYS\s*>>", re.IGNORECASE),
    re.compile(r"<<\s*/SYS\s*>>", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|im_end\|>", re.IGNORECASE),
    re.compile(r"<\|endoftext\|>", re.IGNORECASE),
    re.compile(r"\\x[0-9a-fA-F]{2}", re.IGNORECASE),
]

# Default execution limits per tenant tier
_DEFAULT_LIMITS: dict[str, dict] = {
    "free": {
        "max_prompt_length": 4_000,
        "max_context_tokens": 8_000,
        "max_concurrent_sessions": 2,
        "max_requests_per_hour": 20,
    },
    "standard": {
        "max_prompt_length": 16_000,
        "max_context_tokens": 32_000,
        "max_concurrent_sessions": 10,
        "max_requests_per_hour": 200,
    },
    "enterprise": {
        "max_prompt_length": 64_000,
        "max_context_tokens": 128_000,
        "max_concurrent_sessions": 50,
        "max_requests_per_hour": 2_000,
    },
}

_BOUNDARY_START = "--- BEGIN USER INPUT ---"
_BOUNDARY_END = "--- END USER INPUT ---"


class SecurityHardeningService:
    """Prompt sanitization, context boundary enforcement, and execution limit checks."""

    # ------------------------------------------------------------------
    # Prompt sanitization
    # ------------------------------------------------------------------

    def sanitize_prompt_input(self, text: str) -> str:
        """Strip known injection patterns from user-supplied prompt text.

        Returns the sanitized string with injection patterns removed and
        leading/trailing whitespace collapsed.
        """
        sanitized = text
        for pattern in _INJECTION_PATTERNS:
            sanitized = pattern.sub("", sanitized)

        # Collapse excessive whitespace introduced by removals
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)
        sanitized = re.sub(r"  +", " ", sanitized)
        return sanitized.strip()

    # ------------------------------------------------------------------
    # Context boundary enforcement
    # ------------------------------------------------------------------

    def validate_context_boundaries(
        self, system_context: str, user_input: str
    ) -> str:
        """Add boundary markers between system context and user input.

        Returns the combined string with clear delimiters so that
        downstream LLM prompts maintain context separation.
        """
        sanitized_input = self.sanitize_prompt_input(user_input)
        return (
            f"{system_context}\n\n"
            f"{_BOUNDARY_START}\n"
            f"{sanitized_input}\n"
            f"{_BOUNDARY_END}"
        )

    # ------------------------------------------------------------------
    # Execution limits
    # ------------------------------------------------------------------

    def check_execution_limits(self, tenant_id: str) -> dict:
        """Return the resource limit configuration for the given tenant.

        Looks up the tenant's tier from the database and returns the
        corresponding limits. Falls back to 'standard' tier if the
        tenant is not found.
        """
        from app.db.models import TenantTable

        with SessionLocal() as session:
            tenant = (
                session.query(TenantTable)
                .filter(TenantTable.id == tenant_id)
                .first()
            )

            # Determine tier from tenant status or a future tier column.
            # For now, map status to a tier heuristic.
            if tenant is None:
                tier = "standard"
            elif tenant.status == "enterprise":
                tier = "enterprise"
            elif tenant.status == "free" or tenant.status == "trial":
                tier = "free"
            else:
                tier = "standard"

        limits = _DEFAULT_LIMITS.get(tier, _DEFAULT_LIMITS["standard"]).copy()
        limits["tenant_id"] = tenant_id
        limits["tier"] = tier
        return limits

    # ------------------------------------------------------------------
    # Security audit logging
    # ------------------------------------------------------------------

    def audit_security_event(
        self,
        event_type: str,
        detail: str,
        actor_id: str,
        tenant_id: str,
    ) -> None:
        """Log a security event via the event store."""
        with SessionLocal() as session:
            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type=f"security.{event_type}",
                aggregate_type="security",
                aggregate_id=tenant_id,
                actor=actor_id,
                detail=detail,
            )
            session.commit()


security_hardening_service = SecurityHardeningService()
