import { PageShell } from "@rgp/ui";
import { DataTable, appShellProps } from "../../components/ui-helpers";

const workspaces = [
  { id: "ws_001", name: "Curriculum Repository", owner: "team_curriculum", changesets: 4, status: "active" },
  { id: "ws_002", name: "Assessment Repository", owner: "team_assessment", changesets: 2, status: "active" }
];

export default function WorkspacesPage() {
  return (
    <PageShell {...appShellProps("/workspaces", "Workspaces", "Repository-backed change governance for governed code and non-code workspaces.")}>
      <DataTable
        data={workspaces}
        emptyMessage="No workspaces available."
        columns={[
          { key: "id", header: "Workspace", render: (row) => row.id },
          { key: "name", header: "Name", render: (row) => row.name },
          { key: "owner", header: "Owner", render: (row) => row.owner },
          { key: "changesets", header: "Change Sets", render: (row) => row.changesets },
          { key: "status", header: "Status", render: (row) => row.status }
        ]}
      />
    </PageShell>
  );
}
