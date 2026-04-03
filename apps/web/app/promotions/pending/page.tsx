import { listRequests } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, QueueTabs, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";

const promotionQueueTabs = [
  { key: "pending", label: "Promotion Pending", href: "/promotions/pending" },
  { key: "all-requests", label: "All Requests", href: "/requests" }
];

export default async function PromotionPendingPage({
  searchParams
}: {
  searchParams: Promise<{ page?: string; sort?: string; order?: string; selected?: string; cols?: string }>;
}) {
  const filters = await searchParams;
  const page = Number(filters.page ?? "1") || 1;
  const data = await listRequests({ status: "promotion_pending", page, page_size: 25 });
  const sort = filters.sort ?? "updated_at";
  const order = filters.order === "asc" ? "asc" : "desc";
  const selectedKeys = (filters.selected ?? "").split(",").filter(Boolean);
  const defaultColumns = ["id", "title", "status", "owner", "workflow", "promotion", "updated"];
  const visibleColumnKeys = new Set((filters.cols ?? defaultColumns.join(",")).split(",").filter(Boolean));
  const sortedItems = [...data.items].sort((left, right) => {
    const direction = order === "asc" ? 1 : -1;
    switch (sort) {
      case "title":
        return direction * left.title.localeCompare(right.title);
      case "owner_team_id":
        return direction * (left.owner_team_id ?? "").localeCompare(right.owner_team_id ?? "");
      default:
        return direction * (new Date(left.updated_at).getTime() - new Date(right.updated_at).getTime());
    }
  });
  const withPage = (nextPage: number, overrides: Record<string, string | undefined> = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries({ ...filters, ...overrides, page: String(nextPage) })) {
      if (value) {
        params.set(key, value);
      }
    }
    return `/promotions/pending?${params.toString()}`;
  };
  const sortHref = (column: string) => withPage(1, { sort: column, order: sort === column && order === "asc" ? "desc" : "asc" });
  const toggleSelectedHref = (requestId: string) => {
    const nextSelected = selectedKeys.includes(requestId)
      ? selectedKeys.filter((key) => key !== requestId)
      : [...selectedKeys, requestId];
    return withPage(1, { selected: nextSelected.length > 0 ? nextSelected.join(",") : undefined });
  };
  const toggleColumnHref = (columnKey: string) => {
    const nextColumns = new Set(visibleColumnKeys);
    if (nextColumns.has(columnKey)) {
      if (nextColumns.size === 1) {
        return withPage(1);
      }
      nextColumns.delete(columnKey);
    } else {
      nextColumns.add(columnKey);
    }
    return withPage(1, { cols: Array.from(nextColumns).join(",") });
  };
  const columnVisibility = [
    { key: "title", label: "Title" },
    { key: "status", label: "Status" },
    { key: "owner", label: "Owner" },
    { key: "workflow", label: "Workflow" },
    { key: "promotion", label: "Action" },
    { key: "updated", label: "Updated" }
  ].map((column) => ({
    ...column,
    visible: visibleColumnKeys.has(column.key),
    toggleHref: toggleColumnHref(column.key)
  }));

  return (
    <PageShell
      {...appShellProps("/promotions/pending", "Promotion Pending", "Operational gate for approved work waiting on promotion checks, approvals, or execution confirmation.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Queue Status" />
          <MetricStack
            items={[
              { label: "Promotion Pending", value: data.total_count },
              { label: "Owners", value: new Set(data.items.map((item) => item.owner_team_id ?? "Unassigned")).size },
              { label: "Urgent", value: data.items.filter((item) => item.priority === "urgent").length }
            ]}
          />
        </div>
      }
    >
      <div className="space-y-4">
        <QueueTabs activeKey="pending" items={promotionQueueTabs} />
        <FilterPanel
          title="Queue Filters"
          items={[
            { label: "Queue", value: "Promotion Pending", active: true },
            { label: "Status", value: "promotion_pending", active: true }
          ]}
          actions={
            <Link href="/requests?status=promotion_pending&page=1" className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
              Open In Requests
            </Link>
          }
        />
        <DataTable
          data={sortedItems}
          emptyMessage="No promotion-pending requests."
          selection={{
            rowKey: (row) => row.id,
            selectedKeys,
            toggleHref: toggleSelectedHref,
            clearHref: selectedKeys.length > 0 ? withPage(1, { selected: undefined }) : undefined
          }}
          columnVisibility={columnVisibility}
          pagination={{
            page: data.page,
            pageSize: data.page_size,
            totalCount: data.total_count,
            totalPages: data.total_pages,
            previousHref: data.page > 1 ? withPage(data.page - 1) : undefined,
            nextHref: data.page < data.total_pages ? withPage(data.page + 1) : undefined
          }}
          columns={[
            { key: "id", header: "Request ID", render: (row) => <Link href={`/requests/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
            { key: "title", header: "Title", sortHref: sortHref("title"), sortDirection: sort === "title" ? order : undefined, render: (row) => row.title },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "owner", header: "Owner", sortHref: sortHref("owner_team_id"), sortDirection: sort === "owner_team_id" ? order : undefined, render: (row) => row.owner_team_id ?? "Unassigned" },
            { key: "workflow", header: "Workflow", render: (row) => row.workflow_binding_id ?? row.template_id },
            {
              key: "promotion",
              header: "Promotion Action",
              render: (row) => <Link href={`/requests/${row.id}`} className="text-accent">Open request gate</Link>
            },
            { key: "updated", header: "Updated At", sortHref: sortHref("updated_at"), sortDirection: sort === "updated_at" ? order : undefined, render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
