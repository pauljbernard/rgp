import { getRequestHistory } from "@/lib/server-api";
import { DataTable, PageShell, Tabs, appShellProps } from "../../../../components/ui-helpers";

export default async function RequestHistoryPage({ params }: { params: Promise<{ requestId: string }> }) {
  const { requestId } = await params;
  const history = await getRequestHistory(requestId);

  return (
    <PageShell {...appShellProps("/requests", "Audit History", "Immutable request timeline and traceability view.")}>
      <div className="space-y-4">
        <Tabs
          activeKey="history"
          tabs={[
            { key: "overview", label: "Overview", href: `/requests/${requestId}` },
            { key: "history", label: "History", href: `/requests/${requestId}/history` }
          ]}
        />
        <DataTable
          data={history}
          emptyMessage="No audit history available."
          columns={[
            { key: "timestamp", header: "Timestamp", render: (row) => new Date(row.timestamp).toLocaleString() },
            { key: "actor", header: "Actor", render: (row) => row.actor },
            { key: "action", header: "Action", render: (row) => row.action },
            { key: "type", header: "Object Type", render: (row) => row.object_type },
            { key: "id", header: "Object ID", render: (row) => row.object_id },
            { key: "reason", header: "Reason / Evidence", render: (row) => row.reason_or_evidence }
          ]}
        />
      </div>
    </PageShell>
  );
}
