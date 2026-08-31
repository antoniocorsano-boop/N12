# CEW Enterprise Professional Workspace Model v1

**Status:** `DESIGN_BASELINE_PROPOSED`  
**Authority effect:** `NONE`  
**Canonical engineering write:** `false`  
**Supersedes for layout decisions:** `desktop: split/overlay primary` assumption in `CEW_PROFESSIONAL_WORKBENCH_INTERACTION_ARCHITECTURE_v1.md`.

## 1. Product thesis

CEW is a **Professional Work Operating System for evidence-first existing-building engineering**.

It is not:
- a PDF viewer with governance panels;
- a BIM viewer with issue forms;
- a dashboard that opens many unrelated tools;
- an AI detector that promotes its own results.

The core experience is:

`work queue → professional workspace → context-bound action → governed decision → durable receipt → next eligible work`

The operator should spend most of the session reading, selecting, comparing and deciding in context. Governance remains enforceable but normally lives one disclosure level below the work.

## 2. Enterprise domain model for interaction

The interface is driven by seven work objects.

### 2.1 WorkItem
A bounded professional objective such as:
- acquire columns on TAV-05S;
- resolve an unreadable reinforcement label;
- review a similarity cluster;
- verify continuity between drawings;
- accept/reject a structural identity candidate.

A WorkItem owns objective, eligibility, blockers, required evidence, allowed actions and completion condition.

### 2.2 WorkContext
The exact project/scope state needed to perform the WorkItem:
- Project;
- discipline/scope;
- SourceVersion/Page/EvidenceRegion;
- technical scene/revision when available;
- active object/family/issue;
- registration state;
- work mode.

### 2.3 ViewState
A recoverable visual context, separate from engineering authority:
- source page/zoom/rotation/centre;
- technical camera/zoom/visibility;
- layers;
- selected/isolated objects;
- clipping/compare state when relevant.

ViewState can be saved and linked to issues/decisions without becoming geometry authority.

### 2.4 EvidenceObject
The source-bound evidence unit: SourceVersion/Page/EvidenceRegion/Observation and related immutable provenance.

### 2.5 TechnicalObject
An operational object/candidate/projection. It may be selected, compared and edited in working state but does not become structural identity by proximity or similarity.

### 2.6 IssueTopic
A durable question, ambiguity, finding or blocker with:
- type;
- status;
- priority/severity;
- assignee/reviewer when applicable;
- linked ViewState;
- linked evidence/object candidates;
- discussion/history;
- resolution/decision links.

### 2.7 DecisionReceipt
An append-only human/system decision record. It records what was decided, by whom, against which exact revision/evidence, and its authority effect.

## 3. Product information architecture

### 3.1 Project Home — situational awareness
Purpose: answer **what requires attention and why**.

Contains:
- readiness/blocked state;
- work queues by professional objective;
- recent decisions/change signals;
- source/project health;
- navigation to domains.

Does not contain dense editing UI.

### 3.2 Work Queue / Inbox — operational prioritization
Purpose: answer **what should I work on next**.

Views:
- My work;
- Blocked;
- Needs human review;
- Changed since last review;
- By source / object type / severity / discipline.

Rows remain compact. Selecting an item opens the Professional Workspace at the exact WorkContext.

### 3.3 Professional Workspace — sustained engineering work
Purpose: perform one WorkItem without losing context.

This is the primary working environment and must be stable for hours of use.

### 3.4 Libraries — reusable project grammar
Includes:
- object families/prototypes;
- tool sets/templates;
- saved filters;
- saved views;
- project rules/controlled vocabularies.

Libraries are contextual resources, not a second source of engineering authority.

### 3.5 Issues / Decisions — durable coordination and audit
Global list/search/reporting surface for IssueTopics and DecisionReceipts. Opening one restores its ViewState and WorkContext in the Workspace.

### 3.6 Sources / Records
Document and provenance management surface. It owns versions, immutable identities, registration health and document lineage, not professional decisions themselves.

## 4. Professional Workspace anatomy

Desktop target uses a **viewport-bound application frame**. The browser page itself must not grow with work results.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Project / WorkItem / revision           Command bar          user/session   │
├───────┬───────────────────────────────────────────────────────┬──────────────┤
│       │                                                       │              │
│ Rail  │              PRIMARY WORK CANVAS                      │ Context Rail │
│       │                                                       │              │
│ tasks │ source / technical / compare according to WorkMode    │ object       │
│ views │                                                       │ issue        │
│ layer │                                                       │ actions      │
│ issue │                                                       │ blockers     │
│       │                                                       │ evidence     │
├───────┴───────────────────────────────────────────────────────┴──────────────┤
│ status / selection / registration / working changes / audit availability   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.1 Application frame
- height bounded to viewport after global header;
- no workspace-level vertical page growth;
- primary canvas and context rail have independent overflow behavior;
- context rail width adjustable within governed min/max bounds;
- bottom status strip remains visible.

