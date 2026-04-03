import clsx from "clsx";
import React, { type ReactNode } from "react";

type NavItem = {
  label: string;
  href: string;
};

type LinkRenderer = (item: NavItem, className: string, isActive: boolean) => ReactNode;

type TableColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  sortHref?: string;
  sortDirection?: "asc" | "desc";
};

type SelectionConfig<T> = {
  rowKey: (row: T) => string;
  selectedKeys: string[];
  toggleHref: (key: string) => string;
  clearHref?: string;
};

type ColumnVisibilityOption = {
  key: string;
  label: string;
  visible: boolean;
  toggleHref: string;
};

type FilterItem = {
  label: string;
  value: string;
  href?: string;
  active?: boolean;
};

type PaginationConfig = {
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  previousHref?: string;
  nextHref?: string;
};

type TimeSeriesDatum = {
  label: string;
  value: number;
};

type TimeSeriesChartSeries = {
  key: string;
  label: string;
  color: string;
  points: TimeSeriesDatum[];
};

export function PageShell({
  title,
  subtitle,
  navItems,
  currentPath,
  contextPanel,
  headerActions,
  children,
  renderNavItem
}: {
  title: string;
  subtitle: string;
  navItems: readonly NavItem[];
  currentPath: string;
  contextPanel?: ReactNode;
  headerActions?: ReactNode;
  children: ReactNode;
  renderNavItem?: LinkRenderer;
}) {
  return (
    <div className="min-h-screen bg-slate-100">
      <div className="grid min-h-screen grid-cols-1 xl:grid-cols-[240px_minmax(0,1fr)_300px]">
        <aside className="border-b border-chrome bg-white px-5 py-6 text-slate-900 xl:border-b-0 xl:border-r">
          <div className="mb-8">
            <div className="text-[11px] font-semibold text-slate-500">RGP</div>
            <div className="mt-2 text-lg font-semibold">Governed Work OS</div>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = currentPath === item.href || currentPath.startsWith(`${item.href}/`);
              const className = clsx(
                "block rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive ? "bg-slate-200 text-slate-950" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
              );
              if (renderNavItem) {
                return <div key={item.href}>{renderNavItem(item, className, isActive)}</div>;
              }
              return (
                <a key={item.href} href={item.href} className={className}>
                  {item.label}
                </a>
              );
            })}
          </nav>
        </aside>

        <main className="px-4 py-6 md:px-8">
          <header className="mb-6 rounded-xl border border-chrome bg-white px-6 py-5 shadow-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="text-[11px] font-semibold text-slate-500">Work System</div>
                <h1 className="mt-2 text-3xl font-semibold">{title}</h1>
                <p className="mt-2 max-w-3xl text-sm text-slate-600">{subtitle}</p>
              </div>
              {headerActions ? <div className="flex flex-wrap items-center gap-2">{headerActions}</div> : null}
            </div>
          </header>
          {children}
        </main>

        <aside className="border-t border-chrome px-4 py-6 md:px-8 xl:border-l xl:border-t-0">
          <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">{contextPanel}</div>
        </aside>
      </div>
    </div>
  );
}

export function EntityHeader({
  id,
  title,
  status,
  ownership,
  blocking,
  primaryActions
}: {
  id: string;
  title: string;
  status: ReactNode;
  ownership: string;
  blocking?: string;
  primaryActions?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-chrome bg-white px-6 py-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <div className="font-mono text-xs text-slate-500">{id}</div>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-2xl font-semibold">{title}</h2>
            {status}
          </div>
          <div className="grid gap-2 text-sm text-slate-600">
            <div>Owner: {ownership}</div>
            {blocking ? <div>Blocking: {blocking}</div> : null}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">{primaryActions}</div>
      </div>
    </div>
  );
}

