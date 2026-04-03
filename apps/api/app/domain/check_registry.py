"""Extensible check type registry.

Replaces the hard-coded check definitions in policy_check_service with a
registry pattern. The 5 existing checks are registered as built-in handlers.
New check types can be added via ``register()`` without modifying the core.

Usage::

    from app.domain.check_registry import check_registry

    # Register a custom check
    check_registry.register("my_custom_check", my_handler_function)

    # Evaluate a check
    result = check_registry.evaluate("Intake Completeness", context)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


class CheckContext:
    """Context object passed to check handlers for evaluation."""

    def __init__(
        self,
        *,
        request_id: str = "",
        title: str = "",
        summary: str = "",
        template_id: str = "",
        status: str = "",
        priority: str = "",
        policy_context: dict | None = None,
        has_artifact: bool = False,
        artifact_stale_review: bool = False,
        has_review: bool = False,
        review_blocking_status: str = "",
        extra: dict | None = None,
    ) -> None:
        self.request_id = request_id
        self.title = title
        self.summary = summary
        self.template_id = template_id
        self.status = status
        self.priority = priority
        self.policy_context = policy_context or {}
        self.has_artifact = has_artifact
        self.artifact_stale_review = artifact_stale_review
        self.has_review = has_review
        self.review_blocking_status = review_blocking_status
        self.extra = extra or {}


@dataclass(frozen=True)
class CheckResult:
    """Result of evaluating a single check."""

    state: str  # "passed", "failed", "pending"
    detail: str
    evidence: str


class CheckHandlerFn(Protocol):
    """Protocol for check handler callables."""

    def __call__(self, context: CheckContext) -> CheckResult: ...


# ---------------------------------------------------------------------------
# Built-in check handlers (matching the 5 existing hard-coded checks)
# ---------------------------------------------------------------------------

def _intake_completeness(ctx: CheckContext) -> CheckResult:
    fields = {
        "title": bool(ctx.title and ctx.title.strip()),
        "summary": bool(ctx.summary and ctx.summary.strip()),
        "template_id": bool(ctx.template_id and ctx.template_id.strip()),
    }
    passed = all(fields.values())
    return CheckResult(
        state="passed" if passed else "failed",
        detail="All canonical intake fields are populated." if passed else "Title, summary, and template binding are required.",
        evidence=str(fields),
    )


def _review_package_readiness(ctx: CheckContext) -> CheckResult:
    passed = ctx.has_artifact and ctx.has_review
    return CheckResult(
        state="passed" if passed else "pending",
        detail="Artifact and review routing are ready." if passed else "Artifact generation and reviewer routing must complete.",
        evidence=f"artifact={'present' if ctx.has_artifact else 'missing'}, review={'present' if ctx.has_review else 'missing'}",
    )


def _approval_freshness(ctx: CheckContext) -> CheckResult:
    passed = ctx.has_artifact and not ctx.artifact_stale_review and (not ctx.has_review or ctx.review_blocking_status == "Approved")
    return CheckResult(
        state="passed" if passed else "pending",
        detail="Latest approval evidence is fresh." if passed else "A fresh approved review is required before promotion.",
        evidence=f"artifact_stale={ctx.artifact_stale_review}, review={ctx.review_blocking_status or 'missing'}",
    )


def _policy_bundle(ctx: CheckContext) -> CheckResult:
    passed = ctx.policy_context.get("policy_bundle_passed", True) is not False
    return CheckResult(
        state="passed" if passed else "failed",
        detail="Automated policy bundle evaluation passed." if passed else "Automated policy bundle evaluation failed.",
        evidence=f"policy_context={ctx.policy_context}",
    )


def _promotion_approval_freshness(ctx: CheckContext) -> CheckResult:
    fresh = ctx.has_artifact and not ctx.artifact_stale_review and (not ctx.has_review or ctx.review_blocking_status == "Approved")
    return CheckResult(
        state="passed" if fresh else "pending",
        detail="Latest approved artifact is fresh." if fresh else "Waiting for fresh approval evidence.",
        evidence=f"artifact_stale={ctx.artifact_stale_review}, review_state={ctx.review_blocking_status or 'missing'}",
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class CheckRegistry:
    """Registry of named check handlers.

    Check handlers are callables that accept a ``CheckContext`` and return
    a ``CheckResult``. Built-in handlers are registered at construction time.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, CheckHandlerFn] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self.register("Intake Completeness", _intake_completeness)
        self.register("Review Package Readiness", _review_package_readiness)
        self.register("Approval Freshness", _approval_freshness)
        self.register("Policy Bundle", _policy_bundle)
        self.register("Promotion Approval Freshness", _promotion_approval_freshness)

    def register(self, name: str, handler: CheckHandlerFn) -> None:
        """Register a check handler under *name*."""
        self._handlers[name] = handler

    def unregister(self, name: str) -> None:
        """Remove a handler. Raises KeyError if not found."""
        del self._handlers[name]

    def has(self, name: str) -> bool:
        """Return True if a handler is registered for *name*."""
        return name in self._handlers

    def list_names(self) -> list[str]:
        """Return all registered check names."""
        return sorted(self._handlers.keys())

    def evaluate(self, name: str, context: CheckContext) -> CheckResult:
        """Evaluate the named check against *context*.

        Raises ``KeyError`` if no handler is registered for *name*.
        """
        handler = self._handlers.get(name)
        if handler is None:
            raise KeyError(f"No check handler registered for '{name}'")
        return handler(context)

    def evaluate_all(self, names: list[str], context: CheckContext) -> dict[str, CheckResult]:
        """Evaluate multiple checks, returning a name→result mapping."""
        return {name: self.evaluate(name, context) for name in names if self.has(name)}


# Module-level singleton
check_registry = CheckRegistry()
