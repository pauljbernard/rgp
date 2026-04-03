import React from "react";
import { listAdminTemplates, validateAdminTemplateDefinition } from "@/lib/server-api";
import { Button, PageShell, SectionHeading, Tabs, appShellProps } from "../../../../../components/ui-helpers";
import { createTemplateVersionAction, deleteTemplateVersionAction, deprecateTemplateVersionAction, publishTemplateVersionAction, saveTemplateDefinitionAction, validateTemplateDefinitionAction } from "../../actions";

type AdminTemplatesPageProps = {
  params: Promise<{ templateId: string; version: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function schemaFieldCount(schema: Record<string, unknown>) {
  const properties = schema.properties;
  return properties && typeof properties === "object" ? Object.keys(properties as Record<string, unknown>).length : 0;
}

function schemaRequiredFields(schema: Record<string, unknown>) {
  return Array.isArray(schema.required) ? schema.required.map((item) => String(item)) : [];
}

function schemaProperties(schema: Record<string, unknown>) {
  const properties = schema.properties;
  if (!properties || typeof properties !== "object") {
    return [];
  }
  return Object.entries(properties as Record<string, Record<string, unknown>>).map(([key, definition]) => ({
    key,
    title: String(definition.title ?? key),
    fieldType: String(definition.type ?? "string"),
    description: String(definition.description ?? ""),
    defaultValue: definition.default == null ? "" : String(definition.default),
    enumCsv: Array.isArray(definition.enum) ? definition.enum.map((item) => String(item)).join(", ") : "",
    pattern: String(definition.pattern ?? ""),
    minLength: definition.min_length == null ? "" : String(definition.min_length),
    maxLength: definition.max_length == null ? "" : String(definition.max_length),
    order: definition.order == null ? "" : String(definition.order),
    required: schemaRequiredFields(schema).includes(key),
  })).sort((left, right) => {
    const leftOrder = Number.parseInt(left.order || "", 10);
    const rightOrder = Number.parseInt(right.order || "", 10);
    return (Number.isFinite(leftOrder) ? leftOrder : Number.MAX_SAFE_INTEGER) - (Number.isFinite(rightOrder) ? rightOrder : Number.MAX_SAFE_INTEGER) || left.key.localeCompare(right.key);
  });
}

function schemaConditionalRules(schema: Record<string, unknown>) {
  const rules = schema.conditional_required;
  if (!Array.isArray(rules)) {
    return [];
  }
  return rules.map((rule) => {
    const condition = typeof rule === "object" && rule ? (rule as Record<string, unknown>) : {};
    const when = typeof condition.when === "object" && condition.when ? (condition.when as Record<string, unknown>) : {};
    return {
      order: condition.order == null ? "" : String(condition.order),
      whenField: String(when.field ?? ""),
      equals: String(when.equals ?? ""),
      targetField: String(condition.field ?? ""),
      message: String(condition.message ?? ""),
    };
  }).sort((left, right) => {
    const leftOrder = Number.parseInt(left.order || "", 10);
    const rightOrder = Number.parseInt(right.order || "", 10);
    return (Number.isFinite(leftOrder) ? leftOrder : Number.MAX_SAFE_INTEGER) - (Number.isFinite(rightOrder) ? rightOrder : Number.MAX_SAFE_INTEGER) || left.targetField.localeCompare(right.targetField);
  });
}

function schemaRouting(schema: Record<string, unknown>) {
  const routing = schema.routing;
  if (!routing || typeof routing !== "object") {
    return {
      ownerTeam: "",
      workflowBinding: "",
      reviewersCsv: "",
      approversCsv: "",
      advancedJson: "{}",
    };
  }
  const routingRecord = routing as Record<string, unknown>;
  const advancedEntries = Object.fromEntries(
    Object.entries(routingRecord).filter(([key]) => !["owner_team", "workflow_binding", "reviewers", "promotion_approvers"].includes(key))
  );
  return {
    ownerTeam: String(routingRecord.owner_team ?? ""),
    workflowBinding: String(routingRecord.workflow_binding ?? ""),
    reviewersCsv: Array.isArray(routingRecord.reviewers) ? routingRecord.reviewers.map((item) => String(item)).join(", ") : "",
    approversCsv: Array.isArray(routingRecord.promotion_approvers) ? routingRecord.promotion_approvers.map((item) => String(item)).join(", ") : "",
    advancedJson: JSON.stringify(advancedEntries, null, 2),
  };
}

function schemaStringList(schema: Record<string, unknown>, key: string) {
  const value = schema[key];
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}

function schemaRoutingRuleRows(schema: Record<string, unknown>) {
  const routing = schema.routing;
  const rows: Array<{ order: string; routeType: string; sourceField: string; matchValue: string; targetValue: string }> = [];
  if (!routing || typeof routing !== "object") {
    return rows;
  }
  const routingRecord = routing as Record<string, unknown>;
  for (const routeType of ["owner_team_by_field", "workflow_binding_by_field", "reviewers_by_field", "promotion_approvers_by_field"]) {
    const group = routingRecord[routeType];
    if (!group || typeof group !== "object") {
      continue;
    }
    for (const [sourceField, mapping] of Object.entries(group as Record<string, Record<string, unknown>>)) {
      if (!mapping || typeof mapping !== "object") {
        continue;
      }
      for (const [matchValue, targetValue] of Object.entries(mapping)) {
        const typedTarget = targetValue as { value?: unknown; order?: unknown };
        rows.push({
          order: typeof typedTarget?.order === "number" ? String(typedTarget.order) : "",
          routeType,
          sourceField,
          matchValue,
          targetValue:
            typeof typedTarget?.value !== "undefined"
              ? Array.isArray(typedTarget.value)
                ? typedTarget.value.map((item) => String(item)).join(", ")
                : String(typedTarget.value)
              : Array.isArray(targetValue)
                ? targetValue.map((item) => String(item)).join(", ")
                : String(targetValue),
        });
      }
    }
  }
  return rows.sort((left, right) => {
    const leftOrder = Number.parseInt(left.order || "", 10);
    const rightOrder = Number.parseInt(right.order || "", 10);
    return (Number.isFinite(leftOrder) ? leftOrder : Number.MAX_SAFE_INTEGER) - (Number.isFinite(rightOrder) ? rightOrder : Number.MAX_SAFE_INTEGER) || left.sourceField.localeCompare(right.sourceField);
  });
}

function versionSortKey(version: string) {
  return version
    .split(".")
    .map((part) => Number.parseInt(part, 10) || 0)
    .slice(0, 3);
}

function suggestNextDraftVersion(version: string) {
  const parts = version.split(".").map((part) => Number.parseInt(part, 10));
  const major = Number.isFinite(parts[0]) ? parts[0] : 1;
  const minor = Number.isFinite(parts[1]) ? parts[1] : 0;
  const patch = Number.isFinite(parts[2]) ? parts[2] : 0;
  return `${major}.${minor}.${patch + 1}`;
}

function compareTemplateSchemas(currentSchema: Record<string, unknown>, previousSchema: Record<string, unknown>) {
  const currentFieldList = schemaProperties(currentSchema).filter((field) => field.key);
  const previousFieldList = schemaProperties(previousSchema).filter((field) => field.key);
  const currentFieldMap = new Map(currentFieldList.map((field) => [field.key, field]));
  const previousFieldMap = new Map(previousFieldList.map((field) => [field.key, field]));
  const currentFields = new Set(currentFieldMap.keys());
  const previousFields = new Set(previousFieldMap.keys());
  const addedFields = [...currentFields].filter((field) => !previousFields.has(field));
  const removedFields = [...previousFields].filter((field) => !currentFields.has(field));
  const changedFields = [...currentFields]
    .filter((field) => previousFields.has(field))
    .map((field) => {
      const currentField = currentFieldMap.get(field);
      const previousField = previousFieldMap.get(field);
      if (!currentField || !previousField) {
        return null;
      }
      const changes: string[] = [];
      if (currentField.title !== previousField.title) {
        changes.push(`title: ${previousField.title} -> ${currentField.title}`);
      }
      if (currentField.fieldType !== previousField.fieldType) {
        changes.push(`type: ${previousField.fieldType} -> ${currentField.fieldType}`);
      }
      if (currentField.required !== previousField.required) {
        changes.push(`required: ${previousField.required ? "yes" : "no"} -> ${currentField.required ? "yes" : "no"}`);
      }
      if (currentField.defaultValue !== previousField.defaultValue) {
        changes.push(`default: ${previousField.defaultValue || "none"} -> ${currentField.defaultValue || "none"}`);
      }
      if (currentField.enumCsv !== previousField.enumCsv) {
        changes.push(`enum: ${previousField.enumCsv || "none"} -> ${currentField.enumCsv || "none"}`);
      }
      if (currentField.pattern !== previousField.pattern) {
        changes.push(`pattern changed`);
      }
      if (currentField.minLength !== previousField.minLength || currentField.maxLength !== previousField.maxLength) {
        changes.push(`length bounds changed`);
      }
      if (currentField.order !== previousField.order) {
        changes.push(`order: ${previousField.order || "auto"} -> ${currentField.order || "auto"}`);
      }
      return changes.length ? { key: field, changes } : null;
    })
    .filter((item): item is { key: string; changes: string[] } => item !== null);
  const currentArtifactTypes = new Set(schemaStringList(currentSchema, "expected_artifact_types"));
  const previousArtifactTypes = new Set(schemaStringList(previousSchema, "expected_artifact_types"));
  const currentChecks = new Set(schemaStringList(currentSchema, "check_requirements"));
  const previousChecks = new Set(schemaStringList(previousSchema, "check_requirements"));
  const currentPromotionRequirements = new Set(schemaStringList(currentSchema, "promotion_requirements"));
  const previousPromotionRequirements = new Set(schemaStringList(previousSchema, "promotion_requirements"));
  const currentRouting = schemaRouting(currentSchema);
  const previousRouting = schemaRouting(previousSchema);
  const currentRoutingRuleRows = schemaRoutingRuleRows(currentSchema);
  const previousRoutingRuleRows = schemaRoutingRuleRows(previousSchema);
  const currentRoutingRules = currentRoutingRuleRows.length;
  const previousRoutingRules = previousRoutingRuleRows.length;
  const currentConditionalRuleRows = schemaConditionalRules(currentSchema);
  const previousConditionalRuleRows = schemaConditionalRules(previousSchema);
  const currentConditionalRules = currentConditionalRuleRows.length;
  const previousConditionalRules = previousConditionalRuleRows.length;
  const currentRoutingRuleSet = new Set(
    currentRoutingRuleRows.map((rule) => `${rule.routeType}|${rule.sourceField}|${rule.matchValue}|${rule.targetValue}`)
  );
  const previousRoutingRuleSet = new Set(
    previousRoutingRuleRows.map((rule) => `${rule.routeType}|${rule.sourceField}|${rule.matchValue}|${rule.targetValue}`)
  );
  const currentConditionalRuleSet = new Set(
    currentConditionalRuleRows.map((rule) => `${rule.whenField}|${rule.equals}|${rule.targetField}|${rule.message}`)
  );
  const previousConditionalRuleSet = new Set(
    previousConditionalRuleRows.map((rule) => `${rule.whenField}|${rule.equals}|${rule.targetField}|${rule.message}`)
  );
  const changedDefaultRouting: string[] = [];
  if (currentRouting.ownerTeam !== previousRouting.ownerTeam) {
    changedDefaultRouting.push(`owner_team: ${previousRouting.ownerTeam || "none"} -> ${currentRouting.ownerTeam || "none"}`);
  }
  if (currentRouting.workflowBinding !== previousRouting.workflowBinding) {
    changedDefaultRouting.push(`workflow_binding: ${previousRouting.workflowBinding || "none"} -> ${currentRouting.workflowBinding || "none"}`);
  }
  if (currentRouting.reviewersCsv !== previousRouting.reviewersCsv) {
    changedDefaultRouting.push(`reviewers: ${previousRouting.reviewersCsv || "none"} -> ${currentRouting.reviewersCsv || "none"}`);
  }
  if (currentRouting.approversCsv !== previousRouting.approversCsv) {
    changedDefaultRouting.push(`promotion_approvers: ${previousRouting.approversCsv || "none"} -> ${currentRouting.approversCsv || "none"}`);
  }
  return {
    addedFields,
    removedFields,
    changedFields,
    addedArtifactTypes: [...currentArtifactTypes].filter((item) => !previousArtifactTypes.has(item)),
    removedArtifactTypes: [...previousArtifactTypes].filter((item) => !currentArtifactTypes.has(item)),
    addedChecks: [...currentChecks].filter((item) => !previousChecks.has(item)),
    removedChecks: [...previousChecks].filter((item) => !currentChecks.has(item)),
    addedPromotionRequirements: [...currentPromotionRequirements].filter((item) => !previousPromotionRequirements.has(item)),
    removedPromotionRequirements: [...previousPromotionRequirements].filter((item) => !currentPromotionRequirements.has(item)),
    routingDelta: currentRoutingRules - previousRoutingRules,
    conditionalDelta: currentConditionalRules - previousConditionalRules,
    defaultRoutingChanged: changedDefaultRouting.length > 0,
    changedDefaultRouting,
    addedRoutingRules: currentRoutingRuleRows
      .filter((rule) => !previousRoutingRuleSet.has(`${rule.routeType}|${rule.sourceField}|${rule.matchValue}|${rule.targetValue}`))
      .map((rule) => `${rule.routeType}: ${rule.sourceField}=${rule.matchValue} -> ${rule.targetValue}`),
    removedRoutingRules: previousRoutingRuleRows
      .filter((rule) => !currentRoutingRuleSet.has(`${rule.routeType}|${rule.sourceField}|${rule.matchValue}|${rule.targetValue}`))
      .map((rule) => `${rule.routeType}: ${rule.sourceField}=${rule.matchValue} -> ${rule.targetValue}`),
    addedConditionalRules: currentConditionalRuleRows
      .filter((rule) => !previousConditionalRuleSet.has(`${rule.whenField}|${rule.equals}|${rule.targetField}|${rule.message}`))
      .map((rule) => `${rule.whenField}=${rule.equals || "*"} => ${rule.targetField}`),
    removedConditionalRules: previousConditionalRuleRows
      .filter((rule) => !currentConditionalRuleSet.has(`${rule.whenField}|${rule.equals}|${rule.targetField}|${rule.message}`))
      .map((rule) => `${rule.whenField}=${rule.equals || "*"} => ${rule.targetField}`),
  };
}

export default async function AdminTemplatesPage({ params, searchParams }: AdminTemplatesPageProps) {
  const routeParams = await params;
  const query = (await searchParams) ?? {};
  const templates = await listAdminTemplates();
  const selectedTemplateId = routeParams.templateId;
  const selectedVersion = routeParams.version;
  const compareVersionParam = typeof query.compareVersion === "string" ? query.compareVersion : undefined;
  const fallbackTemplate =
    templates.find((template) => template.status === "draft" && template.version.trim()) ??
    templates.find((template) => template.status === "published") ??
    templates[0];
  const selectedTemplate =
    templates.find((template) => template.id === selectedTemplateId && template.version === selectedVersion) ?? fallbackTemplate;
  const validation =
    query.validate === "1" && selectedTemplate
      ? await validateAdminTemplateDefinition(selectedTemplate.id, selectedTemplate.version)
      : null;
  const fieldRows = selectedTemplate ? [...schemaProperties(selectedTemplate.schema), ...Array.from({ length: 3 }, () => ({
    key: "",
    title: "",
    fieldType: "string",
    description: "",
    defaultValue: "",
    enumCsv: "",
    pattern: "",
    minLength: "",
    maxLength: "",
    order: "",
    required: false,
  }))] : [];
  const conditionalRuleRows = selectedTemplate ? [...schemaConditionalRules(selectedTemplate.schema), ...Array.from({ length: 2 }, () => ({
    order: "",
    whenField: "",
    equals: "",
    targetField: "",
    message: "",
  }))] : [];
  const routingState = selectedTemplate ? schemaRouting(selectedTemplate.schema) : { ownerTeam: "", workflowBinding: "", reviewersCsv: "", approversCsv: "", advancedJson: "{}" };
  const routingRuleRows = selectedTemplate ? [...schemaRoutingRuleRows(selectedTemplate.schema), ...Array.from({ length: 3 }, () => ({
    order: "",
    routeType: "owner_team_by_field",
    sourceField: "",
    matchValue: "",
    targetValue: "",
  }))] : [];
  const artifactTypes = selectedTemplate ? schemaStringList(selectedTemplate.schema, "expected_artifact_types") : [];
  const checkRequirements = selectedTemplate ? schemaStringList(selectedTemplate.schema, "check_requirements") : [];
  const promotionRequirements = selectedTemplate ? schemaStringList(selectedTemplate.schema, "promotion_requirements") : [];
  const comparisonCandidates =
    selectedTemplate
      ? templates
          .filter((template) => template.id === selectedTemplate.id && template.version && template.version !== selectedTemplate.version)
          .sort((left, right) => {
            const a = versionSortKey(left.version);
            const b = versionSortKey(right.version);
            return a[0] - b[0] || a[1] - b[1] || a[2] - b[2];
          })
      : [];
  const comparisonVersion =
    selectedTemplate
      ? comparisonCandidates.find((template) => template.version === compareVersionParam) ?? comparisonCandidates.at(-1)
      : undefined;
  const comparison = selectedTemplate && comparisonVersion ? compareTemplateSchemas(selectedTemplate.schema, comparisonVersion.schema) : null;
  const suggestedDraftVersion = selectedTemplate ? suggestNextDraftVersion(selectedTemplate.version) : "1.0.1";

  return (
    <PageShell
      {...appShellProps("/admin/templates", "Template Definition", "Draft authoring, validation, comparison, and publishing surface.")}
      contextPanel={
        <div className="space-y-5">
          <div>
            <SectionHeading title="Selected Version" />
            <p className="mt-2 text-sm text-slate-600">
              This page is scoped to one template version. Return to the catalog to switch templates or browse the wider registry.
            </p>
          </div>

          {selectedTemplate ? (
            <div className="space-y-3 rounded-xl border border-chrome bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-800">Validation and Publish</div>
                  <div className="text-xs text-slate-500">
                  {selectedTemplate.id}@{selectedTemplate.version}
                  </div>
                </div>
                <div
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    selectedTemplate.status === "published"
                      ? "bg-emerald-100 text-emerald-700"
                      : selectedTemplate.status === "draft"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-slate-200 text-slate-700"
                  }`}
                >
                  {selectedTemplate.status}
                </div>
              </div>
              <form action={validateTemplateDefinitionAction}>
                <input type="hidden" name="templateId" value={selectedTemplate.id} />
                <input type="hidden" name="version" value={selectedTemplate.version} />
                <Button label="Validate Selected Draft" tone="secondary" type="submit" />
              </form>
              <form action={publishTemplateVersionAction}>
                <input type="hidden" name="templateId" value={selectedTemplate.id} />
                <input type="hidden" name="version" value={selectedTemplate.version} />
                <Button label="Publish Selected Version" tone="primary" type="submit" />
              </form>
              <form action={deprecateTemplateVersionAction}>
                <input type="hidden" name="templateId" value={selectedTemplate.id} />
                <input type="hidden" name="version" value={selectedTemplate.version} />
                <Button label="Deprecate Selected Version" tone="secondary" type="submit" />
              </form>
              {selectedTemplate.status === "draft" ? (
                <form action={deleteTemplateVersionAction}>
                  <input type="hidden" name="templateId" value={selectedTemplate.id} />
                  <input type="hidden" name="version" value={selectedTemplate.version} />
                  <Button label="Delete Selected Draft" tone="secondary" type="submit" />
                </form>
              ) : null}
              {validation ? (
                <div className="space-y-3 rounded-lg border border-chrome bg-slate-50 p-3">
                  <div className={`text-sm font-semibold ${validation.valid ? "text-emerald-700" : "text-rose-700"}`}>
                  {validation.valid ? "Definition valid" : "Definition has issues"}
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs text-slate-600">
                    <div>Fields: {validation.preview.field_count}</div>
                    <div>Conditional Rules: {validation.preview.conditional_rule_count}</div>
                    <div>Routing Rules: {validation.preview.routing_rule_count}</div>
                    <div>Artifact Types: {validation.preview.artifact_type_count}</div>
                    <div>Checks: {validation.preview.check_requirement_count}</div>
                    <div>Promotion Rules: {validation.preview.promotion_requirement_count}</div>
                  </div>
                  <div className="space-y-2">
                    {validation.issues.length === 0 ? (
                      <div className="text-xs text-slate-600">No structural issues found.</div>
                    ) : (
                      validation.issues.map((issue) => (
                        <div key={`${issue.level}-${issue.path}-${issue.message}`} className="rounded-lg border border-chrome bg-white px-3 py-2 text-xs text-slate-700">
                          <div className="font-medium">
                            {issue.level.toUpperCase()} · {issue.path}
                          </div>
                          <div className="mt-1 text-slate-600">{issue.message}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              ) : null}
              {selectedTemplate.status !== "draft" ? (
                <form action={createTemplateVersionAction} className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
                  <input type="hidden" name="templateId" value={selectedTemplate.id} />
                  <input type="hidden" name="sourceVersion" value={selectedTemplate.version} />
                  <div className="text-sm font-semibold text-amber-800">Create Editable Draft</div>
                  <div className="text-sm text-amber-900">
                    {selectedTemplate.status === "published"
                      ? "Published versions are immutable. Start a new draft from this version to make changes."
                      : "Deprecated versions are immutable. Start a new draft from this version if you need to revise it."}
                  </div>
                  <label className="space-y-1 text-sm text-slate-700">
                    <span className="block text-xs font-medium text-slate-500">New Draft Version</span>
                    <input
                      name="version"
                      defaultValue={suggestedDraftVersion}
                      className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700"
                    />
                  </label>
                  <div className="flex justify-end">
                    <Button label="Create Editable Draft" tone="primary" type="submit" />
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}
          <a href="/admin/templates" className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">
            Back to Template Catalog
          </a>
        </div>
      }
    >
      <div className="space-y-4">
        <Tabs
          activeKey="templates"
          tabs={[
            { key: "org", label: "Organization", href: "/admin/org" },
            { key: "templates", label: "Templates", href: "/admin/templates" },
            { key: "policies", label: "Policies", href: "/admin/policies" },
            { key: "integrations", label: "Integrations", href: "/admin/integrations" },
          ]}
        />
        <div className="rounded-xl border border-chrome bg-white p-4 shadow-sm">
          <SectionHeading title="Definition Editor" />
          {selectedTemplate ? (
            <form action={saveTemplateDefinitionAction} className="mt-3 space-y-4">
                <input type="hidden" name="templateId" value={selectedTemplate.id} />
                <input type="hidden" name="version" value={selectedTemplate.version} />
                <input type="hidden" name="field_row_count" value={String(fieldRows.length)} />
                <input type="hidden" name="rule_row_count" value={String(conditionalRuleRows.length)} />
                <input type="hidden" name="routing_rule_row_count" value={String(routingRuleRows.length)} />
                <div className="grid gap-3 md:grid-cols-2">
                  {selectedTemplate.status !== "draft" ? (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-900 md:col-span-2">
                      This version is {selectedTemplate.status} and cannot be edited in place. Use
                      {" "}
                      <span className="font-semibold">Create Editable Draft</span>
                      {" "}
                      in the right panel to fork a writable draft from this version.
                    </div>
                  ) : null}
                  <label className="space-y-1 text-sm text-slate-700">
                    <span className="block text-xs font-medium text-slate-500">Template Name</span>
                    <input
                      name="name"
                      defaultValue={selectedTemplate.name}
                      disabled={selectedTemplate.status !== "draft"}
                      className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:cursor-not-allowed disabled:bg-slate-100"
                    />
                  </label>
                  <label className="space-y-1 text-sm text-slate-700">
                    <span className="block text-xs font-medium text-slate-500">Selected Version</span>
                    <input
                      value={`${selectedTemplate.id}@${selectedTemplate.version}`}
                      readOnly
                      disabled
                      className="w-full rounded-lg border border-chrome bg-slate-100 px-3 py-2 text-sm text-slate-700"
                    />
                  </label>
                </div>
                <label className="space-y-1 text-sm text-slate-700">
                  <span className="block text-xs font-medium text-slate-500">Description</span>
                  <textarea
                    name="description"
                    rows={2}
                    defaultValue={selectedTemplate.description}
                    disabled={selectedTemplate.status !== "draft"}
                    className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:cursor-not-allowed disabled:bg-slate-100"
                  />
                </label>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-medium text-slate-500">Field Designer</div>
                    <div className="mt-1 text-sm text-slate-600">Edit draft fields directly here instead of authoring the whole schema by hand.</div>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-chrome">
                    <table className="min-w-full divide-y divide-chrome text-sm">
                      <thead className="bg-slate-50 text-xs uppercase tracking-[0.08em] text-slate-500">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium">Use</th>
                          <th className="px-3 py-2 text-left font-medium">Order</th>
                          <th className="px-3 py-2 text-left font-medium">Key</th>
                          <th className="px-3 py-2 text-left font-medium">Title</th>
                          <th className="px-3 py-2 text-left font-medium">Type</th>
                          <th className="px-3 py-2 text-left font-medium">Required</th>
                          <th className="px-3 py-2 text-left font-medium">Default</th>
                          <th className="px-3 py-2 text-left font-medium">Enum</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-chrome bg-white">
                        {fieldRows.map((field, index) => (
                          <tr key={`field-row-${index}`}>
                            <td className="px-3 py-2 align-top">
                              <input type="checkbox" name={`field_enabled_${index}`} defaultChecked={Boolean(field.key)} disabled={selectedTemplate.status !== "draft"} className="mt-2 h-4 w-4 rounded border-chrome disabled:opacity-60" />
                            </td>
                            <td className="px-3 py-2 align-top">
                              <input name={`field_order_${index}`} defaultValue={field.order} disabled={selectedTemplate.status !== "draft"} className="w-16 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                            <td className="px-3 py-2 align-top">
                              <input name={`field_key_${index}`} defaultValue={field.key} disabled={selectedTemplate.status !== "draft"} className="w-36 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                            <td className="px-3 py-2 align-top">
                              <div className="space-y-2">
                                <input name={`field_title_${index}`} defaultValue={field.title} disabled={selectedTemplate.status !== "draft"} className="w-44 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                                <input name={`field_description_${index}`} defaultValue={field.description} placeholder="Description" disabled={selectedTemplate.status !== "draft"} className="w-56 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                              </div>
                            </td>
                            <td className="px-3 py-2 align-top">
                              <select name={`field_type_${index}`} defaultValue={field.fieldType} disabled={selectedTemplate.status !== "draft"} className="w-28 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100">
                                <option value="string">string</option>
                                <option value="number">number</option>
                                <option value="integer">integer</option>
                                <option value="boolean">boolean</option>
                              </select>
                              <div className="mt-2 grid grid-cols-2 gap-2">
                                <input name={`field_min_length_${index}`} defaultValue={field.minLength} placeholder="Min" disabled={selectedTemplate.status !== "draft"} className="w-20 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-xs text-slate-700 disabled:bg-slate-100" />
                                <input name={`field_max_length_${index}`} defaultValue={field.maxLength} placeholder="Max" disabled={selectedTemplate.status !== "draft"} className="w-20 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-xs text-slate-700 disabled:bg-slate-100" />
                              </div>
                              <input name={`field_pattern_${index}`} defaultValue={field.pattern} placeholder="Pattern" disabled={selectedTemplate.status !== "draft"} className="mt-2 w-28 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-xs text-slate-700 disabled:bg-slate-100" />
                            </td>
                            <td className="px-3 py-2 align-top">
                              <input type="checkbox" name={`field_required_${index}`} defaultChecked={field.required} disabled={selectedTemplate.status !== "draft"} className="mt-2 h-4 w-4 rounded border-chrome disabled:opacity-60" />
                            </td>
                            <td className="px-3 py-2 align-top">
                              <input name={`field_default_${index}`} defaultValue={field.defaultValue} disabled={selectedTemplate.status !== "draft"} className="w-28 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                            <td className="px-3 py-2 align-top">
                              <input name={`field_enum_${index}`} defaultValue={field.enumCsv} placeholder="a, b, c" disabled={selectedTemplate.status !== "draft"} className="w-44 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-medium text-slate-500">Routing Designer</div>
                    <div className="mt-1 text-sm text-slate-600">Set default ownership, workflow, review, and promotion routing without editing JSON for the common path.</div>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    <label className="space-y-1 text-sm text-slate-700">
                      <span className="block text-xs font-medium text-slate-500">Owner Team</span>
                      <input name="routing_owner_team" defaultValue={routingState.ownerTeam} disabled={selectedTemplate.status !== "draft"} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                    </label>
                    <label className="space-y-1 text-sm text-slate-700">
                      <span className="block text-xs font-medium text-slate-500">Workflow Binding</span>
                      <input name="routing_workflow_binding" defaultValue={routingState.workflowBinding} disabled={selectedTemplate.status !== "draft"} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                    </label>
                    <label className="space-y-1 text-sm text-slate-700">
                      <span className="block text-xs font-medium text-slate-500">Reviewers</span>
                      <input name="routing_reviewers" defaultValue={routingState.reviewersCsv} placeholder="reviewer_a, reviewer_b" disabled={selectedTemplate.status !== "draft"} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                    </label>
                    <label className="space-y-1 text-sm text-slate-700">
                      <span className="block text-xs font-medium text-slate-500">Promotion Approvers</span>
                      <input name="routing_promotion_approvers" defaultValue={routingState.approversCsv} placeholder="ops_a, ops_b" disabled={selectedTemplate.status !== "draft"} className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                    </label>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-medium text-slate-500">Routing Rules By Field</div>
                    <div className="mt-1 text-sm text-slate-600">Define field-driven routing without falling back to raw JSON for common mapping cases. Disable a row to remove it on the next save.</div>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-chrome">
                    <table className="min-w-full divide-y divide-chrome text-sm">
                      <thead className="bg-slate-50 text-xs uppercase tracking-[0.08em] text-slate-500">
                        <tr>
                          <th className="px-3 py-2 text-left font-medium">Use</th>
                          <th className="px-3 py-2 text-left font-medium">Order</th>
                          <th className="px-3 py-2 text-left font-medium">Route Type</th>
                          <th className="px-3 py-2 text-left font-medium">Source Field</th>
                          <th className="px-3 py-2 text-left font-medium">Match Value</th>
                          <th className="px-3 py-2 text-left font-medium">Target Value</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-chrome bg-white">
                        {routingRuleRows.map((row, index) => (
                          <tr key={`routing-rule-${index}`}>
                            <td className="px-3 py-2">
                              <input type="checkbox" name={`routing_rule_enabled_${index}`} defaultChecked={Boolean(row.sourceField && row.matchValue && row.targetValue)} disabled={selectedTemplate.status !== "draft"} className="h-4 w-4 rounded border-chrome disabled:opacity-60" />
                            </td>
                            <td className="px-3 py-2">
                              <input name={`routing_rule_order_${index}`} defaultValue={row.order} disabled={selectedTemplate.status !== "draft"} className="w-16 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                            <td className="px-3 py-2">
                              <select name={`routing_rule_type_${index}`} defaultValue={row.routeType} disabled={selectedTemplate.status !== "draft"} className="w-48 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100">
                                <option value="owner_team_by_field">owner_team_by_field</option>
                                <option value="workflow_binding_by_field">workflow_binding_by_field</option>
                                <option value="reviewers_by_field">reviewers_by_field</option>
                                <option value="promotion_approvers_by_field">promotion_approvers_by_field</option>
                              </select>
                            </td>
                            <td className="px-3 py-2">
                              <input name={`routing_rule_source_field_${index}`} defaultValue={row.sourceField} disabled={selectedTemplate.status !== "draft"} className="w-40 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                            <td className="px-3 py-2">
                              <input name={`routing_rule_match_value_${index}`} defaultValue={row.matchValue} disabled={selectedTemplate.status !== "draft"} className="w-40 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                            <td className="px-3 py-2">
                              <input name={`routing_rule_target_value_${index}`} defaultValue={row.targetValue} disabled={selectedTemplate.status !== "draft"} className="w-56 rounded-lg border border-chrome bg-slate-50 px-2 py-1.5 text-sm text-slate-700 disabled:bg-slate-100" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs font-medium text-slate-500">Conditional Rules</div>
                    <div className="mt-1 text-sm text-slate-600">Define when one field becomes required based on another field’s value. Disable a row to remove it on the next save.</div>
                  </div>
                  <div className="space-y-2">
                    {conditionalRuleRows.map((rule, index) => (
                      <div key={`rule-row-${index}`} className="grid gap-2 rounded-lg border border-chrome bg-slate-50 p-3 md:grid-cols-[0.55fr_0.65fr_1fr_1fr_1fr_1.2fr]">
                        <label className="flex items-center gap-2 text-xs text-slate-600">
                          <input type="checkbox" name={`rule_enabled_${index}`} defaultChecked={Boolean(rule.whenField && rule.targetField)} disabled={selectedTemplate.status !== "draft"} className="h-4 w-4 rounded border-chrome disabled:opacity-60" />
                          Use
                        </label>
                        <input name={`rule_order_${index}`} defaultValue={rule.order} placeholder="Order" disabled={selectedTemplate.status !== "draft"} className="rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                        <input name={`rule_when_field_${index}`} defaultValue={rule.whenField} placeholder="When field" disabled={selectedTemplate.status !== "draft"} className="rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                        <input name={`rule_equals_${index}`} defaultValue={rule.equals} placeholder="Equals value" disabled={selectedTemplate.status !== "draft"} className="rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                        <input name={`rule_target_field_${index}`} defaultValue={rule.targetField} placeholder="Require field" disabled={selectedTemplate.status !== "draft"} className="rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                        <input name={`rule_message_${index}`} defaultValue={rule.message} placeholder="Validation message" disabled={selectedTemplate.status !== "draft"} className="rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100" />
                      </div>
                    ))}
                  </div>
                </div>
                <label className="space-y-1 text-sm text-slate-700">
                  <span className="block text-xs font-medium text-slate-500">Advanced Routing JSON</span>
                  <textarea
                    name="routing_json"
                    rows={10}
                    defaultValue={routingState.advancedJson}
                    disabled={selectedTemplate.status !== "draft"}
                    className="w-full rounded-lg border border-chrome bg-slate-950 px-3 py-3 font-mono text-xs text-slate-100 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-700"
                  />
                </label>
                <div className="grid gap-4 md:grid-cols-3">
                  <label className="space-y-1 text-sm text-slate-700">
                    <span className="block text-xs font-medium text-slate-500">Expected Artifact Types</span>
                    <textarea
                      name="expected_artifact_types"
                      rows={6}
                      defaultValue={artifactTypes.join(", ")}
                      placeholder="doc, rubric, deployment_bundle"
                      disabled={selectedTemplate.status !== "draft"}
                      className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100"
                    />
                  </label>
                  <label className="space-y-1 text-sm text-slate-700">
                    <span className="block text-xs font-medium text-slate-500">Check Requirements</span>
                    <textarea
                      name="check_requirements"
                      rows={6}
                      defaultValue={checkRequirements.join("\n")}
                      placeholder={"policy_pack\nsafety_review"}
                      disabled={selectedTemplate.status !== "draft"}
                      className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100"
                    />
                  </label>
                  <label className="space-y-1 text-sm text-slate-700">
                    <span className="block text-xs font-medium text-slate-500">Promotion Requirements</span>
                    <textarea
                      name="promotion_requirements"
                      rows={6}
                      defaultValue={promotionRequirements.join("\n")}
                      placeholder={"approval:ops\napproval:security"}
                      disabled={selectedTemplate.status !== "draft"}
                      className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:bg-slate-100"
                    />
                  </label>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                    <div className="text-xs font-medium text-slate-500">Preview</div>
                    <div className="mt-2">Fields: {validation?.preview.field_count ?? schemaFieldCount(selectedTemplate.schema)}</div>
                    <div>Required: {(validation?.preview.required_fields ?? schemaRequiredFields(selectedTemplate.schema)).join(", ") || "None"}</div>
                    <div>Artifacts: {artifactTypes.length}</div>
                    <div>Checks: {checkRequirements.length}</div>
                    <div>Promotion Rules: {promotionRequirements.length}</div>
                  </div>
                  <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                    <div className="text-xs font-medium text-slate-500">Definition State</div>
                    <div className="mt-2">
                      {selectedTemplate.status === "draft"
                        ? "Draft versions can be edited, previewed, and validated in this surface."
                        : "Published and deprecated versions are immutable. Create a new draft version to modify them."}
                    </div>
                  </div>
                </div>
                <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                  <div className="text-xs font-medium text-slate-500">Intake Preview</div>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    {schemaProperties(selectedTemplate.schema)
                      .filter((field) => field.key)
                      .map((field) => (
                        <div key={`preview-${field.key}`} className="rounded-lg border border-chrome bg-white px-3 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <div className="font-medium text-slate-900">{field.title}</div>
                            <div className="text-xs uppercase tracking-[0.08em] text-slate-500">{field.fieldType}</div>
                          </div>
                          <div className="mt-1 text-xs text-slate-500">{field.key}</div>
                          {field.description ? <div className="mt-2 text-sm text-slate-600">{field.description}</div> : null}
                          <div className="mt-3 flex flex-wrap gap-2 text-xs">
                            {field.required ? <span className="rounded-full bg-amber-100 px-2 py-1 font-medium text-amber-700">Required</span> : <span className="rounded-full bg-slate-200 px-2 py-1 font-medium text-slate-700">Optional</span>}
                            {field.defaultValue ? <span className="rounded-full bg-emerald-100 px-2 py-1 font-medium text-emerald-700">Default: {field.defaultValue}</span> : null}
                            {field.enumCsv ? <span className="rounded-full bg-sky-100 px-2 py-1 font-medium text-sky-700">Enum</span> : null}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                    <div className="text-xs font-medium text-slate-500">Expected Artifacts</div>
                    <div className="mt-2 space-y-2">
                      {artifactTypes.length ? artifactTypes.map((item) => <div key={item} className="rounded-lg bg-white px-3 py-2">{item}</div>) : <div className="text-slate-500">None configured.</div>}
                    </div>
                  </div>
                  <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                    <div className="text-xs font-medium text-slate-500">Check Requirements</div>
                    <div className="mt-2 space-y-2">
                      {checkRequirements.length ? checkRequirements.map((item) => <div key={item} className="rounded-lg bg-white px-3 py-2">{item}</div>) : <div className="text-slate-500">None configured.</div>}
                    </div>
                  </div>
                  <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                    <div className="text-xs font-medium text-slate-500">Promotion Requirements</div>
                    <div className="mt-2 space-y-2">
                      {promotionRequirements.length ? promotionRequirements.map((item) => <div key={item} className="rounded-lg bg-white px-3 py-2">{item}</div>) : <div className="text-slate-500">None configured.</div>}
                    </div>
                  </div>
                </div>
                {comparison && comparisonVersion ? (
                  <div className="rounded-lg border border-chrome bg-slate-50 px-3 py-3 text-sm text-slate-700">
                    <div className="text-xs font-medium text-slate-500">Version Comparison</div>
                    <div className="mt-2 space-y-1">
                      <div className="block text-xs font-medium text-slate-500">Compare Against</div>
                      <div className="flex flex-wrap gap-2">
                        {comparisonCandidates.map((template) => (
                          <a
                            key={`${template.id}@${template.version}`}
                    href={`/admin/templates/${encodeURIComponent(selectedTemplate.id)}/${encodeURIComponent(selectedTemplate.version)}?compareVersion=${encodeURIComponent(template.version)}`}
                            className={`rounded-lg border px-3 py-2 text-sm ${
                              template.version === comparisonVersion.version
                                ? "border-accent bg-accent text-white"
                                : "border-chrome bg-white text-slate-700"
                            }`}
                          >
                            {template.version} ({template.status})
                          </a>
                        ))}
                      </div>
                    </div>
                    <div className="mt-3">Comparing {selectedTemplate.version} against {comparisonVersion.version}</div>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Added Fields</div>
                        <div className="mt-2">{comparison.addedFields.length ? comparison.addedFields.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Removed Fields</div>
                        <div className="mt-2">{comparison.removedFields.length ? comparison.removedFields.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3 md:col-span-2">
                        <div className="text-xs font-medium text-slate-500">Changed Fields</div>
                        <div className="mt-2 space-y-2">
                          {comparison.changedFields.length ? (
                            comparison.changedFields.map((field) => (
                              <div key={field.key} className="rounded-lg border border-chrome px-3 py-2">
                                <div className="font-medium text-slate-900">{field.key}</div>
                                <div className="mt-1 text-xs text-slate-600">{field.changes.join(" · ")}</div>
                              </div>
                            ))
                          ) : (
                            <div>None</div>
                          )}
                        </div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Routing Rule Delta</div>
                        <div className="mt-2">{comparison.routingDelta >= 0 ? "+" : ""}{comparison.routingDelta}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Conditional Rule Delta</div>
                        <div className="mt-2">{comparison.conditionalDelta >= 0 ? "+" : ""}{comparison.conditionalDelta}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Added Artifact Types</div>
                        <div className="mt-2">{comparison.addedArtifactTypes.length ? comparison.addedArtifactTypes.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Removed Artifact Types</div>
                        <div className="mt-2">{comparison.removedArtifactTypes.length ? comparison.removedArtifactTypes.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Added Checks</div>
                        <div className="mt-2">{comparison.addedChecks.length ? comparison.addedChecks.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Removed Checks</div>
                        <div className="mt-2">{comparison.removedChecks.length ? comparison.removedChecks.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Added Promotion Rules</div>
                        <div className="mt-2">{comparison.addedPromotionRequirements.length ? comparison.addedPromotionRequirements.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Removed Promotion Rules</div>
                        <div className="mt-2">{comparison.removedPromotionRequirements.length ? comparison.removedPromotionRequirements.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3 md:col-span-2">
                        <div className="text-xs font-medium text-slate-500">Default Routing Changed</div>
                        <div className="mt-2">{comparison.defaultRoutingChanged ? comparison.changedDefaultRouting.join(" · ") : "No"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Added Routing Rules</div>
                        <div className="mt-2">{comparison.addedRoutingRules.length ? comparison.addedRoutingRules.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Removed Routing Rules</div>
                        <div className="mt-2">{comparison.removedRoutingRules.length ? comparison.removedRoutingRules.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Added Conditional Rules</div>
                        <div className="mt-2">{comparison.addedConditionalRules.length ? comparison.addedConditionalRules.join(", ") : "None"}</div>
                      </div>
                      <div className="rounded-lg bg-white px-3 py-3">
                        <div className="text-xs font-medium text-slate-500">Removed Conditional Rules</div>
                        <div className="mt-2">{comparison.removedConditionalRules.length ? comparison.removedConditionalRules.join(", ") : "None"}</div>
                      </div>
                    </div>
                  </div>
                ) : null}
                <div className="flex justify-end gap-2">
                  <a
                    href={`/admin/templates/${encodeURIComponent(selectedTemplate.id)}/${encodeURIComponent(selectedTemplate.version)}?validate=1`}
                    className="inline-flex items-center rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700"
                  >
                    Preview Definition
                  </a>
                  <Button label="Save Draft" tone="primary" type="submit" disabled={selectedTemplate.status !== "draft"} />
                </div>
              </form>
            ) : (
              <div className="mt-3 text-sm text-slate-600">Select a template version from the catalog to inspect or author it.</div>
            )}
        </div>
      </div>
    </PageShell>
  );
}