### 4.2 Primary Work Canvas
The largest surface. Its rendering depends on WorkMode and registration state.

Never covered by persistent badges, forms or result cards.

### 4.3 Context Rail
A single contextual rail, not multiple stacked permanent panels.

Sections are progressively disclosed:
1. Active item/object;
2. Primary action;
3. Current blocker/readiness;
4. candidate/result set;
5. Evidence;
6. Provenance/Audit.

Long result sets are virtualized and scroll inside the rail.

### 4.4 Navigation / Work Rail
Compact optional rail for:
- work queue;
- saved views;
- layers;
- issue list;
- family library.

It can collapse to icons and must not compete with the canvas unless explicitly opened.

## 5. WorkMode model

The Workspace is **task-state dependent**, not mode-first. Only modes relevant to the current WorkItem are enabled.

### NAVIGATE
Default reading state. Pan/zoom/select only. No accidental editing.

### ACQUIRE
Teach/classify source or technical candidates. Primary pattern:
`select → classify → family/prototype → persist`.

### REVIEW_SET
Review detector/checker/similarity output. Pattern:
`summary → filter → active candidate → decision → next`.

### COMPARE
Version/sheet/scene comparison. Side-by-side, swipe or overlay chosen explicitly. Requires appropriate alignment semantics.

### RESOLVE_ISSUE
Issue-focused state. Restores issue ViewState, shows question/history and bounded resolution actions.

### EDIT_WORKING
Working proposal editing. Clearly non-canonical; undo/redo applies to working state.

### VALIDATE
Explicit human authority boundary. Shows only evidence/relations required to make the decision and blocks unrelated editing.

### PROVENANCE_AUDIT
Deep technical trace. IDs/hashes/revisions/audit lineage visible. Not the normal working mode.

Mode transitions are explicit events and may temporarily disable unrelated commands, following the same risk-control logic seen in mature CAD review modes.

## 6. View topology is state-dependent

There is no universal `Source / Technical / Split / Overlay` default.

### Source position UNREGISTERED
Default: `SOURCE_PRIMARY + CONTEXT_RAIL`.
Technical view is on-demand. Split/overlay cannot imply spatial relation.

### Explicit semantic binding but no spatial transform
Default may be source or technical according to WorkItem. `SEMANTIC_LINK` highlighting allowed; pan/zoom independent.

### VERIFIED spatial registration
Split or overlay can become eligible. They remain explicit modes, never automatic acceptance of alignment.

### Compare WorkItem
Comparison surface can take over the primary canvas because comparison itself is the task.

### Technical/model WorkItem
Technical/3D canvas may become primary, while source evidence opens in a context pane/drawer.

## 7. Result-set review model

Detector/checker/similarity results use a three-level model:

### Level A — Summary
- total;
- strong / possible / ambiguous / blocked counts;
- family/type;
- current review progress;
- filters.

### Level B — Review Set
Virtualized compact rows/cards with stable sort and filters. Never render the complete expanded payload for all results simultaneously.

### Level C — Active Candidate
Only one primary candidate at a time:
- focused/highlighted in canvas where binding permits;
- evidence/context visible;
- score explanation if applicable;
- bounded human decision actions;
- previous/next navigation.

Batch decision is available only after explicit selection and policy eligibility. No implicit whole-cluster confirmation.

## 8. Context continuity

Every meaningful issue/review decision should be capable of restoring:

`Project + WorkItem + SourceVersion + Page + EvidenceRegion + selected object(s) + ViewState + exact revision`

A snapshot may be generated for convenience, but immutable source/evidence links remain authoritative.

Deep links must never require the user to copy internal IDs manually.

## 9. Saved Views

CEW introduces `SavedView` as a first-class operational object.

It may store:
- source transform;
- technical transform;
- visible layers;
- selection/isolation;
- compare configuration;
- clipping when supported;
- linked IssueTopic/WorkItem.

It cannot store or imply canonical engineering truth.

## 10. Issue model

IssueTopic states are separate from evidence/object states.

Baseline lifecycle:
`OPEN → IN_REVIEW → NEEDS_EVIDENCE | READY_FOR_DECISION → RESOLVED | REJECTED | DEFERRED`.

Project-specific issue types may define different permitted transitions, but history is append-only.

Issue state color may be shown on pins/rows, while exact meaning remains accessible textually.

## 11. Object/family learning model

Project Symbol Grammar is exposed as a controlled library similar in spirit to professional tool/block libraries.

A family card shows:
- human-approved prototype(s);
- object type;
- project label;
- distinguishing dimensions/features;
- number of verified/candidate/ambiguous instances;
- source coverage;
- last review revision.

`Find Similar` opens REVIEW_SET; it does not append a full expanded list below the prototype form.

## 12. Command architecture

### Global commands
Project navigation, search, saved view, help, session state.

