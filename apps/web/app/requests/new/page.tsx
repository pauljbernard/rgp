import { listTemplates } from "@/lib/server-api";
import { PageShell, SectionHeading, appShellProps } from "../../../components/ui-helpers";
import { createRequestAction } from "./actions";

type TemplateFieldSchema = {
  type?: string;
  title?: string;
  enum?: string[];
  default?: string;
  description?: string;
  min_length?: number;
  max_length?: number;
  pattern?: string;
};

type ConditionalRequiredRule = {
  when?: {
    field?: string;
    equals?: string;
    in?: string[];
  };
  field?: string;
  message?: string;
};

export default async function NewRequestPage({
  searchParams
}: {
  searchParams: Promise<{ template?: string; error?: string }>;
}) {
  const templates = await listTemplates();
  const params = await searchParams;
  const selectedKey = params.template ?? (templates[0] ? `${templates[0].id}@${templates[0].version}` : "");
  const errorMessage = typeof params.error === "string" && params.error ? params.error : "";
  const selectedTemplate =
    templates.find((template) => `${template.id}@${template.version}` === selectedKey) ??
    templates[0];
  const schema = (selectedTemplate?.schema ?? {}) as {
    required?: string[];
    properties?: Record<string, TemplateFieldSchema>;
    conditional_required?: ConditionalRequiredRule[];
  };
  const requiredFields = new Set(schema.required ?? []);
  const conditionalRules = schema.conditional_required ?? [];
  const fields = Object.entries(schema.properties ?? {});
  const conditionalNotesByField = conditionalRules.reduce<Record<string, string[]>>((accumulator, rule) => {
    if (!rule.field) {
      return accumulator;
    }
    const trigger = rule.when?.equals
      ? `${rule.when.field} = ${rule.when.equals}`
      : rule.when?.in?.length
        ? `${rule.when.field} in ${rule.when.in.join(", ")}`
        : "matching requests";
    accumulator[rule.field] = [...(accumulator[rule.field] ?? []), `Required when ${trigger}`];
    return accumulator;
  }, {});

  return (
    <PageShell
      {...appShellProps("/requests", "Create Request", "Start a governed request with a minimal intake form.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Template" />
          <form className="grid gap-2" method="get">
            <select
              name="template"
              defaultValue={selectedTemplate ? `${selectedTemplate.id}@${selectedTemplate.version}` : ""}
              className="rounded-md border border-chrome bg-white px-3 py-2 text-sm"
            >
              {templates.map((template) => (
                <option key={`${template.id}@${template.version}`} value={`${template.id}@${template.version}`}>
                  {template.name} v{template.version}
                </option>
              ))}
            </select>
            <button type="submit" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
              Load Template
            </button>
          </form>
          <SectionHeading title="Flow" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            New requests are created as drafts and then submitted from the request detail page.
          </div>
          <SectionHeading title="Schema" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {fields.length} template fields · {requiredFields.size} required on submit · {conditionalRules.length} conditional rules
          </div>
        </div>
      }
    >
      <div className="rounded-xl border border-chrome bg-panel p-6 shadow-panel">
        {errorMessage ? (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {errorMessage}
          </div>
        ) : null}
        <form action={createRequestAction} className="grid gap-4">
          <input type="hidden" name="templateId" value={selectedTemplate?.id ?? ""} />
          <input type="hidden" name="templateVersion" value={selectedTemplate?.version ?? ""} />
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-700">Title</span>
            <input name="title" required className="rounded-md border border-chrome bg-white px-3 py-2" placeholder="Generate Grade 6 Geometry Unit" />
          </label>
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-700">Summary</span>
            <textarea name="summary" required rows={4} className="rounded-md border border-chrome bg-white px-3 py-2" placeholder="Describe the governed work that needs to happen." />
          </label>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-2 text-sm">
              <span className="font-medium text-slate-700">Priority</span>
              <select name="priority" defaultValue="medium" className="rounded-md border border-chrome bg-white px-3 py-2">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </label>
            <div className="rounded-md border border-dashed border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Bound to {selectedTemplate?.name ?? "No template selected"} v{selectedTemplate?.version ?? ""}
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {fields.map(([fieldName, fieldSchema]) => (
              <label key={fieldName} className="grid gap-2 text-sm">
                <span className="font-medium text-slate-700">
                  {fieldSchema.title ?? fieldName}
                  {requiredFields.has(fieldName) ? " *" : ""}
                </span>
                {fieldSchema.description ? <span className="text-xs text-slate-500">{fieldSchema.description}</span> : null}
                {conditionalNotesByField[fieldName]?.map((note) => (
                  <span key={`${fieldName}-${note}`} className="text-xs text-amber-700">
                    {note}
                  </span>
                ))}
                {fieldSchema.enum?.length ? (
                  <select
                    name={`input_${fieldName}`}
                    defaultValue={fieldSchema.default ?? ""}
                    className="rounded-md border border-chrome bg-white px-3 py-2"
                  >
                    {!requiredFields.has(fieldName) ? <option value="">Select an option</option> : null}
                    {fieldSchema.enum.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    name={`input_${fieldName}`}
                    defaultValue={fieldSchema.default ?? ""}
                    className="rounded-md border border-chrome bg-white px-3 py-2"
                    placeholder={fieldSchema.title ?? fieldName}
                  />
                )}
              </label>
            ))}
          </div>
          <div className="flex justify-end">
            <button type="submit" className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white">
              Create Draft
            </button>
          </div>
        </form>
      </div>
    </PageShell>
  );
}
