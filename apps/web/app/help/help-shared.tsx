import type { ReactNode } from "react";
import { DataTable, SectionHeading, Tabs, appShellProps } from "../../components/ui-helpers";

export const helpTabs = [
  { key: "overview", label: "Overview", href: "/help" },
  { key: "requests", label: "Requests", href: "/help/requests" },
  { key: "operations", label: "Operations", href: "/help/operations" },
  { key: "admin", label: "Admin", href: "/help/admin" },
  { key: "analytics", label: "Analytics", href: "/help/analytics" },
  { key: "journeys", label: "Journeys", href: "/help/journeys" }
];

export function helpShellProps(title: string, subtitle: string) {
  return appShellProps("/help", title, subtitle);
}

export function HelpTabs({ activeKey }: { activeKey: string }) {
  return <Tabs activeKey={activeKey} tabs={helpTabs} />;
}

export function HelpSection({
  title,
  description,
  children
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-chrome bg-white p-5 shadow-sm">
      <SectionHeading title={title} />
      {description ? <p className="mt-2 text-sm text-slate-600">{description}</p> : null}
      {children ? <div className="mt-4">{children}</div> : null}
    </section>
  );
}

export function HelpTable<T>({
  data,
  columns,
  emptyMessage = "No guide entries available."
}: {
  data: T[];
  columns: Array<{ key: string; header: string; render: (row: T) => React.ReactNode }>;
  emptyMessage?: string;
}) {
  return <DataTable data={data} columns={columns} emptyMessage={emptyMessage} />;
}
