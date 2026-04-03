"""Unit tests for the extracted template engine module."""

import unittest

from app.domain.template_engine import (
    coerce_value,
    conditional_rule_matches,
    resolve_routing,
    resolve_routing_value,
    validate_definition,
    validate_payload,
)


class CoerceValueTest(unittest.TestCase):
    def test_valid_string(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "string"}, "hello"), "hello")

    def test_invalid_string(self) -> None:
        with self.assertRaises(ValueError):
            coerce_value("f", {"type": "string"}, 42)

    def test_valid_integer(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "integer"}, 7), 7)

    def test_boolean_not_integer(self) -> None:
        with self.assertRaises(ValueError):
            coerce_value("f", {"type": "integer"}, True)

    def test_valid_number(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "number"}, 3.14), 3.14)

    def test_valid_boolean(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "boolean"}, False), False)

    def test_invalid_boolean(self) -> None:
        with self.assertRaises(ValueError):
            coerce_value("f", {"type": "boolean"}, 0)

    def test_valid_array(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "array"}, [1, 2]), [1, 2])

    def test_valid_object(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "object"}, {"a": 1}), {"a": 1})

    def test_enum_valid(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "string", "enum": ["a", "b"]}, "a"), "a")

    def test_enum_invalid(self) -> None:
        with self.assertRaises(ValueError):
            coerce_value("f", {"type": "string", "enum": ["a", "b"]}, "c")

    def test_min_length(self) -> None:
        with self.assertRaises(ValueError):
            coerce_value("f", {"type": "string", "min_length": 5}, "ab")

    def test_max_length(self) -> None:
        with self.assertRaises(ValueError):
            coerce_value("f", {"type": "string", "max_length": 2}, "abc")

    def test_pattern(self) -> None:
        self.assertEqual(coerce_value("f", {"type": "string", "pattern": r"^\d+$"}, "123"), "123")
        with self.assertRaises(ValueError):
            coerce_value("f", {"type": "string", "pattern": r"^\d+$"}, "abc")


class ConditionalRuleMatchesTest(unittest.TestCase):
    def test_equals_match(self) -> None:
        rule = {"when": {"field": "type", "equals": "bug"}}
        self.assertTrue(conditional_rule_matches(rule, {"type": "bug"}))
        self.assertFalse(conditional_rule_matches(rule, {"type": "feature"}))

    def test_not_equals_match(self) -> None:
        rule = {"when": {"field": "type", "not_equals": "bug"}}
        self.assertTrue(conditional_rule_matches(rule, {"type": "feature"}))
        self.assertFalse(conditional_rule_matches(rule, {"type": "bug"}))

    def test_in_match(self) -> None:
        rule = {"when": {"field": "type", "in": ["bug", "hotfix"]}}
        self.assertTrue(conditional_rule_matches(rule, {"type": "bug"}))
        self.assertFalse(conditional_rule_matches(rule, {"type": "feature"}))

    def test_missing_field_returns_false(self) -> None:
        rule = {"when": {}}
        self.assertFalse(conditional_rule_matches(rule, {"type": "bug"}))


class ValidatePayloadTest(unittest.TestCase):
    SCHEMA = {
        "properties": {
            "title": {"type": "string", "title": "Title"},
            "priority": {"type": "string", "title": "Priority", "enum": ["low", "medium", "high"], "default": "medium"},
        },
        "required": ["title"],
    }

    def test_valid_payload_with_defaults(self) -> None:
        result = validate_payload(self.SCHEMA, {"title": "test"}, require_required=True)
        self.assertEqual(result["title"], "test")
        self.assertEqual(result["priority"], "medium")

    def test_missing_required_raises(self) -> None:
        with self.assertRaises(ValueError):
            validate_payload(self.SCHEMA, {}, require_required=True)

    def test_missing_required_allowed_when_not_required(self) -> None:
        result = validate_payload(self.SCHEMA, {}, require_required=False)
        self.assertEqual(result["priority"], "medium")

    def test_conditional_required(self) -> None:
        schema = {
            "properties": {
                "type": {"type": "string", "title": "Type"},
                "severity": {"type": "string", "title": "Severity"},
            },
            "required": ["type"],
            "conditional_required": [
                {"when": {"field": "type", "equals": "bug"}, "field": "severity", "message": "Severity required for bugs"},
            ],
        }
        with self.assertRaises(ValueError) as ctx:
            validate_payload(schema, {"type": "bug"}, require_required=True)
        self.assertIn("Severity required for bugs", str(ctx.exception))

        result = validate_payload(schema, {"type": "feature"}, require_required=True)
        self.assertEqual(result["type"], "feature")


