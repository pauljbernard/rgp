import { listTemplates } from "@/lib/server-api";
import { DataTable, PageShell, SectionHeading, appShellProps } from "../../../components/ui-helpers";
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
  searchParams: Promise<{
    template?: string;
    error?: string;
    choose_template?: string;
    template_query?: string;
    template_sort?: string;
    template_dir?: string;
    template_page?: string;
  }>;
}) {
  const templates = await listTemplates();
  const params = await searchParams;
  const selectedKey = typeof params.template === "string" ? params.template : "";
  const errorMessage = typeof params.error === "string" && params.error ? params.error : "";
  const templateQuery = typeof params.template_query === "string" ? params.template_query.trim() : "";
  const templateSort = params.template_sort === "updated_at" || params.template_sort === "id" || params.template_sort === "version" ? params.template_sort : "name";
  const templateDir = params.template_dir === "desc" ? "desc" : "asc";
  const templatePage = Math.max(1, Number.parseInt(typeof params.template_page === "string" ? params.template_page : "1", 10) || 1);
  const selectedTemplate = templates.find((template) => `${template.id}@${template.version}` === selectedKey);
  const showTemplatePicker = !selectedTemplate || params.choose_template === "1";
  const filteredTemplates = templates
    .filter((template) => {
      if (!templateQuery) {
        return true;
      }
      const haystack = `${template.id} ${template.name} ${template.description} ${template.version}`.toLowerCase();
      return haystack.includes(templateQuery.toLowerCase());
    })
    .sort((left, right) => {
      const direction = templateDir === "asc" ? 1 : -1;
      const leftValue =
        templateSort === "updated_at"
          ? left.updated_at
          : templateSort === "version"
            ? left.version
            : templateSort === "id"
              ? left.id
              : left.name;
      const rightValue =
        templateSort === "updated_at"
          ? right.updated_at
          : templateSort === "version"
            ? right.version
            : templateSort === "id"
              ? right.id
              : right.name;
      return leftValue.localeCompare(rightValue) * direction;
    });
  const templatePageSize = 10;
  const templateTotalPages = Math.max(1, Math.ceil(filteredTemplates.length / templatePageSize));
  const normalizedTemplatePage = Math.min(templatePage, templateTotalPages);
  const pagedTemplates = filteredTemplates.slice((normalizedTemplatePage - 1) * templatePageSize, normalizedTemplatePage * templatePageSize);
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
  const buildTemplatePickerHref = (overrides: Record<string, string | number | undefined>) => {
    const next = new URLSearchParams();
    if (selectedKey) {
      next.set("template", selectedKey);
    }
    next.set("choose_template", "1");
    if (templateQuery) {
      next.set("template_query", templateQuery);
    }
    next.set("template_sort", templateSort);
    next.set("template_dir", templateDir);
    next.set("template_page", String(normalizedTemplatePage));
    for (const [key, value] of Object.entries(overrides)) {
      if (value === undefined || value === "") {
        next.delete(key);
      } else {
        next.set(key, String(value));
      }
    }
    return `/requests/new?${next.toString()}`;
  };
  const nextSortHref = (column: "name" | "id" | "version" | "updated_at") =>
    buildTemplatePickerHref({
      template_sort: column,
      template_dir: templateSort === column && templateDir === "asc" ? "desc" : "asc",
      template_page: 1
    });

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
              <div className="flex items-center gap-2">
                {selectedTemplate ? (
                  <a
                    href={`/requests/new?template=${encodeURIComponent(`${selectedTemplate.id}@${selectedTemplate.version}`)}`}
                    className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700"
                  >
                    Back to Form
                  </a>
                ) : null}
                <a href="/requests" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
                  Close
                </a>
              </div>
            </div>
            {errorMessage ? (
              <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {errorMessage}
              </div>
            ) : null}
            <div className="mt-6 rounded-xl border border-chrome bg-white p-5 shadow-sm">
              <form method="get" className="grid gap-4 border-b border-chrome pb-4 md:grid-cols-[minmax(0,1fr)_180px_120px]">
                {selectedKey ? <input type="hidden" name="template" value={selectedKey} /> : null}
                <input type="hidden" name="choose_template" value="1" />
                <label className="grid gap-2 text-sm">
                  <span className="font-medium text-slate-700">Search Templates</span>
                  <input
                    name="template_query"
                    defaultValue={templateQuery}
                    className="rounded-md border border-chrome bg-white px-3 py-2"
                    placeholder="Search by name, id, description, or version"
                  />
                </label>
                <label className="grid gap-2 text-sm">
                  <span className="font-medium text-slate-700">Sort By</span>
                  <select name="template_sort" defaultValue={templateSort} className="rounded-md border border-chrome bg-white px-3 py-2">
                    <option value="name">Name</option>
                    <option value="id">Template ID</option>
                    <option value="version">Version</option>
                    <option value="updated_at">Updated</option>
                  </select>
                </label>
                <label className="grid gap-2 text-sm">
                  <span className="font-medium text-slate-700">Direction</span>
                  <select name="template_dir" defaultValue={templateDir} className="rounded-md border border-chrome bg-white px-3 py-2">
                    <option value="asc">Ascending</option>
                    <option value="desc">Descending</option>
                  </select>
                </label>
                <div className="flex items-end gap-2 md:col-span-3">
                  <button type="submit" className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white">
                    Apply
                  </button>
                  <a
                    href={selectedKey ? `/requests/new?template=${encodeURIComponent(selectedKey)}&choose_template=1` : "/requests/new?choose_template=1"}
                    className="rounded-md border border-chrome bg-white px-4 py-2 text-sm font-medium text-slate-700"
                  >
                    Reset
                  </a>
                </div>
              </form>
              <div className="mt-5">
                <DataTable
                  columns={[
                    {
                      key: "name",
                      header: "Template",
                      render: (template) => (
                        <div className="grid gap-1">
                          <a
                            href={`/requests/new?template=${encodeURIComponent(`${template.id}@${template.version}`)}`}
                            className="font-medium text-accent hover:underline"
                          >
                            {template.name}
                          </a>
                          <span className="text-xs text-slate-500">{template.description}</span>
                        </div>
                      ),
                      sortHref: nextSortHref("name"),
                      sortDirection: templateSort === "name" ? templateDir : undefined
                    },
                    {
                      key: "id",
                      header: "Template ID",
                      render: (template) => <span className="font-mono text-xs text-slate-600">{template.id}</span>,
                      sortHref: nextSortHref("id"),
                      sortDirection: templateSort === "id" ? templateDir : undefined
                    },
                    {
                      key: "version",
                      header: "Version",
                      render: (template) => <span className="text-sm text-slate-700">{template.version}</span>,
                      sortHref: nextSortHref("version"),
                      sortDirection: templateSort === "version" ? templateDir : undefined
                    },
                    {
                      key: "updated",
                      header: "Updated",
                      render: (template) => <span className="text-sm text-slate-700">{new Date(template.updated_at).toLocaleDateString()}</span>,
                      sortHref: nextSortHref("updated_at"),
                      sortDirection: templateSort === "updated_at" ? templateDir : undefined
                    },
                    {
                      key: "action",
                      header: "Action",
                      render: (template) => (
                        <a
                          href={`/requests/new?template=${encodeURIComponent(`${template.id}@${template.version}`)}`}
                          className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Select
                        </a>
                      )
                    }
                  ]}
                  data={pagedTemplates}
                  emptyMessage="No templates match the current search and filter criteria."
                  pagination={{
                    page: normalizedTemplatePage,
                    pageSize: templatePageSize,
                    totalCount: filteredTemplates.length,
                    totalPages: templateTotalPages,
                    previousHref: normalizedTemplatePage > 1 ? buildTemplatePickerHref({ template_page: normalizedTemplatePage - 1 }) : undefined,
                    nextHref: normalizedTemplatePage < templateTotalPages ? buildTemplatePickerHref({ template_page: normalizedTemplatePage + 1 }) : undefined
                  }}
                />
              </div>
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
