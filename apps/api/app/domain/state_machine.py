"""Pure state-machine logic for request lifecycle governance.

All functions and constants in this module are free of database or I/O
dependencies. They operate on plain values and can be tested in isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.request import RequestPriority, RequestStatus


# ---------------------------------------------------------------------------
# Transition rules
# ---------------------------------------------------------------------------

TRANSITION_RULES: dict[RequestStatus, set[RequestStatus]] = {
    RequestStatus.SUBMITTED: {RequestStatus.VALIDATED, RequestStatus.VALIDATION_FAILED, RequestStatus.CANCELED},
    RequestStatus.VALIDATION_FAILED: {RequestStatus.DRAFT, RequestStatus.CANCELED},
    RequestStatus.VALIDATED: {RequestStatus.CLASSIFIED, RequestStatus.CANCELED},
    RequestStatus.CLASSIFIED: {RequestStatus.OWNERSHIP_RESOLVED, RequestStatus.CANCELED},
    RequestStatus.OWNERSHIP_RESOLVED: {RequestStatus.PLANNED, RequestStatus.CANCELED},
    RequestStatus.PLANNED: {RequestStatus.QUEUED, RequestStatus.CANCELED},
    RequestStatus.QUEUED: {RequestStatus.IN_EXECUTION, RequestStatus.FAILED, RequestStatus.CANCELED},
    RequestStatus.IN_EXECUTION: {RequestStatus.AWAITING_INPUT, RequestStatus.AWAITING_REVIEW, RequestStatus.FAILED, RequestStatus.CANCELED},
    RequestStatus.AWAITING_INPUT: {RequestStatus.DRAFT, RequestStatus.CANCELED},
    RequestStatus.AWAITING_REVIEW: {RequestStatus.UNDER_REVIEW, RequestStatus.CHANGES_REQUESTED, RequestStatus.APPROVED, RequestStatus.CANCELED},
    RequestStatus.UNDER_REVIEW: {RequestStatus.CHANGES_REQUESTED, RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELED},
    RequestStatus.CHANGES_REQUESTED: {RequestStatus.DRAFT, RequestStatus.CANCELED},
    RequestStatus.APPROVED: {RequestStatus.PROMOTION_PENDING, RequestStatus.COMPLETED, RequestStatus.CANCELED},
    RequestStatus.PROMOTION_PENDING: {RequestStatus.PROMOTED, RequestStatus.FAILED, RequestStatus.CANCELED},
    RequestStatus.PROMOTED: {RequestStatus.COMPLETED},
    RequestStatus.FAILED: {RequestStatus.PLANNED, RequestStatus.CANCELED},
}

SUBMITTABLE_STATUSES: set[RequestStatus] = {
    RequestStatus.DRAFT,
    RequestStatus.CHANGES_REQUESTED,
    RequestStatus.VALIDATION_FAILED,
    RequestStatus.AWAITING_INPUT,
}

AMENDABLE_STATUSES: set[RequestStatus] = {
    RequestStatus.DRAFT,
    RequestStatus.SUBMITTED,
    RequestStatus.VALIDATION_FAILED,
    RequestStatus.VALIDATED,
    RequestStatus.CLASSIFIED,
    RequestStatus.OWNERSHIP_RESOLVED,
    RequestStatus.PLANNED,
    RequestStatus.QUEUED,
    RequestStatus.AWAITING_INPUT,
    RequestStatus.AWAITING_REVIEW,
    RequestStatus.UNDER_REVIEW,
    RequestStatus.CHANGES_REQUESTED,
    RequestStatus.APPROVED,
    RequestStatus.PROMOTION_PENDING,
    RequestStatus.FAILED,
}

CANCELABLE_STATUSES: set[RequestStatus] = {
    RequestStatus.DRAFT,
    RequestStatus.SUBMITTED,
    RequestStatus.VALIDATION_FAILED,
    RequestStatus.VALIDATED,
    RequestStatus.CLASSIFIED,
    RequestStatus.OWNERSHIP_RESOLVED,
    RequestStatus.PLANNED,
    RequestStatus.QUEUED,
    RequestStatus.IN_EXECUTION,
    RequestStatus.AWAITING_INPUT,
    RequestStatus.AWAITING_REVIEW,
    RequestStatus.UNDER_REVIEW,
    RequestStatus.CHANGES_REQUESTED,
    RequestStatus.APPROVED,
    RequestStatus.PROMOTION_PENDING,
    RequestStatus.FAILED,
}


# ---------------------------------------------------------------------------
# SLA policy rules
# ---------------------------------------------------------------------------

SLA_POLICY_RULES: dict[str, dict[str, dict[str, int]]] = {
    "sla_standard_v1": {
        "review_hours": {"medium": 4, "high": 2, "urgent": 1},
        "promotion_hours": {"medium": 6, "high": 4, "urgent": 2},
        "execution_hours": {"medium": 8, "high": 6, "urgent": 3},
    }
}


# ---------------------------------------------------------------------------
# Pure query helpers
# ---------------------------------------------------------------------------

def is_valid_transition(current: RequestStatus, target: RequestStatus) -> bool:
    """Return True if *current* → *target* is an allowed lifecycle transition."""
    return target in TRANSITION_RULES.get(current, set())


def allowed_transitions(current: RequestStatus) -> set[RequestStatus]:
    """Return the set of statuses reachable from *current*."""
    return TRANSITION_RULES.get(current, set())


def assert_submittable(current: RequestStatus) -> None:
    """Raise ``ValueError`` if the request cannot be submitted from *current*."""
    if current not in SUBMITTABLE_STATUSES:
        raise ValueError(f"Request in status {current} cannot be submitted")


def assert_amendable(current: RequestStatus) -> None:
    """Raise ``ValueError`` if the request cannot be amended from *current*."""
    if current not in AMENDABLE_STATUSES:
        raise ValueError(f"Request in status {current} cannot be amended")


def assert_cancelable(current: RequestStatus) -> None:
    """Raise ``ValueError`` if the request cannot be canceled from *current*."""
    if current not in CANCELABLE_STATUSES:
        raise ValueError(f"Request in status {current} cannot be canceled")


def assert_valid_transition(current: RequestStatus, target: RequestStatus) -> None:
    """Raise ``ValueError`` if *current* → *target* is not allowed."""
    if not is_valid_transition(current, target):
        raise ValueError(
            f"Transition from {current} to {target} is not allowed"
        )


# ---------------------------------------------------------------------------
# SLA risk computation (pure — no DB row dependency)
# ---------------------------------------------------------------------------

def compute_sla_risk(
    status: str,
    priority: str,
    sla_policy_id: str | None,
    updated_at: datetime,
) -> tuple[str | None, str | None]:
    """Compute SLA risk level and reason from plain values.

    Returns ``(level, reason)`` or ``(None, None)`` if within SLA.
    """
    policy_id = sla_policy_id or "sla_standard_v1"
    policy = SLA_POLICY_RULES.get(policy_id, SLA_POLICY_RULES["sla_standard_v1"])
    age_hours = max((datetime.now(timezone.utc) - updated_at).total_seconds() / 3600, 0)
    norm_priority = priority if priority in {"medium", "high", "urgent"} else "medium"

    if status == RequestStatus.FAILED.value:
        return "critical", "Execution failure"
    if priority == RequestPriority.URGENT.value:
        if age_hours >= 2:
            return "critical", "Urgent request exceeded rapid-response threshold"
        return "high", "Urgent priority under active SLA watch"
    if status in {
        RequestStatus.AWAITING_REVIEW.value,
        RequestStatus.UNDER_REVIEW.value,
        RequestStatus.CHANGES_REQUESTED.value,
    }:
        threshold = policy["review_hours"][norm_priority]
        if age_hours >= threshold:
            return "high", "Review delay"
    if status == RequestStatus.PROMOTION_PENDING.value:
        threshold = policy["promotion_hours"][norm_priority]
        if age_hours >= threshold:
            return "high", "Promotion delay"
    if status in {
        RequestStatus.QUEUED.value,
        RequestStatus.IN_EXECUTION.value,
        RequestStatus.AWAITING_INPUT.value,
    }:
        threshold = policy["execution_hours"][norm_priority]
        if age_hours >= threshold:
            return "medium", "Execution delay"
    return None, None
