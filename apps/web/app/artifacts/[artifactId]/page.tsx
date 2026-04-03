import { getArtifact } from "@/lib/server-api";
import { Badge, DataTable, EntityHeader, PageShell, ReviewPanel, appShellProps, statusTone } from "../../../components/ui-helpers";

export default async function ArtifactDetailPage({ params }: { params: Promise<{ artifactId: string }> }) {
  const { artifactId } = await params;
  const detail = await getArtifact(artifactId);
  const selected = detail.versions.find((version) => version.id === detail.selected_version_id) ?? detail.versions[0];

  return (
    <PageShell {...appShellProps("/artifacts", "Artifact Detail", "Canonical review surface for governed artifact versions.")}>
      <div className="space-y-4">
        <EntityHeader
          id={detail.artifact.id}
          title={detail.artifact.name}
          status={<Badge tone={statusTone(detail.artifact.status)}>{detail.artifact.status}</Badge>}
          ownership={detail.artifact.owner}
          blocking={detail.stale_review ? "Review is stale and must be refreshed." : undefined}
        />
        <div className="grid gap-4 xl:grid-cols-[260px_minmax(0,1fr)_320px]">
          <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <div className="text-xs font-medium text-slate-500">Versions</div>
            <div className="mt-4 space-y-2">
              {detail.versions.map((version) => (
                <div key={version.id} className={`rounded-lg border px-4 py-3 text-sm ${version.id === detail.selected_version_id ? "border-accent bg-blue-50" : "border-chrome bg-slate-50"}`}>
                  <div className="font-medium">{version.label}</div>
                  <div className="text-slate-600">{version.summary}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-medium text-slate-500">Selected Version</div>
                <h2 className="mt-2 text-xl font-semibold">{selected.label}</h2>
              </div>
              <Badge tone={statusTone(selected.status)}>{selected.status}</Badge>
            </div>
            <div className="mt-4 rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Content / Diff</div>
              <pre className="mt-3 whitespace-pre-wrap font-mono text-sm text-slate-700">{selected.content}</pre>
            </div>
          </div>
          <ReviewPanel state={detail.review_state} scopeLabel={`${detail.artifact.name} ${selected.label}`} />
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <DataTable
            data={detail.lineage}
            emptyMessage="No lineage edges recorded."
            columns={[
              { key: "from", header: "From Version", render: (row) => row.from_version_id ?? "Request" },
              { key: "to", header: "To Version", render: (row) => row.to_version_id },
              { key: "relation", header: "Relation", render: (row) => row.relation },
              { key: "created", header: "Recorded At", render: (row) => new Date(row.created_at).toLocaleString() }
            ]}
          />
          <DataTable
            data={detail.history}
            emptyMessage="No artifact history recorded."
            columns={[
              { key: "time", header: "Timestamp", render: (row) => new Date(row.timestamp).toLocaleString() },
              { key: "actor", header: "Actor", render: (row) => row.actor },
              { key: "action", header: "Action", render: (row) => row.action },
              { key: "detail", header: "Detail", render: (row) => row.detail }
            ]}
          />
        </div>
      </div>
    </PageShell>
  );
}