export function FilterPanel({
  title = "Filters",
  items,
  actions
}: {
  title?: string;
  items: FilterItem[];
  actions?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-chrome bg-white px-5 py-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <SectionHeading title={title} />
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {items.map((item) => (
          item.href ? (
            <a
              key={`${item.label}-${item.value}-${item.href}`}
              href={item.href}
              className={clsx(
                "rounded-full border px-3 py-1.5 text-xs",
                item.active
                  ? "border-slate-300 bg-slate-200 text-slate-950"
                  : "border-chrome bg-slate-50 text-slate-600 hover:bg-slate-100"
              )}
            >
              <span className="font-semibold">{item.label}:</span> {item.value}
            </a>
          ) : (
            <div
              key={`${item.label}-${item.value}`}
              className={clsx(
                "rounded-full border px-3 py-1.5 text-xs",
                item.active ? "border-slate-300 bg-slate-200 text-slate-950" : "border-chrome bg-slate-50 text-slate-600"
              )}
            >
              <span className="font-semibold">{item.label}:</span> {item.value}
            </div>
          )
        ))}
      </div>
    </div>
  );
}

export function DataTable<T>({
  columns,
  data,
  emptyMessage,
  loading = false,
  errorMessage,
  pagination,
  selection,
  columnVisibility
}: {
  columns: Array<TableColumn<T>>;
  data: T[];
  emptyMessage: string;
  loading?: boolean;
  errorMessage?: string;
  pagination?: PaginationConfig;
  selection?: SelectionConfig<T>;
  columnVisibility?: ColumnVisibilityOption[];
}) {
  if (loading) {
    return (
      <div className="rounded-xl border border-chrome bg-white p-6 shadow-sm">
        <div className="text-sm text-slate-600">Loading table data…</div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 shadow-sm">
        <div className="text-sm text-rose-700">{errorMessage}</div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-chrome bg-white p-6 shadow-sm">
        <div className="text-sm text-slate-600">{emptyMessage}</div>
      </div>
    );
  }


  const selectedCount = selection?.selectedKeys.length ?? 0;
  const visibleColumns = columnVisibility
    ? columns.filter((column) => {
        const option = columnVisibility.find((item) => item.key === column.key);
        return option ? option.visible : true;
      })
    : columns;

  return (
    <div className="rounded-xl border border-chrome bg-white shadow-sm">
      {selection || columnVisibility ? (
        <div className="flex flex-col gap-3 border-b border-chrome px-4 py-3 text-sm text-slate-600 md:flex-row md:items-start md:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            {selection ? (
              <>
                <span className="font-medium text-slate-700">Selection</span>
                <span>{selectedCount} selected</span>
                {selection.clearHref && selectedCount > 0 ? (
                  <a href={selection.clearHref} className="rounded-md border border-chrome bg-white px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50">
                    Clear Selection
                  </a>
                ) : null}
              </>
            ) : null}
          </div>
          {columnVisibility ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-slate-700">Columns</span>
              {columnVisibility.map((option) => (
                <a
                  key={option.key}
                  href={option.toggleHref}
                  className={clsx(
                    "rounded-full border px-3 py-1 text-xs",
                    option.visible
                      ? "border-slate-300 bg-slate-200 text-slate-950"
                      : "border-chrome bg-white text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {option.label}
                </a>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-chrome">
          <thead className="sticky top-0 bg-slate-50">
            <tr>
              {selection ? <th className="w-12 px-4 py-3 text-left text-xs font-semibold text-slate-500">Select</th> : null}
              {visibleColumns.map((column) => (
                <th key={column.key} className="px-4 py-3 text-left text-xs font-semibold text-slate-500">
                  {column.sortHref ? (
                    <a href={column.sortHref} className="inline-flex items-center gap-2 hover:text-slate-800">
                      <span>{column.header}</span>
                      <span className="text-[10px] text-slate-400">
                        {column.sortDirection === "asc" ? "▲" : column.sortDirection === "desc" ? "▼" : "↕"}
                      </span>
                    </a>
                  ) : (
                    column.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-chrome">
            {data.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-slate-50">
                {selection ? (
                  <td className="px-4 py-3 align-top text-sm">
                    <a
                      href={selection.toggleHref(selection.rowKey(row))}
                      className={clsx(
                        "inline-flex h-5 w-5 items-center justify-center rounded border text-[10px] font-semibold",
                        selection.selectedKeys.includes(selection.rowKey(row))
                          ? "border-slate-300 bg-slate-200 text-slate-950"
                          : "border-chrome bg-white text-slate-400 hover:bg-slate-50"
                      )}
                      aria-label={`Toggle selection for ${selection.rowKey(row)}`}
                    >
                      {selection.selectedKeys.includes(selection.rowKey(row)) ? "✓" : ""}
                    </a>
                  </td>
                ) : null}
                {visibleColumns.map((column) => (
                  <td key={column.key} className="px-4 py-3 align-top text-sm">
                    {column.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pagination ? (
        <div className="flex flex-col gap-3 border-t border-chrome px-4 py-3 text-sm text-slate-600 md:flex-row md:items-center md:justify-between">
          <div>
            Page {pagination.page} of {pagination.totalPages} · {pagination.totalCount} total records
          </div>
          <div className="flex gap-2">
            {pagination.previousHref ? (
              <a href={pagination.previousHref} className="rounded-md border border-chrome bg-white px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50">
                Previous
              </a>
            ) : (
              <span className="rounded-md border border-chrome bg-slate-50 px-3 py-1.5 text-slate-400">Previous</span>
            )}
            {pagination.nextHref ? (
              <a href={pagination.nextHref} className="rounded-md border border-chrome bg-white px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-50">
                Next
              </a>
            ) : (
              <span className="rounded-md border border-chrome bg-slate-50 px-3 py-1.5 text-slate-400">Next</span>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function TimeSeriesChart({
  title,
  subtitle,
  series,
  valueFormatter = (value: number) => String(value)
}: {
  title: string;
  subtitle?: string;
  series: TimeSeriesChartSeries[];
  valueFormatter?: (value: number) => string;
}) {
  const width = 720;
  const height = 220;
  const padding = 24;
  const longestSeries = series.reduce((longest, current) => (current.points.length > longest.points.length ? current : longest), series[0]);
  const xCount = Math.max(longestSeries?.points.length ?? 0, 1);
  const values = series.flatMap((item) => item.points.map((point) => point.value));
  const maxValue = Math.max(...values, 1);

  return (
    <div className="rounded-xl border border-chrome bg-white px-5 py-4 shadow-sm">
      <div className="flex flex-col gap-1">
        <SectionHeading title={title} />
        {subtitle ? <p className="text-sm text-slate-600">{subtitle}</p> : null}
      </div>
      {series.length === 0 || values.length === 0 ? (
        <div className="mt-4 text-sm text-slate-600">No time-series data available for the selected filters.</div>
      ) : (
        <>
          <svg viewBox={`0 0 ${width} ${height}`} className="mt-4 w-full">
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const y = padding + (height - padding * 2) * ratio;
              return (
                <g key={ratio}>
                  <line x1={padding} y1={y} x2={width - padding} y2={y} stroke="#e2e8f0" strokeWidth="1" />
                  <text x={0} y={y + 4} fill="#64748b" fontSize="10">
                    {valueFormatter(Math.round(maxValue * (1 - ratio)))}
                  </text>
                </g>
              );
            })}
            {series.map((item) => {
              const path = item.points
                .map((point, index) => {
                  const x = padding + ((width - padding * 2) * index) / Math.max(xCount - 1, 1);
                  const y = height - padding - ((height - padding * 2) * point.value) / maxValue;
                  return `${index === 0 ? "M" : "L"} ${x} ${y}`;
                })
                .join(" ");
              return <path key={item.key} d={path} fill="none" stroke={item.color} strokeWidth="3" strokeLinecap="round" />;
            })}
            {longestSeries.points.map((point, index) => {
              const x = padding + ((width - padding * 2) * index) / Math.max(xCount - 1, 1);
              return (
                <text key={`${point.label}-${index}`} x={x} y={height - 6} textAnchor="middle" fill="#64748b" fontSize="10">
                  {point.label.slice(5)}
                </text>
              );
            })}
          </svg>
          <div className="mt-4 flex flex-wrap gap-3">
            {series.map((item) => {
              const latest = item.points[item.points.length - 1]?.value ?? 0;
              return (
                <div key={item.key} className="rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="font-medium text-slate-700">{item.label}</span>
                  </div>
                  <div className="mt-1 text-slate-600">Latest: {valueFormatter(latest)}</div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

export function Tabs({
  tabs,
  activeKey,
  renderTabLink
}: {
  tabs: { key: string; label: string; href?: string }[];
  activeKey: string;
  renderTabLink?: LinkRenderer;
}) {
  return (
    <div className="rounded-xl border border-chrome bg-white p-2 shadow-sm">
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => {
          const isActive = tab.key === activeKey;
          const className = clsx(
            "rounded-lg px-3 py-2 text-sm font-medium",
            isActive ? "bg-slate-200 text-slate-950" : "text-slate-600 hover:bg-slate-100"
          );
          if (tab.href && renderTabLink) {
            return <div key={tab.key}>{renderTabLink({ label: tab.label, href: tab.href }, className, isActive)}</div>;
          }
          if (tab.href) {
            return (
              <a key={tab.key} href={tab.href} className={className}>
                {tab.label}
              </a>
            );
          }
          return (
            <div key={tab.key} className={clsx("rounded-lg px-3 py-2 text-sm font-medium", isActive ? "bg-slate-200 text-slate-950" : "text-slate-600")}>
              {tab.label}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function Timeline({
  steps,
  currentStepId
}: {
  steps: Array<{ id: string; name: string; status: string; owner?: string }>;
  currentStepId: string;
}) {
  return (
    <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
      <SectionHeading title="Run Steps" />
      <div className="mt-4 space-y-3">
        {steps.map((step, index) => (
          <div key={step.id} className="flex gap-3">
            <div className="flex w-6 flex-col items-center">
              <div
                className={clsx(
                  "mt-1 h-3 w-3 rounded-full",
                  step.id === currentStepId
                    ? "bg-accent"
                    : step.status === "completed"
                      ? "bg-success"
                      : step.status === "failed"
                        ? "bg-danger"
                        : step.status === "blocked"
                          ? "bg-warning"
                          : "bg-slate-300"
                )}
              />
              {index < steps.length - 1 ? <div className="mt-1 h-full w-px bg-chrome" /> : null}
            </div>
            <div className="pb-3">
              <div className="font-medium">{step.name}</div>
              <div className="text-xs text-slate-500">{step.status}{step.owner ? ` · ${step.owner}` : ""}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ReviewPanel({
  state,
  scopeLabel
}: {
  state: string;
  scopeLabel: string;
}) {
  return (
    <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
      <SectionHeading title="Review Panel" />
      <div className="mt-4 space-y-4">
        <div className="text-sm text-slate-600">Scope: {scopeLabel}</div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-500">State</span>
          <Badge tone={state === "approved" ? "success" : state === "changes_requested" ? "warning" : state === "blocked" ? "danger" : "neutral"}>{state}</Badge>
        </div>
        <div className="grid gap-2">
          <Button label="Approve" tone="primary" />
          <Button label="Request Changes" tone="secondary" />
          <Button label="Block" tone="danger" />
          <Button label="Comment" tone="secondary" />
        </div>
      </div>
    </div>
  );
}

export function PromotionGate({
  checks,
  approvals,
  target,
  readiness
}: {
  checks: Array<{ name: string; state: string; detail: string }>;
  approvals: Array<{ reviewer: string; state: string; scope: string }>;
  target: string;
  readiness: string;
}) {
  return (
    <div className="space-y-4 rounded-xl border border-chrome bg-white p-5 shadow-sm">
      <SectionHeading title="Promotion Gate" />
      <div className="text-sm text-slate-600">Target: {target}</div>
      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-lg border border-chrome bg-slate-50 p-4">
          <div className="mb-2 text-[11px] font-semibold text-slate-500">Required Checks</div>
          <div className="space-y-2">
            {checks.map((check) => (
              <div key={check.name} className="text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{check.name}</span>
                  <Badge tone={check.state === "passed" ? "success" : check.state === "pending" ? "warning" : "danger"}>{check.state}</Badge>
                </div>
                <div className="text-slate-600">{check.detail}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-lg border border-chrome bg-slate-50 p-4">
          <div className="mb-2 text-[11px] font-semibold text-slate-500">Required Approvals</div>
          <div className="space-y-2">
            {approvals.map((approval) => (
              <div key={`${approval.reviewer}-${approval.scope}`} className="text-sm">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{approval.reviewer}</span>
                  <Badge tone={approval.state === "approved" ? "success" : approval.state === "pending" ? "warning" : "danger"}>{approval.state}</Badge>
                </div>
                <div className="text-slate-600">{approval.scope}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <div className="rounded-lg border border-chrome bg-amber-50 p-4 text-sm text-slate-700">{readiness}</div>
      <div className="flex flex-wrap gap-2">
        <Button label="Dry Run" tone="secondary" />
        <Button label="Authorize Promotion" tone="secondary" />
        <Button label="Execute Promotion" tone="primary" />
      </div>
    </div>
  );
}

export function ConversationDock({
  title,
  messages
}: {
  title: string;
  messages: Array<{ actor: string; text: string }>;
}) {
  return (
    <div className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
      <SectionHeading title={title} />
      <div className="mt-4 space-y-3">
        {messages.map((message, index) => (
          <div key={index} className="rounded-lg border border-chrome bg-slate-50 p-3 text-sm">
            <div className="font-medium">{message.actor}</div>
            <div className="mt-1 text-slate-600">{message.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function KeyValueGrid({ items }: { items: Array<{ label: string; value: ReactNode }> }) {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {items.map((item) => (
        <div key={item.label} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">
          <div className="text-[11px] font-semibold text-slate-500">{item.label}</div>
          <div className="mt-1 text-sm text-slate-800">{item.value}</div>
        </div>
      ))}
    </div>
  );
}

export function Badge({
  tone,
  children
}: {
  tone: "neutral" | "info" | "warning" | "danger" | "success";
  children: ReactNode;
}) {
  const toneClassName = {
    neutral: "bg-slate-100 text-slate-700",
    info: "bg-blue-100 text-blue-700",
    warning: "bg-amber-100 text-amber-800",
    danger: "bg-rose-100 text-rose-800",
    success: "bg-emerald-100 text-emerald-800"
  }[tone];

  return <span className={clsx("inline-flex rounded-full px-2.5 py-1 text-xs font-semibold", toneClassName)}>{children}</span>;
}

export function SectionHeading({ title }: { title: string }) {
  return <h3 className="text-sm font-semibold text-slate-600">{title}</h3>;
}

export function Button({
  label,
  tone = "secondary",
  type = "button",
  disabled = false
}: {
  label: string;
  tone?: "primary" | "secondary" | "danger";
  type?: "button" | "submit";
  disabled?: boolean;
}) {
  const className = {
    primary: "bg-accent text-white",
    secondary: "bg-slate-100 text-slate-800",
    danger: "bg-rose-600 text-white"
  }[tone];

  return (
    <button type={type} disabled={disabled} className={clsx("rounded-md px-4 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50", className)}>
      {label}
    </button>
  );
}
