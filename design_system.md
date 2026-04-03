RGP ENTERPRISE DESIGN SYSTEM







Version 1.0










1. DESIGN PRINCIPLES (FOUNDATIONAL)










1.1 Work System, Not Application





The UI SHALL behave like:

An operating system for governed work
NOT:

A dashboard-heavy web app







1.2 Data First, Interaction Second





Tables and structured data dominate
Interaction is contextual and controlled
Conversation is secondary









1.3 Deterministic UX





Same input → same visible outcome
No hidden state
No implicit transitions









1.4 Explicit Over Elegant





clarity > minimalism
visibility > cleverness
structure > abstraction









1.5 Consistency Over Flexibility





no per-page design variations
no component improvisation
no alternate patterns









2. DESIGN TOKEN SYSTEM










2.1 Spacing Scale





Base unit: 4px

Token

Value

space-1

4px

space-2

8px

space-3

12px

space-4

16px

space-5

24px

space-6

32px








2.2 Border Radius



Token

Value

radius-sm

4px

radius-md

8px

radius-lg

12px

radius-xl

16px








2.3 Elevation





Minimal shadows only:

Token

Use

elevation-0

flat

elevation-1

panels

elevation-2

modals








2.4 Z-Index



Base → Panels → Modals → Alerts → Global overlays







3. COLOR SYSTEM (SEMANTIC ONLY)










3.1 Neutral Palette





Used for:



backgrounds
borders
typography









3.2 State Colors (STRICT)



State

Color

Active

Blue

Success

Green

Warning

Yellow

Failed

Red

Neutral

Gray








3.3 Rules





No decorative color usage
No gradient backgrounds
Color must always encode meaning









4. TYPOGRAPHY SYSTEM










4.1 Scale



Level

Size

H1

24px

H2

20px

H3

18px

Body

14px

Table

13px

Meta

12px








4.2 Font Usage





System font for UI
Monospace for:
IDs
hashes
system values










4.3 Rules





no oversized headings
no marketing typography
no dense paragraphs









5. LAYOUT SYSTEM










5.1 Page Structure



Top Bar
Main Content
Right Panel (optional)
Bottom Panel (conversation only)







5.2 Layout Types



Type

Use

List Layout

tables

Detail Layout

entity view

Split Layout

artifacts, runs

Queue Layout

review, ops








5.3 Grid





12-column layout
consistent gutters
no fluid improvisation









6. STATE MODEL (CRITICAL)








Every component must support:

Default
Hover
Focus
Selected
Disabled
Loading
Error
Blocked
Stale







6.1 Visual Representation





Loading → skeleton
Error → visible message + action
Blocked → yellow + reason
Stale → warning badge









7. CORE COMPONENTS










7.1 Table (MOST IMPORTANT)





Must support:



server-side pagination
multi-column sort
filtering
column toggle
row selection
bulk actions
sticky headers









7.2 Filters





left panel or top bar
multi-condition logic
saved views









7.3 Form Fields





label above input
inline validation
required indicators









7.4 Buttons



Type

Use

Primary

main action

Secondary

supporting

Tertiary

low priority

Danger

destructive








7.5 Badges





Used for:



status
SLA
ownership









7.6 Tabs





Used only for:



switching between entity sub-views









7.7 Panels



Panel

Use

Main

data

Right

context

Bottom

conversation








8. COMPLEX COMPONENTS










8.1 Run Timeline





vertical DAG
step states
current highlight









8.2 Diff Viewer





side-by-side
inline comments
version comparison









8.3 Review Panel





structured review actions
no chat mixing









8.4 Promotion Gate





checks
approvals
target
action









8.5 Capability Viewer





definition
lineage
usage
performance









9. UX PATTERNS










9.1 List → Detail Pattern





Mandatory:

List → Detail → Sub-detail → Trace







9.2 Queue Pattern





Queues must:



be actionable
show SLA
show blocking reason









9.3 Drill-Down Pattern





All analytics:

Metric → Request → Run → Step







10. RESPONSIVE & DENSITY










10.1 Density Modes





Standard
Compact









10.2 Wide Table Handling





horizontal scroll
column pinning
truncation rules









10.3 Breakpoints





Desktop-first
Mobile minimal support (read-only preferred)









11. ACCESSIBILITY










11.1 Required





keyboard navigation
focus states
ARIA roles
color contrast compliance









11.2 Screen Readers





semantic labeling
table accessibility









12. CONTENT & MICROCOPY










12.1 Language Rules





direct
action-oriented
consistent vocabulary









12.2 Error Messages





Must include:



what happened
why
how to fix









12.3 Confirmation Messages





explicit consequences
reversible indication









13. AI IMPLEMENTATION CONTRACT










13.1 AI MUST





use defined components only
follow layout patterns exactly
respect naming conventions
enforce state visibility









13.2 AI MUST NOT





invent new components
change terminology
mix concerns
introduce dashboards by default









13.3 Validation Checklist





Every screen must satisfy:

✔ Table-first
✔ Clear primary action
✔ No mixed concerns
✔ Visible state
✔ Drill-down supported
✔ Audit-safe







14. ANTI-PATTERNS










PROHIBITED





chat-driven UI
dashboard-first UX
card-based infinite scroll
hidden state transitions
mixed execution + review + chat in one surface
unstructured data presentation









FINAL DESIGN SYSTEM STATEMENT








This design system defines:

A deterministic, scalable, enterprise-grade interface system
for governed human + AI work







FINAL RESULT





You now have:





Architecture





✔ Complete





UX IA





✔ Complete





Style Guide





✔ Complete





Design System





✔ Complete





Implementation Contract





✔ AI-safe


