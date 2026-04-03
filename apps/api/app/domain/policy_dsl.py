"""Pure policy DSL — condition evaluation and action resolution.

Policy rules are JSON-serializable dicts. This module evaluates conditions
against a context dict and resolves actions. No database or I/O dependencies.

Condition structure::

    {"field": "priority", "op": "eq", "value": "urgent"}
    {"op": "and", "conditions": [cond1, cond2]}
    {"op": "or", "conditions": [cond1, cond2]}
    {"op": "not", "condition": cond}
    {"field": "tags", "op": "contains", "value": "security"}
    {"field": "status", "op": "in", "value": ["awaiting_review", "under_review"]}
    {"field": "sla_risk_level", "op": "not_null"}
    {"field": "priority", "op": "ne", "value": "low"}
    {"field": "age_hours", "op": "gte", "value": 24}

Action structure::

    {"type": "route", "target_team": "team_security"}
    {"type": "block", "reason": "Security review required"}
    {"type": "escalate", "to": "team_ops", "reason": "SLA breach"}
    {"type": "require_review", "reviewer": "security_lead"}
    {"type": "branch", "workflow": "wf_expedited"}
    {"type": "remediate", "action": "notify_owner"}
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------

def evaluate_condition(condition: dict, context: dict) -> bool:
    """Evaluate a policy condition against a context dict.

    Returns True if the condition is satisfied.
    """
    if not isinstance(condition, dict):
        return False

    op = condition.get("op", "eq")

    # Logical combinators
    if op == "and":
        return all(evaluate_condition(c, context) for c in condition.get("conditions", []))
    if op == "or":
        return any(evaluate_condition(c, context) for c in condition.get("conditions", []))
    if op == "not":
        inner = condition.get("condition", {})
        return not evaluate_condition(inner, context)
    if op == "always":
        return True
    if op == "never":
        return False

    # Field-level operators
    field = condition.get("field")
    if field is None:
        return False

    actual = _resolve_field(context, field)
    expected = condition.get("value")

    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return actual in (expected if isinstance(expected, (list, set, tuple)) else [])
    if op == "not_in":
        return actual not in (expected if isinstance(expected, (list, set, tuple)) else [])
    if op == "contains":
        if isinstance(actual, (list, set, tuple)):
            return expected in actual
        if isinstance(actual, str):
            return str(expected) in actual
        return False
    if op == "not_null":
        return actual is not None
    if op == "is_null":
        return actual is None
    if op == "gt":
        return _compare(actual, expected) > 0
    if op == "gte":
        return _compare(actual, expected) >= 0
    if op == "lt":
        return _compare(actual, expected) < 0
    if op == "lte":
        return _compare(actual, expected) <= 0
    if op == "matches":
        import re
        return bool(re.fullmatch(str(expected), str(actual or "")))

    return False


def _resolve_field(context: dict, field: str) -> Any:
    """Resolve a dotted field path from a context dict.

    Supports ``"foo.bar.baz"`` for nested access.
    """
    parts = field.split(".")
    current: Any = context
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _compare(a: Any, b: Any) -> int:
    """Compare two values, coercing to float if possible."""
    try:
        fa, fb = float(a), float(b)
        return (fa > fb) - (fa < fb)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# Action types
# ---------------------------------------------------------------------------

VALID_ACTION_TYPES = frozenset({
    "route",
    "block",
    "escalate",
    "require_review",
    "branch",
    "remediate",
    "notify",
    "add_tag",
    "set_field",
})


def validate_action(action: dict) -> list[str]:
    """Validate a policy action dict. Returns a list of error messages (empty if valid)."""
    errors: list[str] = []
    if not isinstance(action, dict):
        return ["Action must be a dict"]
    action_type = action.get("type")
    if action_type not in VALID_ACTION_TYPES:
        errors.append(f"Unknown action type: {action_type}")
    if action_type == "block" and not action.get("reason"):
        errors.append("Block action requires a reason")
    if action_type == "route" and not action.get("target_team"):
        errors.append("Route action requires target_team")
    if action_type == "escalate" and not action.get("to"):
        errors.append("Escalate action requires 'to' field")
    if action_type == "require_review" and not action.get("reviewer"):
        errors.append("Require_review action requires 'reviewer' field")
    if action_type == "branch" and not action.get("workflow"):
        errors.append("Branch action requires 'workflow' field")
    return errors


# ---------------------------------------------------------------------------
# Rule evaluation
# ---------------------------------------------------------------------------

def evaluate_rule(rule: dict, context: dict) -> list[dict]:
    """Evaluate a single policy rule against a context.

    Returns the list of actions to execute (empty if condition not met or
    rule is inactive).
    """
    if not rule.get("active", True):
        return []
    condition = rule.get("condition", {})
    if not evaluate_condition(condition, context):
        return []
    return rule.get("actions", [])


def evaluate_rules(rules: list[dict], context: dict) -> list[dict]:
    """Evaluate an ordered list of policy rules against a context.

    Rules are evaluated in priority order. All matching rules' actions are
    collected. Returns the aggregated action list.
    """
    sorted_rules = sorted(rules, key=lambda r: r.get("priority", 0))
    actions: list[dict] = []
    for rule in sorted_rules:
        actions.extend(evaluate_rule(rule, context))
    return actions


def has_blocking_action(actions: list[dict]) -> bool:
    """Return True if any action in the list is a block action."""
    return any(a.get("type") == "block" for a in actions)


def get_actions_by_type(actions: list[dict], action_type: str) -> list[dict]:
    """Filter actions by type."""
    return [a for a in actions if a.get("type") == action_type]
