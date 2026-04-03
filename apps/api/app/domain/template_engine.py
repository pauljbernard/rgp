"""Pure template schema validation, payload coercion, and routing resolution.

All functions in this module operate on plain dicts/values with no database
or I/O dependencies.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from app.models.template import (
    TemplateValidationIssue,
    TemplateValidationPreview,
    TemplateValidationPreviewField,
    TemplateValidationResult,
)


# ---------------------------------------------------------------------------
# Field-level helpers
# ---------------------------------------------------------------------------

def coerce_value(field_name: str, field_schema: dict, value: Any) -> Any:
    """Validate and return *value* against *field_schema*, raising on mismatch."""
    expected_type = field_schema.get("type")
    if expected_type == "string" and not isinstance(value, str):
        raise ValueError(f"Template validation failed for {field_name}: expected string")
    if expected_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
        raise ValueError(f"Template validation failed for {field_name}: expected integer")
    if expected_type == "number" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        raise ValueError(f"Template validation failed for {field_name}: expected number")
    if expected_type == "boolean" and not isinstance(value, bool):
        raise ValueError(f"Template validation failed for {field_name}: expected boolean")
    if expected_type == "array" and not isinstance(value, list):
        raise ValueError(f"Template validation failed for {field_name}: expected array")
    if expected_type == "object" and not isinstance(value, dict):
        raise ValueError(f"Template validation failed for {field_name}: expected object")
    allowed_values = field_schema.get("enum")
    if allowed_values and value not in allowed_values:
        raise ValueError(f"Template validation failed for {field_name}: expected one of {', '.join(str(item) for item in allowed_values)}")
    if isinstance(value, str):
        min_length = field_schema.get("min_length")
        max_length = field_schema.get("max_length")
        pattern = field_schema.get("pattern")
        if min_length is not None and len(value.strip()) < int(min_length):
            raise ValueError(f"Template validation failed for {field_name}: minimum length is {min_length}")
        if max_length is not None and len(value) > int(max_length):
            raise ValueError(f"Template validation failed for {field_name}: maximum length is {max_length}")
        if pattern and not re.fullmatch(str(pattern), value):
            raise ValueError(f"Template validation failed for {field_name}: does not match required format")
    return value


def conditional_rule_matches(rule: dict, field_values: dict) -> bool:
    """Return True if *rule*'s ``when`` clause matches the given *field_values*."""
    when = rule.get("when", {})
    field_name = when.get("field")
    if not field_name:
        return False
    current_value = field_values.get(field_name)
    if "equals" in when:
        return current_value == when.get("equals")
    if "not_equals" in when:
        return current_value != when.get("not_equals")
    if "in" in when:
        return current_value in when.get("in", [])
    return False


# ---------------------------------------------------------------------------
# Payload validation
# ---------------------------------------------------------------------------

def validate_payload(
    schema: dict,
    payload: dict,
    *,
    require_required: bool,
) -> dict:
    """Validate and normalize *payload* against *schema*.

    Returns a normalized copy of the payload with defaults applied and
    values coerced.  Raises ``ValueError`` on validation failure.
    """
    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))
    conditional_required = schema.get("conditional_required", [])
    normalized = deepcopy(payload)

    for field_name, field_schema in properties.items():
        if field_name not in normalized and "default" in field_schema:
            normalized[field_name] = deepcopy(field_schema["default"])

    for field_name in required_fields:
        value = normalized.get(field_name)
        if require_required and (value is None or (isinstance(value, str) and not value.strip())):
            raise ValueError(f"Template validation failed for {field_name}: field is required")

    for rule in conditional_required:
        target_field = rule.get("field")
        if not target_field or not conditional_rule_matches(rule, normalized):
            continue
        value = normalized.get(target_field)
        if require_required and (value is None or (isinstance(value, str) and not value.strip())):
            raise ValueError(rule.get("message") or f"Template validation failed for {target_field}: field is required")

    for field_name, value in list(normalized.items()):
        field_schema = properties.get(field_name)
        if field_schema is None:
            continue
        normalized[field_name] = coerce_value(field_name, field_schema, value)

    return normalized


