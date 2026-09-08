# CEW Professional Evidence Workbench — Product Contract v1

**Status:** `DESIGN_BASELINE_PROPOSED`  
**Scope:** CEW B1 professional document/evidence work  
**Authority effect:** `NONE`  
**Canonical write:** `false`  
**Depends on:** Professional Workbench Audit v1 + Reuse Map v1

## 1. Product purpose

The Professional Evidence Workbench is the primary graphical working surface for an engineer who must read, compare, interpret and resolve uncertainty in existing structural documentation while retaining a reproducible evidence chain.

It is **not** a canonical model editor and it does not replace CEW promotion/governance.

Primary outcome:

`source inspection → technical representation → uncertainty resolution → governed proposal/evidence handoff`

## 2. Product principles

1. **Drawing first** — drawing work dominates the viewport.
2. **Direct manipulation** — navigation, selection and editing occur on graphical objects.
3. **Progressive disclosure** — technical work first, evidence second, full provenance on demand.
4. **Reuse first** — F3 deep zoom, Dual Vector Agreement, F6 structural scene/sync and B1.8 runtime hardening are reused through adapters.
5. **No invented engineering fact** — every visible technical object declares origin and state.
6. **Authority separation** — working edits and issues cannot mutate canonical engineering registers.
7. **Fail closed** — unavailable registration/binding/recognition remains explicit and disables dependent functionality.

## 3. Primary user jobs

The workbench must enable an engineer to:

- find and open the correct drawing/source version;
- orient and navigate a very large drawing efficiently;
- inspect detail without losing global position;
- compare the verified source with a clean technical representation;
- select a technical object and immediately reach its supporting source evidence;
- identify unreadable, conflicting or unresolved information;
- edit a recognized value as a non-canonical working proposal;
- confirm that an item is unreadable or cannot be resolved from available sources;
- inspect alternative evidence before deciding;
- distinguish source fact, recognition candidate, working edit and promoted engineering state;
- leave a reproducible review trail without learning internal CEW identifiers during normal work.

## 4. Workspace display modes

The product must support four persistent modes:

### SOURCE
Verified original source at maximum usable area.

### TECHNICAL
Derived vector/technical scene at maximum usable area.

### SPLIT
Source and technical views side by side.

### OVERLAY
Source and technical scene in one registered view with opacity/layer controls.

Mode switching must preserve location, selection and applicable view state.

## 5. Source authority contract

The primary verified source remains authoritative evidence.

Source panel/view may expose:

- immutable source identity;
- F3 deep-zoom tiles;
- EvidenceRegion outlines;
- source orientation/display rotation;
- source-space coordinates;
- links to full provenance.

Display state never changes source identity/content.

## 6. Technical representation contract

The technical representation is a **derived working projection**. It may contain:

- document linework/primitives;
- recognized text and dimensions;
- technical object candidates;
- governed structural objects when explicit bindings exist;
- reading issues;
- engineer annotations;
- working edits;
- validation/promotion-state indicators.

Every object must expose at least:

- stable workbench object id;
- object family/type;
- geometry in its declared coordinate space;
- provenance/evidence links;
- origin adapter/extractor;
- recognition/validation state;
- working-edit state;
- canonical/engineering authority state.

No technical object becomes canonical merely by being drawn, selected or edited.

## 7. Information-state model

The UI must distinguish, without relying only on colour:

- `SOURCE_DOCUMENTED`
- `EXTRACTED`
- `RECOGNIZED_CANDIDATE`
- `HUMAN_WORKING_EDIT`
- `HUMAN_CONFIRMED_READING`
- `OPEN_UNRESOLVED`
- `NOT_RESOLVABLE_FROM_CURRENT_SOURCES`
- `GOVERNED_BOUND`
- `PROMOTED` only when supplied by CEW authority state.

`HUMAN_CONFIRMED_READING` is still not automatically equivalent to a promoted engineering assertion.

## 8. ReadingIssue contract

A `ReadingIssue` is a first-class workbench object anchored to source and/or technical geometry.

