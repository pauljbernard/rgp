"""MCP tool access control — pure policy-based filtering.

Filters the set of available MCP tools based on collaboration mode,
caller role, and tenant policy rules. This module is a pure function
with no database or I/O dependencies.
"""

from __future__ import annotations


def filter_tools_by_policy(
    tools: list[dict],
    collaboration_mode: str,
    role: str,
    policy_rules: list[dict],
) -> list[dict]:
    """Filter MCP tools according to policy constraints.

    Args:
        tools: List of tool descriptor dicts (each has ``name``,
            ``description``, ``input_schema``).
        collaboration_mode: Current collaboration mode for the session
            (e.g. ``"human_led"``, ``"agent_assisted"``, ``"agent_led"``).
        role: The caller's role identifier.
        policy_rules: List of policy rule dicts.  Each may contain an
            ``actions`` list with entries of type ``"restrict_tool"``
            that carry a ``tool_name`` field.

    Returns:
        The filtered list of tool dicts that the caller is permitted to
        use in the current policy context.
    """
    # Collect explicitly denied tool names from policy rules.
    denied_tools: set[str] = set()
    for rule in policy_rules:
        for action in rule.get("actions", []):
            if action.get("type") == "restrict_tool":
                tool_name = action.get("tool_name")
                # Optionally scope restriction to a mode or role.
                restrict_mode = action.get("collaboration_mode")
                restrict_role = action.get("role")
                mode_match = restrict_mode is None or restrict_mode == collaboration_mode
                role_match = restrict_role is None or restrict_role == role
                if tool_name and mode_match and role_match:
                    denied_tools.add(tool_name)

    # Apply mode-level defaults: in human_led mode, tools that declare
    # ``requires_agent`` are excluded unless the role is an agent.
    filtered: list[dict] = []
    for tool in tools:
        name = tool.get("name", "")

        if name in denied_tools:
            continue

        # Mode gate: tools may declare a minimum collaboration mode.
        required_mode = tool.get("required_collaboration_mode")
        if required_mode and not _mode_satisfies(collaboration_mode, required_mode):
            continue

        # Role gate: tools may declare allowed roles.
        allowed_roles = tool.get("allowed_roles")
        if allowed_roles and role not in allowed_roles:
            continue

        filtered.append(tool)

    return filtered


# Collaboration mode ordering for minimum-mode checks.
_MODE_ORDER = {
    "human_led": 0,
    "agent_assisted": 1,
    "agent_led": 2,
}


def _mode_satisfies(current_mode: str, required_mode: str) -> bool:
    """Return True if *current_mode* meets or exceeds *required_mode*."""
    return _MODE_ORDER.get(current_mode, 0) >= _MODE_ORDER.get(required_mode, 0)