# ---------------------------------------------------------------------------
# Definition validation
# ---------------------------------------------------------------------------

def validate_definition(template_schema: dict) -> TemplateValidationResult:
    """Validate a template definition schema and produce a preview.

    Returns a ``TemplateValidationResult`` with issues and a preview of
    the fields that would be rendered on the intake form.
    """
    issues: list[TemplateValidationIssue] = []
    if not isinstance(template_schema, dict):
        return TemplateValidationResult(
            valid=False,
            issues=[TemplateValidationIssue(level="error", path="schema", message="Template schema must be an object.")],
            preview=TemplateValidationPreview(field_count=0, required_fields=[], conditional_rule_count=0, routed_fields=[], fields=[]),
        )

    properties = template_schema.get("properties", {})
    required_fields = template_schema.get("required", [])
    conditional_required = template_schema.get("conditional_required", [])
    routing = template_schema.get("routing", {})

    if not isinstance(properties, dict):
        issues.append(TemplateValidationIssue(level="error", path="schema.properties", message="Properties must be an object."))
        properties = {}
    if not isinstance(required_fields, list):
        issues.append(TemplateValidationIssue(level="error", path="schema.required", message="Required must be a list of field keys."))
        required_fields = []
    if not isinstance(conditional_required, list):
        issues.append(TemplateValidationIssue(level="error", path="schema.conditional_required", message="Conditional rules must be a list."))
        conditional_required = []
    if not isinstance(routing, dict):
        issues.append(TemplateValidationIssue(level="error", path="schema.routing", message="Routing must be an object."))
        routing = {}

    allowed_types = {"string", "number", "integer", "boolean"}
    property_keys = set(properties.keys())
    preview_fields: list[TemplateValidationPreviewField] = []
    routing_rule_count = 0

    for key, definition in properties.items():
        if not isinstance(definition, dict):
            issues.append(TemplateValidationIssue(level="error", path=f"schema.properties.{key}", message="Field definition must be an object."))
            continue
        field_type = str(definition.get("type", "") or "")
        if field_type not in allowed_types:
            issues.append(TemplateValidationIssue(level="error", path=f"schema.properties.{key}.type", message=f"Unsupported field type {field_type or '<missing>'}."))
        if "title" not in definition:
            issues.append(TemplateValidationIssue(level="warning", path=f"schema.properties.{key}.title", message="Field title is missing."))
        enum_values = definition.get("enum", [])
        if enum_values and not isinstance(enum_values, list):
            issues.append(TemplateValidationIssue(level="error", path=f"schema.properties.{key}.enum", message="Enum must be a list."))
        if isinstance(definition.get("min_length"), int) and isinstance(definition.get("max_length"), int):
            if int(definition["min_length"]) > int(definition["max_length"]):
                issues.append(TemplateValidationIssue(level="error", path=f"schema.properties.{key}", message="min_length cannot exceed max_length."))
        preview_fields.append(
            TemplateValidationPreviewField(
                key=key,
                title=str(definition.get("title", key)),
                field_type=field_type or "unknown",
                required=key in required_fields,
                default=definition.get("default"),
                enum_values=[str(item) for item in enum_values] if isinstance(enum_values, list) else [],
                description=str(definition.get("description")) if definition.get("description") is not None else None,
            )
        )

    for field in required_fields:
        if field not in property_keys:
            issues.append(TemplateValidationIssue(level="error", path="schema.required", message=f"Required field {field} is not defined in properties."))

    for index, rule in enumerate(conditional_required):
        if not isinstance(rule, dict):
            issues.append(TemplateValidationIssue(level="error", path=f"schema.conditional_required[{index}]", message="Conditional rule must be an object."))
            continue
        when = rule.get("when", {})
        fields = rule.get("fields")
        if fields is None and rule.get("field"):
            fields = [rule.get("field")]
        when_field = when.get("field") if isinstance(when, dict) else None
        if when_field not in property_keys:
            issues.append(TemplateValidationIssue(level="error", path=f"schema.conditional_required[{index}].when.field", message="Conditional rule references an unknown field."))
        if not isinstance(fields, list) or not fields:
            issues.append(TemplateValidationIssue(level="error", path=f"schema.conditional_required[{index}].fields", message="Conditional rule must list one or more dependent fields."))
            continue
        for field in fields:
            if field not in property_keys:
                issues.append(TemplateValidationIssue(level="error", path=f"schema.conditional_required[{index}].fields", message=f"Conditional field {field} is not defined in properties."))

    routed_fields: set[str] = set()
    for route_key, route_mapping in routing.items():
        if route_key == "owner_team":
            if not isinstance(route_mapping, str) or not route_mapping.strip():
                issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}", message="owner_team must be a non-empty string."))
            continue
        if route_key == "workflow_binding":
            if not isinstance(route_mapping, str) or not route_mapping.strip():
                issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}", message="workflow_binding must be a non-empty string."))
            continue
        if route_key in {"reviewers", "promotion_approvers"}:
            if not isinstance(route_mapping, list) or not all(isinstance(item, str) and item.strip() for item in route_mapping):
                issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}", message=f"{route_key} must be a list of non-empty strings."))
            continue
        if not isinstance(route_mapping, dict):
            issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}", message="Routing mapping must be an object."))
            continue
        for field_name, field_mapping in route_mapping.items():
            routed_fields.add(str(field_name))
            if field_name not in property_keys:
                issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}.{field_name}", message="Routing references an unknown field."))
            if not isinstance(field_mapping, dict):
                issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}.{field_name}", message="Routing field mapping must be an object."))
                continue
            for match_value, target_value in field_mapping.items():
                routing_rule_count += 1
                if not str(match_value).strip():
                    issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}.{field_name}", message="Routing match value must be non-empty."))
                normalized_target = target_value
                if isinstance(target_value, dict) and "value" in target_value:
                    normalized_target = target_value.get("value")
                if route_key in {"reviewers_by_field", "promotion_approvers_by_field"}:
                    if not isinstance(normalized_target, list) or not all(isinstance(item, str) and item.strip() for item in normalized_target):
                        issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}.{field_name}.{match_value}", message="Target value must be a list of non-empty strings."))
                else:
                    if not isinstance(normalized_target, str) or not normalized_target.strip():
                        issues.append(TemplateValidationIssue(level="error", path=f"schema.routing.{route_key}.{field_name}.{match_value}", message="Target value must be a non-empty string."))

    list_values: dict[str, list[str]] = {}
    for list_key, label in {
        "expected_artifact_types": "Expected artifact types",
        "check_requirements": "Check requirements",
        "promotion_requirements": "Promotion requirements",
    }.items():
        value = template_schema.get(list_key, [])
        if value is None:
            list_values[list_key] = []
            continue
        if not isinstance(value, list):
            issues.append(TemplateValidationIssue(level="error", path=f"schema.{list_key}", message=f"{label} must be a list."))
            list_values[list_key] = []
            continue
        normalized_items: list[str] = []
        seen_items: set[str] = set()
        for idx, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                issues.append(TemplateValidationIssue(level="error", path=f"schema.{list_key}[{idx}]", message=f"{label} entries must be non-empty strings."))
                continue
            normalized = item.strip()
            normalized_items.append(normalized)
            if normalized in seen_items:
                issues.append(TemplateValidationIssue(level="warning", path=f"schema.{list_key}[{idx}]", message=f"{label} contains duplicate entry {normalized}."))
            seen_items.add(normalized)
            if list_key in {"expected_artifact_types", "check_requirements"} and not re.match(r"^[a-z][a-z0-9_:-]*$", normalized):
                issues.append(TemplateValidationIssue(level="error", path=f"schema.{list_key}[{idx}]", message=f"{label} must use lowercase identifier syntax."))
            if list_key == "promotion_requirements":
                if ":" not in normalized:
                    issues.append(TemplateValidationIssue(level="error", path=f"schema.{list_key}[{idx}]", message="Promotion requirement must use type:value syntax."))
                else:
                    requirement_type, requirement_value = normalized.split(":", 1)
                    if requirement_type not in {"approval", "check", "segregation_of_duties"}:
                        issues.append(TemplateValidationIssue(level="warning", path=f"schema.{list_key}[{idx}]", message=f"Unknown promotion requirement type {requirement_type}."))
                    if not requirement_value.strip():
                        issues.append(TemplateValidationIssue(level="error", path=f"schema.{list_key}[{idx}]", message="Promotion requirement value must be non-empty."))
        list_values[list_key] = normalized_items

    if not property_keys:
        issues.append(TemplateValidationIssue(level="warning", path="schema.properties", message="Template has no fields defined."))
    if "expected_artifact_types" in template_schema and not list_values.get("expected_artifact_types"):
        issues.append(TemplateValidationIssue(level="warning", path="schema.expected_artifact_types", message="No expected artifact types defined."))
    if "check_requirements" in template_schema and not list_values.get("check_requirements"):
        issues.append(TemplateValidationIssue(level="warning", path="schema.check_requirements", message="No check requirements defined."))
    if "promotion_requirements" in template_schema and not list_values.get("promotion_requirements"):
        issues.append(TemplateValidationIssue(level="warning", path="schema.promotion_requirements", message="No promotion requirements defined."))

    field_order_map = {
        key: int(definition.get("order"))
        for key, definition in properties.items()
        if isinstance(definition, dict) and definition.get("order") is not None
    }
    issues.sort(key=lambda issue: (issue.level != "error", issue.path))
    preview_fields.sort(key=lambda field: (field_order_map.get(field.key, 10_000), field.key))
    return TemplateValidationResult(
        valid=not any(issue.level == "error" for issue in issues),
        issues=issues,
        preview=TemplateValidationPreview(
            field_count=len(preview_fields),
            required_fields=[str(field) for field in required_fields],
            conditional_rule_count=len(conditional_required) if isinstance(conditional_required, list) else 0,
            routing_rule_count=routing_rule_count,
            artifact_type_count=len(list_values.get("expected_artifact_types", [])),
            check_requirement_count=len(list_values.get("check_requirements", [])),
            promotion_requirement_count=len(list_values.get("promotion_requirements", [])),
            routed_fields=sorted(routed_fields),
            fields=preview_fields,
        ),
    )


