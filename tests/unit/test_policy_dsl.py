"""Unit tests for the policy DSL module."""

import unittest

from app.domain.policy_dsl import (
    VALID_ACTION_TYPES,
    evaluate_condition,
    evaluate_rule,
    evaluate_rules,
    get_actions_by_type,
    has_blocking_action,
    validate_action,
)


class EvaluateConditionTest(unittest.TestCase):
    CTX = {"priority": "urgent", "status": "awaiting_review", "tags": ["security", "compliance"], "age_hours": 5}

    def test_eq(self) -> None:
        self.assertTrue(evaluate_condition({"field": "priority", "op": "eq", "value": "urgent"}, self.CTX))
        self.assertFalse(evaluate_condition({"field": "priority", "op": "eq", "value": "low"}, self.CTX))

    def test_ne(self) -> None:
        self.assertTrue(evaluate_condition({"field": "priority", "op": "ne", "value": "low"}, self.CTX))

    def test_in(self) -> None:
        self.assertTrue(evaluate_condition({"field": "status", "op": "in", "value": ["awaiting_review", "under_review"]}, self.CTX))
        self.assertFalse(evaluate_condition({"field": "status", "op": "in", "value": ["draft"]}, self.CTX))

    def test_not_in(self) -> None:
        self.assertTrue(evaluate_condition({"field": "status", "op": "not_in", "value": ["draft"]}, self.CTX))

    def test_contains(self) -> None:
        self.assertTrue(evaluate_condition({"field": "tags", "op": "contains", "value": "security"}, self.CTX))
        self.assertFalse(evaluate_condition({"field": "tags", "op": "contains", "value": "finance"}, self.CTX))

    def test_not_null(self) -> None:
        self.assertTrue(evaluate_condition({"field": "priority", "op": "not_null"}, self.CTX))
        self.assertFalse(evaluate_condition({"field": "missing_field", "op": "not_null"}, self.CTX))

    def test_is_null(self) -> None:
        self.assertTrue(evaluate_condition({"field": "missing_field", "op": "is_null"}, self.CTX))

    def test_gt_gte_lt_lte(self) -> None:
        self.assertTrue(evaluate_condition({"field": "age_hours", "op": "gt", "value": 4}, self.CTX))
        self.assertTrue(evaluate_condition({"field": "age_hours", "op": "gte", "value": 5}, self.CTX))
        self.assertFalse(evaluate_condition({"field": "age_hours", "op": "lt", "value": 5}, self.CTX))
        self.assertTrue(evaluate_condition({"field": "age_hours", "op": "lte", "value": 5}, self.CTX))

    def test_and(self) -> None:
        cond = {"op": "and", "conditions": [
            {"field": "priority", "op": "eq", "value": "urgent"},
            {"field": "status", "op": "eq", "value": "awaiting_review"},
        ]}
        self.assertTrue(evaluate_condition(cond, self.CTX))

    def test_or(self) -> None:
        cond = {"op": "or", "conditions": [
            {"field": "priority", "op": "eq", "value": "low"},
            {"field": "status", "op": "eq", "value": "awaiting_review"},
        ]}
        self.assertTrue(evaluate_condition(cond, self.CTX))

    def test_not(self) -> None:
        cond = {"op": "not", "condition": {"field": "priority", "op": "eq", "value": "low"}}
        self.assertTrue(evaluate_condition(cond, self.CTX))

    def test_always_never(self) -> None:
        self.assertTrue(evaluate_condition({"op": "always"}, {}))
        self.assertFalse(evaluate_condition({"op": "never"}, {}))

    def test_dotted_field(self) -> None:
        ctx = {"request": {"metadata": {"category": "change"}}}
        self.assertTrue(evaluate_condition({"field": "request.metadata.category", "op": "eq", "value": "change"}, ctx))

    def test_invalid_condition(self) -> None:
        self.assertFalse(evaluate_condition("not a dict", {}))
        self.assertFalse(evaluate_condition({}, {}))

    def test_matches_regex(self) -> None:
        self.assertTrue(evaluate_condition({"field": "status", "op": "matches", "value": r"awaiting_.*"}, self.CTX))


class ValidateActionTest(unittest.TestCase):
    def test_valid_block(self) -> None:
        self.assertEqual(validate_action({"type": "block", "reason": "Policy violation"}), [])

    def test_block_without_reason(self) -> None:
        errors = validate_action({"type": "block"})
        self.assertTrue(any("reason" in e for e in errors))

    def test_unknown_type(self) -> None:
        errors = validate_action({"type": "unknown_action"})
        self.assertTrue(any("Unknown" in e for e in errors))

    def test_route_requires_target(self) -> None:
        errors = validate_action({"type": "route"})
        self.assertTrue(any("target_team" in e for e in errors))

    def test_valid_escalate(self) -> None:
        self.assertEqual(validate_action({"type": "escalate", "to": "team_ops", "reason": "SLA breach"}), [])

    def test_not_a_dict(self) -> None:
        self.assertTrue(validate_action("string"))


class EvaluateRuleTest(unittest.TestCase):
    def test_matching_rule_returns_actions(self) -> None:
        rule = {
            "condition": {"field": "priority", "op": "eq", "value": "urgent"},
            "actions": [{"type": "escalate", "to": "ops"}],
            "active": True,
        }
        result = evaluate_rule(rule, {"priority": "urgent"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["type"], "escalate")

    def test_non_matching_rule_returns_empty(self) -> None:
        rule = {
            "condition": {"field": "priority", "op": "eq", "value": "urgent"},
            "actions": [{"type": "block", "reason": "x"}],
        }
        self.assertEqual(evaluate_rule(rule, {"priority": "low"}), [])

    def test_inactive_rule_skipped(self) -> None:
        rule = {
            "condition": {"op": "always"},
            "actions": [{"type": "block", "reason": "x"}],
            "active": False,
        }
        self.assertEqual(evaluate_rule(rule, {}), [])


class EvaluateRulesTest(unittest.TestCase):
    def test_multiple_rules_aggregated(self) -> None:
        rules = [
            {"condition": {"op": "always"}, "actions": [{"type": "notify"}], "priority": 2},
            {"condition": {"op": "always"}, "actions": [{"type": "add_tag", "tag": "flagged"}], "priority": 1},
        ]
        result = evaluate_rules(rules, {})
        self.assertEqual(len(result), 2)
        # Lower priority first
        self.assertEqual(result[0]["type"], "add_tag")
        self.assertEqual(result[1]["type"], "notify")

    def test_no_matching_rules(self) -> None:
        rules = [{"condition": {"op": "never"}, "actions": [{"type": "block", "reason": "x"}]}]
        self.assertEqual(evaluate_rules(rules, {}), [])


class ActionHelpersTest(unittest.TestCase):
    def test_has_blocking_action(self) -> None:
        self.assertTrue(has_blocking_action([{"type": "block", "reason": "x"}]))
        self.assertFalse(has_blocking_action([{"type": "notify"}]))

    def test_get_actions_by_type(self) -> None:
        actions = [{"type": "block", "reason": "x"}, {"type": "notify"}, {"type": "block", "reason": "y"}]
        blocks = get_actions_by_type(actions, "block")
        self.assertEqual(len(blocks), 2)


if __name__ == "__main__":
    unittest.main()
