import { PageShell, appShellProps } from "../../../components/ui-helpers";
import { createKnowledgeArtifactAction } from "../actions";

export default function NewKnowledgeArtifactPage() {
  return (
    <PageShell {...appShellProps("/knowledge", "New Knowledge Artifact", "Create a governed knowledge artifact for reusable guidance, policy context, or operational memory.")}>
      <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
        <form action={createKnowledgeArtifactAction} className="grid gap-4">
          <div className="grid gap-2">
            <label htmlFor="knowledge-name" className="text-sm font-medium text-slate-700">Name</label>
            <input id="knowledge-name" name="name" required className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
          </div>
          <div className="grid gap-2">
            <label htmlFor="knowledge-description" className="text-sm font-medium text-slate-700">Description</label>
            <textarea id="knowledge-description" name="description" rows={3} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
          </div>
          <div className="grid gap-2">
            <label htmlFor="knowledge-content" className="text-sm font-medium text-slate-700">Content</label>
            <textarea id="knowledge-content" name="content" rows={12} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-mono" />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <label htmlFor="knowledge-content-type" className="text-sm font-medium text-slate-700">Content Type</label>
              <select id="knowledge-content-type" name="contentType" defaultValue="text" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                <option value="text">Text</option>
                <option value="markdown">Markdown</option>
                <option value="json">JSON</option>
              </select>
            </div>
            <div className="grid gap-2">
              <label htmlFor="knowledge-tags" className="text-sm font-medium text-slate-700">Tags</label>
              <input id="knowledge-tags" name="tags" placeholder="policy, editorial, onboarding" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-4 py-2 text-sm font-medium text-white">
              Create Knowledge Artifact
            </button>
          </div>
        </form>
      </div>
    </PageShell>
  );
}