# ---------------------------------------------------------------------------
# Routing resolution
# ---------------------------------------------------------------------------

def resolve_routing_value(mapping_groups: dict, field_values: dict) -> Any:
    """Resolve a single routing value from field-based routing mappings."""
    for source_field, mapping in mapping_groups.items():
        field_value = field_values.get(source_field)
        if isinstance(mapping, dict) and field_value in mapping:
            target = deepcopy(mapping[field_value])
            if isinstance(target, dict) and "value" in target:
                return deepcopy(target["value"])
            return target
    return None


def resolve_routing(schema: dict, input_payload: dict) -> dict:
    """Resolve ownership, workflow, reviewers, and approvers from *schema* routing.

    Returns a dict with keys: ``owner_team_id``, ``workflow_binding_id``,
    ``reviewers``, ``promotion_approvers``.
    """
    routing = schema.get("routing", {})
    owner_team = routing.get("owner_team")
    if owner_team is None:
        owner_team = resolve_routing_value(routing.get("owner_team_by_field", {}), input_payload)

    workflow_binding = routing.get("workflow_binding")
    if workflow_binding is None:
        workflow_binding = resolve_routing_value(routing.get("workflow_binding_by_field", {}), input_payload)

    reviewers = routing.get("reviewers")
    if reviewers is None:
        reviewers = resolve_routing_value(routing.get("reviewers_by_field", {}), input_payload)
    if not isinstance(reviewers, list):
        reviewers = []

    promotion_approvers = routing.get("promotion_approvers")
    if promotion_approvers is None:
        promotion_approvers = resolve_routing_value(routing.get("promotion_approvers_by_field", {}), input_payload)
    if not isinstance(promotion_approvers, list):
        promotion_approvers = []

    return {
        "owner_team_id": owner_team,
        "workflow_binding_id": workflow_binding,
        "reviewers": reviewers,
        "promotion_approvers": promotion_approvers,
    }