class ValidateDefinitionTest(unittest.TestCase):
    def test_valid_schema(self) -> None:
        schema = {
            "properties": {
                "title": {"type": "string", "title": "Title"},
            },
            "required": ["title"],
        }
        result = validate_definition(schema)
        self.assertTrue(result.valid)
        self.assertEqual(result.preview.field_count, 1)

    def test_non_dict_schema(self) -> None:
        result = validate_definition("not a dict")
        self.assertFalse(result.valid)

    def test_unsupported_field_type(self) -> None:
        schema = {"properties": {"f": {"type": "blob", "title": "F"}}}
        result = validate_definition(schema)
        self.assertFalse(result.valid)

    def test_missing_title_warning(self) -> None:
        schema = {"properties": {"f": {"type": "string"}}}
        result = validate_definition(schema)
        self.assertTrue(result.valid)  # warning, not error
        self.assertTrue(any(i.level == "warning" and "title" in i.message for i in result.issues))

    def test_required_field_not_in_properties(self) -> None:
        schema = {"properties": {}, "required": ["ghost"]}
        result = validate_definition(schema)
        self.assertFalse(result.valid)

    def test_routing_owner_team(self) -> None:
        schema = {
            "properties": {"dept": {"type": "string", "title": "Dept"}},
            "routing": {"owner_team": "team_alpha"},
        }
        result = validate_definition(schema)
        self.assertTrue(result.valid)

    def test_promotion_requirements_validation(self) -> None:
        schema = {
            "properties": {"f": {"type": "string", "title": "F"}},
            "promotion_requirements": ["approval:lead", "check:lint"],
        }
        result = validate_definition(schema)
        self.assertTrue(result.valid)

    def test_promotion_requirements_invalid_syntax(self) -> None:
        schema = {
            "properties": {"f": {"type": "string", "title": "F"}},
            "promotion_requirements": ["no_colon"],
        }
        result = validate_definition(schema)
        self.assertFalse(result.valid)

    def test_empty_properties_warning(self) -> None:
        result = validate_definition({"properties": {}})
        self.assertTrue(any(i.level == "warning" and "no fields" in i.message.lower() for i in result.issues))

    def test_min_max_length_conflict(self) -> None:
        schema = {"properties": {"f": {"type": "string", "title": "F", "min_length": 10, "max_length": 5}}}
        result = validate_definition(schema)
        self.assertFalse(result.valid)


class ResolveRoutingTest(unittest.TestCase):
    def test_static_routing(self) -> None:
        schema = {
            "routing": {
                "owner_team": "team_alpha",
                "workflow_binding": "wf_standard",
                "reviewers": ["user_a"],
                "promotion_approvers": ["user_b"],
            }
        }
        result = resolve_routing(schema, {})
        self.assertEqual(result["owner_team_id"], "team_alpha")
        self.assertEqual(result["workflow_binding_id"], "wf_standard")
        self.assertEqual(result["reviewers"], ["user_a"])
        self.assertEqual(result["promotion_approvers"], ["user_b"])

    def test_field_based_routing(self) -> None:
        schema = {
            "routing": {
                "owner_team_by_field": {
                    "department": {"engineering": "team_eng", "design": "team_design"},
                },
            }
        }
        result = resolve_routing(schema, {"department": "engineering"})
        self.assertEqual(result["owner_team_id"], "team_eng")

    def test_unmatched_field_returns_none(self) -> None:
        schema = {
            "routing": {
                "owner_team_by_field": {
                    "department": {"engineering": "team_eng"},
                },
            }
        }
        result = resolve_routing(schema, {"department": "unknown"})
        self.assertIsNone(result["owner_team_id"])

    def test_empty_routing(self) -> None:
        result = resolve_routing({}, {})
        self.assertIsNone(result["owner_team_id"])
        self.assertIsNone(result["workflow_binding_id"])
        self.assertEqual(result["reviewers"], [])
        self.assertEqual(result["promotion_approvers"], [])


class ResolveRoutingValueTest(unittest.TestCase):
    def test_simple_value(self) -> None:
        result = resolve_routing_value({"dept": {"eng": "team_eng"}}, {"dept": "eng"})
        self.assertEqual(result, "team_eng")

    def test_wrapped_value(self) -> None:
        result = resolve_routing_value({"dept": {"eng": {"value": "team_eng"}}}, {"dept": "eng"})
        self.assertEqual(result, "team_eng")

    def test_no_match(self) -> None:
        result = resolve_routing_value({"dept": {"eng": "team_eng"}}, {"dept": "sales"})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
