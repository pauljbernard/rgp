RGP UX STYLE GUIDE







Version 1.0 (Enterprise + AI-Buildable)










1. PRODUCT BEHAVIOR PRINCIPLES










1.1 The System Is Not a Chatbot





The platform SHALL:



not default to chat
not treat conversation as primary UX
not hide system state in conversation




Conversation is:

A supporting tool, not the system interface







1.2 Every Screen Must Answer:



What is happening?
What is blocking progress?
What can I do next?
If a screen does not answer all three, it is incomplete.








1.3 No Implicit Behavior





The system MUST NOT:



auto-transition states silently
auto-resolve errors without visibility
auto-approve anything without showing it




Everything must be:

Explicit, visible, explainable







1.4 Deterministic UX





Even if execution is non-deterministic:



the UI must always be predictable
actions must have consistent outcomes
state transitions must be explainable









2. LANGUAGE & TERMINOLOGY










2.1 Canonical Vocabulary (DO NOT DEVIATE)



Concept

Term

Unit of work

Request

Execution instance

Run

Output

Artifact

Evaluation

Review

Decision

Approval

Finalization

Promotion

No synonyms allowed.








2.2 Status Language





Statuses must be consistent:

Draft
Submitted
In Execution
Awaiting Review
Blocked
Approved
Failed
Completed
Never invent new variants.








2.3 Action Language





Use verbs:



Approve
Reject
Request Changes
Promote
Retry
Pause




Avoid vague language like:



“Process”
“Handle”
“Manage”









3. VISUAL CONSISTENCY RULES










3.1 No Decorative UI





The system SHALL NOT include:



gradients
decorative icons
animation without purpose
marketing-style visuals




This is a work system, not a marketing site.








3.2 Density Modes





Must support:



Standard (default)
Compact (high-density enterprise)









3.3 Alignment Rules





all tables align left
numeric values align right
actions align consistently









3.4 Visual Hierarchy





Priority:

State > Action > Data > Decoration







4. INTERACTION RULES










4.1 One Primary Action Per Screen





Each screen MUST have:

One dominant action
Example:



Request List → Create Request
Review → Approve / Request Changes
Promotion → Promote









4.2 No Modal Overuse





Modals are allowed ONLY for:



confirmations
destructive actions




Everything else:

→ full-page or panel








4.3 No Inline Complexity





Do NOT:



edit complex objects inline
embed workflows inside tables




Use:

→ detail views








4.4 Command vs Conversation Separation





Commands:



structured
explicit
auditable




Conversation:



unstructured
advisory




Never mix.








5. STATE DESIGN










5.1 State Visibility





Every entity must show:



current state
blocking conditions
next step









5.2 Blocking State (CRITICAL)





Blocked state must show:

What is blocking
Who owns the block
What action resolves it







5.3 Error Handling





Errors must be:



visible
actionable
persistent until resolved









5.4 Loading States





skeleton UI (not spinners)
never blank screens









6. TABLE BEHAVIOR STANDARD










6.1 Default Behavior





sorted by most relevant
paginated server-side
filterable immediately









6.2 Bulk Actions





Tables must support:



multi-select
bulk approve
bulk retry
bulk assign









6.3 Row Expansion





Rows MAY expand for:



preview
quick metadata




But not for full workflows.








7. REVIEW UX RULES










7.1 Review Is Not Chat





Review must:



attach to artifacts
be structured
be auditable









7.2 Required Signals





Every review must show:



reviewer
decision
timestamp
scope









7.3 Stale Review





Must be visually obvious:

⚠ Stale Review







8. ANALYTICS UX RULES










8.1 No Dashboard First





Start with:

Table → Drill → Insight







8.2 No Vanity Metrics





Every metric must:



tie to a decision
support drill-down









8.3 Comparison Required





All analytics must support:



before vs after
A vs B
trend over time









9. ACCESSIBILITY & INCLUSIVITY










9.1 Accessibility





keyboard navigation required
screen reader support
color-independent state









9.2 Internationalization





no hardcoded text
support localization









10. AI AGENT IMPLEMENTATION RULES










10.1 Do Not Invent UI





Agents must:



use defined patterns only
reuse components
not create new paradigms









10.2 No Creative Interpretation





AI must NOT:



redesign layouts
change terminology
introduce chat-first UX









10.3 Validation Checklist





Every generated screen must pass:

✔ Table-first
✔ Clear primary action
✔ No mixed concerns
✔ Visible state
✔ Drill-down enabled
✔ Auditability preserved







FINAL ASSESSMENT








Now you have:





UX Architecture





✔ Complete





Design System





✔ Defined





User Journeys





✔ Explicit





Screen Specs





✔ Buildable





Style Guide





✔ Enforced consistency








FINAL VERDICT





You now have:

A complete UX specification system
that can be reliably implemented by:
- human teams
- AI coding agents
- or hybrid approaches
