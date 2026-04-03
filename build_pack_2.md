PART 3 — COMPONENT CONTRACT LIBRARY





This defines exact reusable UI primitives.

An implementation agent MUST NOT invent alternatives.








3.1 Component Rules (Global)





Every screen MUST be composed from these components
No duplicate component patterns allowed
Components MUST be stateless where possible
All components MUST support full state model
All components MUST be accessible









3.2 DataTable (CRITICAL COMPONENT)







Purpose





Primary data exploration surface.





Props



DataTable<T> {
  columns: ColumnDef<T>[]
  data: T[]
  totalCount: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onSortChange: (sort: Sort[]) => void
  onFilterChange: (filters: Filter[]) => void
  selectable?: boolean
  onSelectionChange?: (ids: string[]) => void
  rowAction?: (row: T) => void
}







Required Features





server-side pagination
multi-column sorting
filter integration
sticky header
column resizing
column visibility toggle
row selection
bulk actions support









States





loading → skeleton rows
empty → empty message + CTA
error → persistent banner
normal









Forbidden





client-only pagination for large datasets
inline complex editing
nested workflows









3.3 FilterPanel







Purpose





Structured filtering system.





Props



FilterPanel {
  filters: FilterDefinition[]
  values: Record<string, any>
  onChange: (values) => void
  onSaveView: () => void
}







Behavior





multi-filter logic (AND/OR)
persistent filters
saved views









3.4 EntityHeader







Purpose





Top-level context for any entity.





Contains





ID
title
status badge
ownership
blocking indicator
primary actions









Rules





must always be visible
must include next action if applicable









3.5 StatusBadge







Props



StatusBadge {
  status: string
  variant: "success" | "active" | "warning" | "error" | "neutral"
}







Rules





must be color-coded + labeled
must support accessibility (icon + text)









3.6 Tabs







Props



Tabs {
  tabs: { key: string; label: string }[]
  activeKey: string
  onChange: (key: string) => void
}







Rules





max 7 tabs
no nested tabs
must reflect domain model









3.7 Timeline (Run Steps)







Purpose





Visual execution flow.





Props



Timeline {
  steps: Step[]
  currentStepId: string
}







States





completed
active
blocked
failed









Rules





always visible in Run Detail
no hidden steps









3.8 DiffViewer







Purpose





Artifact comparison.





Props



DiffViewer {
  left: ArtifactVersion
  right: ArtifactVersion
  mode: "side-by-side" | "inline"
}







Rules





must support large files
must support line comments
must preserve whitespace visibility









3.9 ReviewPanel







Purpose





Formal review actions.





Props



ReviewPanel {
  state: ReviewState
  onApprove: () => void
  onRequestChanges: () => void
  onBlock: () => void
  onComment: (text: string) => void
}







Rules





must be separate from chat
must attach to scope (artifact/version)









3.10 PromotionGate







Purpose





Final governance surface.





Props



PromotionGate {
  checks: CheckResult[]
  approvals: Review[]
  target: Target
  onPromote: () => void
  onDryRun: () => void
}







Rules





must show ALL blocking conditions
must not allow hidden approval









3.11 ConversationDock







Purpose





Scoped interaction.





Props



ConversationDock {
  threadId: string
  messages: Message[]
  onSend: (message) => void
}







Rules





docked bottom or side only
never replaces structured UI









3.12 CommandComposer







Purpose





Structured control actions.





Props



CommandComposer {
  availableCommands: CommandType[]
  onExecute: (command) => void
}







Rules





commands must be structured
must not be free-text interpretation









3.13 MetricTable







Purpose





Analytics primary surface.





Rules





always tabular first
charts optional
must support drill-down









PART 4 — DECISION TABLES










4.1 Review Requirement Matrix



Request Type

Required Reviewers

Blocking

Re-review

Standard

1

Yes

On change

Critical

2+ roles

Yes

Always

Capability

Multi-role

Yes

Always








4.2 Promotion Eligibility



Condition

Required

All checks passed

Yes

No stale reviews

Yes

Required approvals present

Yes

No blocking flags

Yes








4.3 Stale Review Rules



Change Type

Stale?

Artifact content change

Yes

Metadata change

No

Re-run execution

Yes








4.4 Ownership Routing



Scope

Owner

Request Type

Team

Artifact Type

Domain Owner

Code Path

Code Owner








4.5 Command Authorization



Role

Allowed Commands

Submitter

limited

Reviewer

review only

Operator

run control

Admin

all








PART 5 — INTEGRATION CONTRACTS










5.1 Foundry Adapter







Responsibilities





dispatch runs
receive status
return outputs









Contract



{
  "request_id": "...",
  "workflow_id": "...",
  "input": {},
  "context": {}
}







5.2 Agent Framework Adapter





workflow execution
step events
agent coordination









5.3 GitHub / MCP Adapter





repo read/write
change set apply
PR mirroring (optional)









Rules





must respect governance
must be scoped per request
must be auditable









5.4 Identity Provider





SAML/OIDC login
SCIM provisioning









5.5 Policy Engine





evaluate checks
return pass/fail + evidence









5.6 Notification System





async delivery
retries
escalation









FINAL STATE








You now have:





Architecture





✔ Complete





UX IA





✔ Complete





Style Guide





✔ Complete





Design System





✔ Complete





Domain Model





✔ Complete





Screen Contracts





✔ Complete





Component Contracts





✔ Complete





Decision Logic





✔ Complete





Integration Contracts





✔ Complete








FINAL VERDICT





This is now:

A fully specified enterprise application blueprint
that an AI agent can implement with minimal ambiguity
