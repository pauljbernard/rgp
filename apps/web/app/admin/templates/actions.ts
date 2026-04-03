"use server";

import {
  createAdminTemplateVersion,
  deleteAdminTemplateVersion,
  deprecateAdminTemplateVersion,
  publishAdminTemplateVersion,
  updateAdminTemplateDefinition,
} from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

function parseIntegerValue(value: FormDataEntryValue | null) {
  if (typeof value !== "string" || !value.trim()) {
    return undefined;
  }
  const parsed = Number.parseInt(value.trim(), 10);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function parseStructuredSchema(formData: FormData) {
  const properties: Record<string, Record<string, unknown>> = {};
  const required: string[] = [];
  const conditionalRequired: Array<Record<string, unknown>> = [];
  const expectedArtifactTypes = String(formData.get("expected_artifact_types") ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const checkRequirements = String(formData.get("check_requirements") ?? "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
  const promotionRequirements = String(formData.get("promotion_requirements") ?? "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

  const rowCount = Number.parseInt(String(formData.get("field_row_count") ?? "0"), 10) || 0;
  const fieldRows: Array<{
    index: number;
    order: number;
    key: string;
    title: string;
    fieldType: string;
    description: string;
    defaultValue: string;
    enumCsv: string;
    pattern: string;
    minLength: number | undefined;
    maxLength: number | undefined;
    required: boolean;
  }> = [];
  for (let index = 0; index < rowCount; index += 1) {
    if (formData.get(`field_enabled_${index}`) !== "on") {
      continue;
    }
    const key = String(formData.get(`field_key_${index}`) ?? "").trim();
    if (!key) {
      continue;
    }
    fieldRows.push({
      index,
      order: parseIntegerValue(formData.get(`field_order_${index}`)) ?? index,
      key,
      title: String(formData.get(`field_title_${index}`) ?? "").trim() || key,
      fieldType: String(formData.get(`field_type_${index}`) ?? "").trim() || "string",
      description: String(formData.get(`field_description_${index}`) ?? "").trim(),
      defaultValue: String(formData.get(`field_default_${index}`) ?? "").trim(),
      enumCsv: String(formData.get(`field_enum_${index}`) ?? "").trim(),
      pattern: String(formData.get(`field_pattern_${index}`) ?? "").trim(),
      minLength: parseIntegerValue(formData.get(`field_min_length_${index}`)),
      maxLength: parseIntegerValue(formData.get(`field_max_length_${index}`)),
      required: formData.get(`field_required_${index}`) === "on",
    });
  }
  for (const field of fieldRows.sort((left, right) => left.order - right.order || left.index - right.index)) {
    const fieldSchema: Record<string, unknown> = {
      type: field.fieldType,
      title: field.title,
      order: field.order,
    };
    if (field.description) {
      fieldSchema.description = field.description;
    }
    if (field.defaultValue) {
      fieldSchema.default = field.defaultValue;
    }
    if (field.enumCsv) {
      fieldSchema.enum = field.enumCsv
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    }
    if (field.pattern) {
      fieldSchema.pattern = field.pattern;
    }
    if (field.minLength !== undefined) {
      fieldSchema.min_length = field.minLength;
    }
    if (field.maxLength !== undefined) {
      fieldSchema.max_length = field.maxLength;
    }
    properties[field.key] = fieldSchema;
    if (field.required) {
      required.push(field.key);
    }
  }

  const ruleCount = Number.parseInt(String(formData.get("rule_row_count") ?? "0"), 10) || 0;
  const ruleRows: Array<{ index: number; order: number; whenField: string; equals: string; targetField: string; message: string }> = [];
  for (let index = 0; index < ruleCount; index += 1) {
    if (formData.get(`rule_enabled_${index}`) !== "on") {
      continue;
    }
    const whenField = String(formData.get(`rule_when_field_${index}`) ?? "").trim();
    const equals = String(formData.get(`rule_equals_${index}`) ?? "").trim();
    const targetField = String(formData.get(`rule_target_field_${index}`) ?? "").trim();
    const message = String(formData.get(`rule_message_${index}`) ?? "").trim();
    if (!whenField || !targetField) {
      continue;
    }
    ruleRows.push({
      index,
      order: parseIntegerValue(formData.get(`rule_order_${index}`)) ?? index,
      whenField,
      equals,
      targetField,
      message,
    });
  }
  for (const rule of ruleRows.sort((left, right) => left.order - right.order || left.index - right.index)) {
    conditionalRequired.push({
      order: rule.order,
      when: {
        field: rule.whenField,
        ...(rule.equals ? { equals: rule.equals } : {}),
      },
      field: rule.targetField,
      ...(rule.message ? { message: rule.message } : {}),
    });
  }

  const routing: Record<string, unknown> = {};
  const ownerTeam = String(formData.get("routing_owner_team") ?? "").trim();
  const workflowBinding = String(formData.get("routing_workflow_binding") ?? "").trim();
  const reviewersCsv = String(formData.get("routing_reviewers") ?? "").trim();
  const approversCsv = String(formData.get("routing_promotion_approvers") ?? "").trim();
  if (ownerTeam) {
    routing.owner_team = ownerTeam;
  }
  if (workflowBinding) {
    routing.workflow_binding = workflowBinding;
  }
  if (reviewersCsv) {
    routing.reviewers = reviewersCsv
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }
  if (approversCsv) {
    routing.promotion_approvers = approversCsv
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  const routingRuleCount = Number.parseInt(String(formData.get("routing_rule_row_count") ?? "0"), 10) || 0;
  const routingRuleRows: Array<{ index: number; order: number; routeType: string; sourceField: string; matchValue: string; targetValue: string }> = [];
  const routingRuleBuckets: Record<
    string,
    Record<string, Record<string, string | string[] | { order: number; value: string | string[] }>>
  > = {
    owner_team_by_field: {},
    workflow_binding_by_field: {},
    reviewers_by_field: {},
    promotion_approvers_by_field: {},
  };
  for (let index = 0; index < routingRuleCount; index += 1) {
    if (formData.get(`routing_rule_enabled_${index}`) !== "on") {
      continue;
    }
    const routeType = String(formData.get(`routing_rule_type_${index}`) ?? "").trim();
    const sourceField = String(formData.get(`routing_rule_source_field_${index}`) ?? "").trim();
    const matchValue = String(formData.get(`routing_rule_match_value_${index}`) ?? "").trim();
    const targetValue = String(formData.get(`routing_rule_target_value_${index}`) ?? "").trim();
    if (!routeType || !sourceField || !matchValue || !targetValue || !(routeType in routingRuleBuckets)) {
      continue;
    }
    routingRuleRows.push({
      index,
      order: parseIntegerValue(formData.get(`routing_rule_order_${index}`)) ?? index,
      routeType,
      sourceField,
      matchValue,
      targetValue,
    });
  }
  for (const rule of routingRuleRows.sort((left, right) => left.order - right.order || left.index - right.index)) {
    const { routeType, sourceField, matchValue, targetValue } = rule;
    routingRuleBuckets[routeType] ??= {};
    routingRuleBuckets[routeType][sourceField] ??= {};
    routingRuleBuckets[routeType][sourceField][matchValue] =
      routeType === "reviewers_by_field" || routeType === "promotion_approvers_by_field"
        ? {
            order: rule.order,
            value: targetValue
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean),
          }
        : {
            order: rule.order,
            value: targetValue,
          };
  }
  for (const [routeType, mapping] of Object.entries(routingRuleBuckets)) {
    if (Object.keys(mapping).length) {
      routing[routeType] = mapping;
    }
  }

  const routingText = String(formData.get("routing_json") ?? "").trim();
  if (routingText) {
    try {
      Object.assign(routing, JSON.parse(routingText) as Record<string, unknown>);
    } catch {
      throw new Error("Routing JSON must be valid JSON");
    }
  }

  return {
    required,
    properties,
    routing,
    conditional_required: conditionalRequired,
    expected_artifact_types: expectedArtifactTypes,
    check_requirements: checkRequirements,
    promotion_requirements: promotionRequirements,
  };
}

export async function createTemplateVersionAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const version = formData.get("version");
  const sourceVersion = formData.get("sourceVersion");
  const startBlank = formData.get("startBlank");
  const name = formData.get("name");
  const description = formData.get("description");
  if (typeof templateId !== "string" || typeof version !== "string") {
    throw new Error("Missing template version fields");
  }
  const created = await createAdminTemplateVersion({
    template_id: templateId.trim(),
    version: version.trim(),
    source_version: startBlank === "on" ? undefined : typeof sourceVersion === "string" && sourceVersion.trim() ? sourceVersion.trim() : undefined,
    name: typeof name === "string" && name.trim() ? name.trim() : undefined,
    description: typeof description === "string" && description.trim() ? description.trim() : undefined,
  });
  revalidatePath("/admin/templates");
  redirect(`/admin/templates/${encodeURIComponent(created.id)}/${encodeURIComponent(created.version)}`);
}

export async function createTemplateIdentityAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const name = formData.get("name");
  const description = formData.get("description");
  const initialVersion = formData.get("initialVersion");
  if (
    typeof templateId !== "string" ||
    typeof name !== "string" ||
    typeof description !== "string" ||
    typeof initialVersion !== "string"
  ) {
    throw new Error("Missing template identity fields");
  }
  const created = await createAdminTemplateVersion({
    template_id: templateId.trim(),
    version: initialVersion.trim() || "1.0.0",
    source_version: undefined,
    name: name.trim(),
    description: description.trim(),
  });
  revalidatePath("/admin/templates");
  redirect(`/admin/templates/${encodeURIComponent(created.id)}/${encodeURIComponent(created.version)}`);
}

export async function saveTemplateDefinitionAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const version = formData.get("version");
  const name = formData.get("name");
  const description = formData.get("description");
  if (
    typeof templateId !== "string" ||
    typeof version !== "string" ||
    typeof name !== "string" ||
    typeof description !== "string"
  ) {
    throw new Error("Missing template definition fields");
  }
  const schema = parseStructuredSchema(formData);

  await updateAdminTemplateDefinition(templateId, version, {
    name: name.trim(),
    description: description.trim(),
    schema,
  });
  revalidatePath("/admin/templates");
  redirect(`/admin/templates/${encodeURIComponent(templateId)}/${encodeURIComponent(version)}?saved=1`);
}

export async function validateTemplateDefinitionAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const version = formData.get("version");
  if (typeof templateId !== "string" || typeof version !== "string") {
    throw new Error("Missing template selection fields");
  }
  redirect(`/admin/templates/${encodeURIComponent(templateId)}/${encodeURIComponent(version)}?validate=1`);
}

export async function publishTemplateVersionAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const version = formData.get("version");
  if (typeof templateId !== "string" || typeof version !== "string") {
    throw new Error("Missing publish fields");
  }
  await publishAdminTemplateVersion(templateId, version);
  revalidatePath("/admin/templates");
  revalidatePath("/requests/new");
  redirect(`/admin/templates/${encodeURIComponent(templateId)}/${encodeURIComponent(version)}`);
}

export async function deprecateTemplateVersionAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const version = formData.get("version");
  if (typeof templateId !== "string" || typeof version !== "string") {
    throw new Error("Missing deprecate fields");
  }
  await deprecateAdminTemplateVersion(templateId, version);
  revalidatePath("/admin/templates");
  revalidatePath("/requests/new");
  redirect(`/admin/templates/${encodeURIComponent(templateId)}/${encodeURIComponent(version)}`);
}

export async function deleteTemplateVersionAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const version = formData.get("version");
  if (typeof templateId !== "string" || typeof version !== "string") {
    throw new Error("Missing delete fields");
  }
  await deleteAdminTemplateVersion(templateId, version);
  revalidatePath("/admin/templates");
  redirect("/admin/templates?deleted=1");
}
