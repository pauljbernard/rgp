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
  searchParams: Promise<{ template?: string; error?: string; choose_template?: string }>;
}) {
  const templates = await listTemplates();
  const params = await searchParams;
  const selectedKey = typeof params.template === "string" ? params.template : "";
  const errorMessage = typeof params.error === "string" && params.error ? params.error : "";
  const selectedTemplate = templates.find((template) => `${template.id}@${template.version}` === selectedKey);
  const showTemplatePicker = !selectedTemplate || params.choose_template === "1";
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
          <SectionHeading title="Flow" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Select a published template first. New requests are created as drafts and then submitted from the request detail page.
          </div>
          <SectionHeading title="Schema" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {selectedTemplate
              ? `${fields.length} template fields · ${requiredFields.size} required on submit · ${conditionalRules.length} conditional rules`
              : "Choose a template to inspect its intake schema and governance rules."}
          </div>
        </div>
      }
    >
      {showTemplatePicker ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/35 px-4">
          <div className="w-full max-w-4xl rounded-xl border border-chrome bg-panel p-6 shadow-panel">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Select Request Template</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Start the request by choosing the published template that defines its intake, routing, and governance rules.
                </p>
              </div>
              {selectedTemplate ? (
                <a
                  href={`/requests/new?template=${encodeURIComponent(`${selectedTemplate.id}@${selectedTemplate.version}`)}`}
                  className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700"
                >
                  Back to Form
                </a>
              ) : null}
            </div>
            {errorMessage ? (
              <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {errorMessage}
              </div>
            ) : null}
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {templates.map((template) => (
                <a
                  key={`${template.id}@${template.version}`}
                  href={`/requests/new?template=${encodeURIComponent(`${template.id}@${template.version}`)}`}
                  className="rounded-xl border border-chrome bg-white p-5 text-left transition hover:border-slate-400 hover:shadow-panel"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-base font-semibold text-slate-900">{template.name}</div>
                      <div className="mt-1 text-sm text-slate-500">
                        {template.id} v{template.version}
                      </div>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium uppercase tracking-wide text-slate-600">
                      {template.status}
                    </span>
                  </div>
                  {template.description ? <p className="mt-3 text-sm text-slate-700">{template.description}</p> : null}
                  <div className="mt-4 text-sm font-medium text-accent">Use this template</div>
                </a>
              ))}
            </div>
          </div>
        </div>
      ) : null}
      {!showTemplatePicker && selectedTemplate ? (
        <div className="rounded-xl border border-chrome bg-panel p-6 shadow-panel">
          {errorMessage ? (
            <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {errorMessage}
            </div>
          ) : null}
          <div className="mb-6 flex items-start justify-between gap-4 rounded-lg border border-chrome bg-slate-50 px-4 py-3">
            <div>
              <div className="text-sm font-medium text-slate-700">Selected Template</div>
              <div className="mt-1 text-sm text-slate-600">
                {selectedTemplate.name} v{selectedTemplate.version}
              </div>
            </div>
            <a
              href={`/requests/new?template=${encodeURIComponent(`${selectedTemplate.id}@${selectedTemplate.version}`)}&choose_template=1`}
              className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700"
            >
              Choose Different Template
            </a>
          </div>
          <form action={createRequestAction} className="grid gap-4">
            <input type="hidden" name="templateId" value={selectedTemplate.id} />
            <input type="hidden" name="templateVersion" value={selectedTemplate.version} />
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
                Bound to {selectedTemplate.name} v{selectedTemplate.version}
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
      ) : null}
    </PageShell>
  );
}