Required states:

- `OPEN`
- `IN_REVIEW`
- `RESOLVED`
- `NOT_RESOLVABLE_FROM_CURRENT_SOURCES`

Required actions:

- inspect source;
- inspect context/other evidence;
- propose/edit reading;
- confirm reading;
- mark unreadable;
- leave unresolved;
- reopen when governed workflow allows.

Issue resolution produces a governed handoff/receipt or proposal artifact; it never directly writes canonical engineering truth from the client.

## 9. Registration and synchronization contract

Spatial synchronization is enabled only when a valid `RegistrationTransform` exists.

Possible states:

- `UNAVAILABLE`
- `PROPOSED`
- `VERIFIED`
- `REJECTED`
- `STALE`

Only `VERIFIED` may enable locked pan/zoom and overlay.

Semantic selection synchronization may exist without spatial registration when an explicit governed object/evidence relation exists. The UI must distinguish the two.

## 10. Progressive disclosure

Normal work surface:

- drawings;
- selected object;
- technical value/state;
- direct actions.

Evidence inspector:

- source region;
- alternative readings/evidence;
- recognition provenance;
- nearby context.

Provenance inspector:

- SourceVersion/Page/Transform/EvidenceRegion/Observation ids;
- hashes;
- epistemic/binding/promotion states;
- technical audit trail.

Internal identifiers must not dominate the default workspace.

## 11. Layer contract

The workbench scene must be layer-capable. Initial layer families:

1. source raster;
2. extracted document linework;
3. recognized text;
4. recognized dimensions;
5. technical candidates;
6. governed structural objects;
7. reinforcement annotations;
8. ReadingIssues;
9. engineer annotations;
10. validated/promoted indicators.

Layer visibility is view state, never authority state.

## 12. Device contract

### Desktop/laptop
Full professional SOURCE/TECHNICAL/SPLIT/OVERLAY modes and editing.

### Tablet landscape
Split when usable; otherwise rapid Source/Technical switching with inspector.

### Narrow/mobile
Review/inspection and issue triage. Dense dual-pane geometry editing is not required to have desktop-equivalent layout.

## 13. Accessibility contract

Essential operations must not depend solely on dragging.

At minimum:

- keyboard navigation and selection;
- keyboard/single-pointer pan and zoom alternatives;
- visible focus;
- labelled controls;
- state communicated by text/icon as well as colour;
- inspector/layers/issues operable by keyboard;
- target sizing consistent with WCAG 2.2 or documented exception.

## 14. Performance contract

Large source drawings must use F3-class multiresolution delivery rather than browser scaling of one full-page raster as the primary architecture.

Technical scenes must support viewport-aware rendering/culling when object count requires it.

Mode changes and selection must not require re-rasterizing the full PDF.

## 15. Reuse obligations

The implementation must reuse or explicitly supersede with evidence:

- F3 OpenSeadragon/DZI source viewer;
- Dual Vector Agreement extraction/comparison;
- F6 structural SVG/member semantics and evidence linking;
- B1.8 exact-revision/auth/audit safety boundaries.

Parallel replacements require a documented reason and compatibility proof.

## 16. Non-goals

This product contract does not:

- define a new engineering authority layer;
- reopen M0-G geometry;
- infer structural identity from drawing proximity;
- promote recognized data;
- make an HVA decision;
- authorize B1 promotion;
- authorize canonical writes.

## 17. Product acceptance gate

The Workbench may enter professional HVA only when automated evidence shows:

- drawing-first layout implemented;
- F3 deep zoom integrated;
- a real technical scene replaces the page-region placeholder;
- selectable technical objects;
- object-anchored WorkingEdit and ReadingIssue;
- explicit registration state;
- SPLIT and OVERLAY behave fail-closed;
- progressive disclosure implemented;
- layer model implemented;
- authority/canonical-write boundaries preserved;
- professional HVA protocol itself is versioned and ready.

Until then:

`PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED`

`HVA_EXECUTION_AUTHORIZED = false`
