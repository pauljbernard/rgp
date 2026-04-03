1. UX INFORMATION ARCHITECTURE SPEC (FINALIZED)










1.1 Canonical Object Model





This is the single source of truth for navigation and UX structure:

Request (PRIMARY ROOT OBJECT)
  ├── Runs
  │     ├── Steps
  │     └── Logs
  ├── Artifacts
  │     └── Versions
  ├── Reviews
  ├── Conversations
  ├── Checks
  └── Promotions

Capability (SECONDARY ROOT)
  ├── Definitions
  ├── Versions
  ├── Usage
  └── Performance

Workspace (SPECIALIZED ROOT)
  ├── Change Sets
  │     ├── Diffs
  │     └── Commits







1.2 Primary Navigation Model



Requests
Runs
Artifacts
Reviews
Promotions
Capabilities
Workspaces
Analytics
Admin







1.3 Navigation Rules







Rule 1 — Always Enter Through Lists





No direct deep-link dependency
Lists are the canonical entry






Rule 2 — Drill Down Only



List → Detail → Sub-detail → Trace


Rule 3 — No Cross-Context Jumping





Example:



Run → Artifact → Review is allowed
Run → random dashboard is NOT allowed









1.4 Role-Based Entry Points



Role

Entry Screen

Submitter

Request List

Reviewer

Review Queue

Operator

Active Runs

Executive

Analytics

Admin

Capabilities








1.5 Queue Semantics (CRITICAL)





Queues must exist for:



Review Queue
Blocked Requests
Failed Runs
Promotion Pending
SLA Risk




Each queue MUST:



be table-driven
support sorting and filtering
be actionable









2. DESIGN SYSTEM SPEC










2.1 Layout System







Page Shell



Top Nav
Left Nav (optional)
Main Content
Right Context Panel
Bottom Panel (conversation only)







2.2 Spacing System





Use fixed scale:

4px base unit
8px small
16px standard
24px section
32px major section







2.3 Typography



Title: 24px
Section: 18px
Body: 14px
Table: 13px
Meta: 12px
Monospace:



IDs
hashes
system data









2.4 Color System





Only use color for state:

State

Color

Success

Green

Active

Blue

Warning

Yellow

Failed

Red

Inactive

Gray

NO decorative colors.








2.5 Table Standard (MANDATORY)





All tables must support:



server-side pagination
multi-column sort
column visibility toggle
saved filters
sticky headers
row selection









2.6 Form Standard





label above field
inline validation
required field marking
no hidden required fields









2.7 Panel Types



Panel

Use

Main Panel

Data

Right Panel

Context

Bottom Panel

Conversation ONLY








2.8 Action Hierarchy



Primary → prominent button
Secondary → outline button
Tertiary → text link
Danger → red







2.9 Status Indicators





Must always show:



state
blocking reason
SLA risk









2.10 Accessibility





keyboard navigation required
ARIA roles
color contrast compliance









3. USER JOURNEY SPEC










3.1 Submitter Journey



Request List → New Request → Submit
→ Request Detail → Monitor Runs
→ View Artifacts → View Outcome







3.2 Reviewer Journey



Review Queue → Select Item
→ Artifact Review → Approve/Reject
→ Return to Queue







3.3 Operator Journey



Active Runs → Select Run
→ Diagnose → Pause/Retry
→ Resolve → Return







3.4 Capability Author Journey



Request → Generate Workflow
→ Review → Approve
→ Promote → Activate







3.5 Executive Journey



Analytics → Select Metric
→ Drill-down → Identify Issue
→ Navigate to Requests







3.6 Admin Journey



Admin → Templates
→ Modify → Publish
→ Monitor Usage







4. SCREEN-BY-SCREEN SPEC










4.1 Request List







Purpose





Primary navigation for all work.





Columns





ID
Type
Status
Owner
Priority
Phase
SLA Risk
Updated






Actions





New Request
Filter
Save View









4.2 Request Detail







Purpose





Central control plane.





Tabs





Overview
Runs
Artifacts
Reviews
Conversations
History






Actions





Cancel
Escalate
Re-run









4.3 Run Detail







Purpose





Execution monitoring.





Sections





Step Timeline (left)
Current Step (center)
Context (right)
Conversation (bottom)









4.4 Artifact Detail







Purpose





Review surface.





Layout





Left: versions
Center: content/diff
Right: review panel









4.5 Review Queue







Purpose





Worklist for reviewers.





Columns





Request
Artifact
Type
SLA
Blocking
Assigned









4.6 Promotion Gate







Purpose





Final governance step.





Sections





Checks
Approvals
Target
Strategy









4.7 Capability Registry







Purpose





System definition view.





Columns





Name
Type
Version
Status
Owner









4.8 Analytics







Purpose





Performance optimization.





Views





Workflow table
Agent table
Bottleneck table









4.9 Audit View







Purpose





Full traceability.





Columns





Time
Actor
Action
Object
Reason









FINAL ASSESSMENT








You now have:





Architecture





complete






UX Structure





enterprise-grade






Design System





defined






Journeys





explicit






Screens





constrained and buildable









FINAL VERDICT





This is now:

Enterprise-grade UX specification
+
AI-buildable UI contract
+
Scalable interaction model
