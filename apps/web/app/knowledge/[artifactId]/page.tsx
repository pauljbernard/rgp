import { getKnowledgeArtifact, listKnowledgeVersions } from "@/lib/server-api";
import { Badge, DataTable, PageShell, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";
import { publishKnowledgeArtifactAction } from "../actions";

export default async function KnowledgeArtifactDetailPage({
  params,
}: {
  params: Promise<{ artifactId: string }>;
}) {
  const { artifactId } = await params;
  const [artifact, versions] = await Promise.all([getKnowledgeArtifact(artifactId), listKnowledgeVersions(artifactId)]);

  return (
    <PageShell
      {...appShellProps("/knowledge", artifact.name, "Inspect governed knowledge content, publication state, and version lineage.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Artifact State" />
          <div className="space-y-2 text-sm text-slate-700">
            <div>Status: <Badge tone={statusTone(artifact.status)}>{artifact.status}</Badge></div>
            <div>Version: v{artifact.version}</div>
            <div>Type: {artifact.content_type}</div>
            <div>Created By: {artifact.created_by}</div>
            <div>Updated: {artifact.updated_at ? formatDate(artifact.updated_at) : "—"}</div>
          </div>
          {artifact.status !== "published" ? (
            <form action={publishKnowledgeArtifactAction}>
              <input type="hidden" name="artifactId" value={artifact.id} />
              <button type="submit" className="w-full rounded-md border border-slate-300 bg-slate-950 px-4 py-2 text-sm font-medium text-white">
                Publish Artifact
              </button>
            </form>
          ) : null}
        </div>
      }
    >
      <div className="space-y-4">
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <h2 className="text-lg font-semibold">Summary</h2>
          <p className="mt-2 text-sm text-slate-700">{artifact.description || "No description provided."}</p>
          <div className="mt-3 text-xs text-slate-500">Tags: {artifact.tags.join(", ") || "—"}</div>
        </div>
        <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <h2 className="text-lg font-semibold">Content</h2>
          <pre className="mt-3 overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-4 text-sm text-slate-100">{artifact.content || "No content provided."}</pre>
        </div>
        <DataTable
          data={versions}
          emptyMessage="No versions recorded."
          columns={[
            { key: "version", header: "Version", render: (row) => `v${row.version}` },
            { key: "summary", header: "Summary", render: (row) => row.summary || "—" },
            { key: "author", header: "Author", render: (row) => row.author },
            { key: "created", header: "Created", render: (row) => (row.created_at ? formatDate(row.created_at) : "—") },
          ]}
        />
      </div>
    </PageShell>
  );
}
