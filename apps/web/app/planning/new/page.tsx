import { PageShell, appShellProps } from "../../../components/ui-helpers";

import { createPlanningConstructAction } from "../actions";

export default function NewPlanningConstructPage() {
  return (
    <PageShell
      {...appShellProps(
        "/planning",
        "New Planning Construct",
        "Create a governed initiative, release, milestone, campaign, or related planning container."
      )}
    >
      <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
        <form action={createPlanningConstructAction} className="grid gap-4">
          <div className="grid gap-2 md:grid-cols-2">
            <div className="grid gap-2">
              <label htmlFor="planning-type" className="text-sm font-medium text-slate-700">Type</label>
              <select id="planning-type" name="type" defaultValue="initiative" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm">
                <option value="initiative">Initiative</option>
                <option value="program">Program</option>
                <option value="release">Release</option>
                <option value="milestone">Milestone</option>
                <option value="campaign">Campaign</option>
              </select>
            </div>
            <div className="grid gap-2">
              <label htmlFor="planning-priority" className="text-sm font-medium text-slate-700">Priority</label>
              <input id="planning-priority" name="priority" type="number" min="0" defaultValue="0" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="grid gap-2">
            <label htmlFor="planning-name" className="text-sm font-medium text-slate-700">Name</label>
            <input id="planning-name" name="name" required className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
          </div>
          <div className="grid gap-2">
            <label htmlFor="planning-description" className="text-sm font-medium text-slate-700">Description</label>
            <textarea id="planning-description" name="description" rows={3} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
          </div>
          <div className="grid gap-2 md:grid-cols-2">
            <div className="grid gap-2">
              <label htmlFor="planning-owner-team" className="text-sm font-medium text-slate-700">Owner Team</label>
              <input id="planning-owner-team" name="ownerTeamId" placeholder="team_assessment_quality" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid gap-2">
              <label htmlFor="planning-target-date" className="text-sm font-medium text-slate-700">Target Date</label>
              <input id="planning-target-date" name="targetDate" type="date" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="grid gap-2">
            <label htmlFor="planning-capacity" className="text-sm font-medium text-slate-700">Capacity Budget</label>
            <input id="planning-capacity" name="capacityBudget" type="number" min="0" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm" />
          </div>
          <div className="flex justify-end">
            <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-4 py-2 text-sm font-medium text-white">
              Create Planning Construct
            </button>
          </div>
        </form>
      </div>
    </PageShell>
  );
}