### Canvas commands
Pan/zoom/fit/rotate/layers; compare controls only when WorkMode=COMPARE; spatial sync only when eligible.

### Contextual commands
Only actions valid for the selected WorkItem/object/issue and current authority state.

### Dangerous/authority-bearing commands
Human validation/acceptance is visually separated from normal edit/navigation and requires explicit confirmation/attestation according to contract.

## 13. Progressive disclosure

Four levels:

1. **Work** — what am I doing; what is selected; what can I do next.
2. **Evidence** — source region, alternatives, related evidence.
3. **Reasoning** — similarity signals, relationship evidence, confidence/reason codes.
4. **Provenance/Audit** — internal IDs, hashes, revisions, receipts, authority fields.

The user should rarely need level 4 during normal review.

## 14. Enterprise usability invariants

- primary canvas minimum target: 65% of usable desktop width when only one contextual rail is open;
- context rail target: 320–440 px, resizable and independently scrollable;
- workspace height bound to viewport; no result list may extend the page height;
- primary action remains visible or recoverable without scrolling through the entire result set;
- long lists must be virtualized/paginated progressively;
- active selection remains visible while the rail scrolls;
- source status indicators live outside source content;
- toolbar is task-aware; unavailable actions explain why;
- focus/keyboard traversal supports sustained desktop work;
- state restoration is revision-bound and fail-closed.

Exact dimensions may evolve through HVA, but the invariants above cannot be removed without a versioned contract change.

## 15. Professional density levels

CEW supports controlled information density rather than one universal layout:

### Focus
Canvas + active item + primary action.

### Review
Canvas + result list + active candidate + issue/evidence summary.

### Audit
Canvas + provenance/audit detail + revision/receipt data.

Density changes do not alter authority.

## 16. System-wide navigation principle

The user navigates by **professional objects**, not internal modules.

Examples:
- Open source;
- Open support 18;
- Open family 40×40;
- Open unresolved issue;
- Open decision;
- Resume review set;
- Show exact evidence.

Internal stages F2/F3/OA/R2 remain inspectable in audit mode but do not define primary navigation labels.

## 17. Data and authority separation

The UI must always preserve:

`EvidenceObject != TechnicalObject != StructuralIdentity != DecisionReceipt`.

A SavedView, IssueTopic or UI selection cannot create identity.

A detector result cannot create type/family membership without the corresponding governed human/system rule.

A resolved IssueTopic does not automatically authorize canonical write.

## 18. Performance model

Enterprise usability requires:
- canvas rendering isolated from inspector/list rendering;
- virtualized candidate/issue lists;
- lazy evidence/provenance loading;
- bounded thumbnails;
- incremental search/filter;
- no re-render of source tiles when only rail state changes;
- cancellable asynchronous analysis;
- explicit loading/partial/error states.

## 19. Accessibility and input

- keyboard equivalent for every essential review action;
- visible focus;
- no color-only state semantics;
- scalable density/text;
- tooltips plus textual disabled reasons;
- pointer/trackpad precision without requiring tiny targets;
- tablet adaptation via drawers/tabs, not desktop page shrink.

## 20. Migration from current Workbench

### EWS-0 — Freeze model
Persist research, enterprise model and contract. No runtime change.

### EWS-1 — Application frame
Viewport-bound workspace, independent canvas/rail scroll, eliminate page-growth failure.

### EWS-2 — Unified context rail
Replace accumulated OA/R2 panels with task-driven sections.

### EWS-3 — WorkMode controller
Explicit NAVIGATE/ACQUIRE/REVIEW_SET/COMPARE/RESOLVE/EDIT/VALIDATE/AUDIT state machine.

### EWS-4 — Result Review Controller
Summary → virtualized set → active candidate; previous/next; filters; batch eligibility.

### EWS-5 — SavedView / Context restoration
Revision-bound visual state and deep links.

### EWS-6 — IssueTopic unification
Context-bound issues across source, technical and future model surfaces.

### EWS-7 — Libraries
Project object-family/tool grammar as reusable managed resource.

### EWS-8 — Enterprise HVA
Multi-hour professional tasks, keyboard, density, error recovery, large result sets, revision mismatch and audit drill-down.

## 21. Immediate consequence for OA G4 pilot

The current long right-hand result stack is not accepted as enterprise UX.

The next runtime tranche must implement EWS-1 + the OA subset of EWS-4:
- bounded workspace;
- independent right-rail scroll;
- source canvas remains full-height;
- similarity results summarized first;
- compact virtualized/restricted result list;
- one active candidate with previous/next review;
- no OA-G5/OA-6 expansion while this UX gate is incomplete.

## 22. Acceptance doctrine

A screen is not enterprise-ready because features are present. It is ready only when a professional user can complete the bounded task with:
- stable context;
- low navigation overhead;
- explicit state;
- no accidental authority transition;
- recoverable evidence;
- bounded visual density;
- predictable keyboard/pointer behavior;
- performance that does not degrade linearly with result count.
