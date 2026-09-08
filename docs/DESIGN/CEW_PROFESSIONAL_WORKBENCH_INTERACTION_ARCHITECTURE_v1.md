# CEW Professional Evidence Workbench — Interaction Architecture v1

**Status:** `DESIGN_BASELINE_PROPOSED`  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Interaction objective

The workbench interaction model must support sustained engineering drawing work without forcing the user to manage CEW governance internals.

Primary interaction loop:

`navigate → select → inspect → compare → edit/resolve → verify evidence`

## 2. Workbench regions

### Global toolbar
Persistent, compact controls:

- mode: Source / Technical / Split / Overlay;
- pan / area zoom;
- fit / 100%;
- rotate;
- sync lock state;
- layer manager;
- issue list;
- provenance/details;
- undo/redo for working state only.

### Source viewport
F3/OpenSeadragon-based source canvas.

### Technical viewport
Vector/scene surface with selection and editing semantics.

### Context inspector
Collapsible side panel for selected object/issue.

### Status strip
Compact state only: source verified, registration state, working changes count, unresolved issues count. No dense provenance by default.

## 3. Viewport state

Each viewport owns explicit state:

- centre/location;
- zoom;
- rotation;
- active layers;
- selected object/evidence;
- hover target;
- display mode;
- registration id/revision;
- sync mode.

Viewport state is not source/model authority.

## 4. Workbench event model

The client uses typed events rather than DOM-string coupling.

Required event families:

- `VIEWPORT_TRANSFORM_CHANGED`
- `MODE_CHANGED`
- `LAYER_VISIBILITY_CHANGED`
- `SOURCE_EVIDENCE_SELECTED`
- `TECHNICAL_OBJECT_SELECTED`
- `REGISTRATION_STATE_CHANGED`
- `WORKING_EDIT_CREATED`
- `WORKING_EDIT_UPDATED`
- `WORKING_EDIT_REVERTED`
- `READING_ISSUE_SELECTED`
- `READING_ISSUE_STATE_CHANGED`
- `PROVENANCE_REQUESTED`

Events may change workbench state but cannot directly mutate canonical CEW records.

## 5. Selection model

Selection is single-primary with optional related highlighting.

Selecting a technical object must:

1. mark it as primary selection;
2. show its inspector;
3. expose evidence links;
4. highlight linked source evidence when available;
5. centre source only when the user requests it or sync policy permits.

Selecting source evidence must analogously expose linked technical objects.

No visual proximity creates a link.

## 6. Synchronization modes

### OFF
Viewports independent.

### SEMANTIC
Selection/highlight synchronized through explicit `EvidenceLink` / governed binding. Pan/zoom independent.

### SPATIAL_LOCKED
Available only with `RegistrationTransform.state=VERIFIED`. Pan/zoom/position synchronized through the transform.

If registration becomes `STALE/REJECTED/UNAVAILABLE`, the UI automatically drops to SEMANTIC or OFF and explains why.

## 7. Overlay interaction

Overlay requires verified spatial registration.

Controls:

- opacity slider;
- source/technical visibility toggles;
- layer visibility;
- difference/highlight mode only when defined by a versioned contract;
- alignment status and residual information in inspector, not as default clutter.

Overlay must fail closed when registration is invalid.

## 8. Navigation interaction

Source viewport:

- wheel/trackpad zoom at pointer;
- drag/space-drag pan;
- pinch zoom;
- double-click or explicit area zoom;
- fit page, fit width, 100%;
- rotate;
- minimap/navigation overview;
- keyboard alternatives.

Technical viewport uses equivalent navigation semantics so mode switching does not require relearning.

## 9. Object editing interaction

Editing begins from a selected object, never from a global unbound textarea.

Sequence:

`select object → Edit → change field/text → working preview → Save working edit / Cancel`

The inspector must show:

- source/current value;
- proposed value;
- state;
- evidence link;
- reason/comment when required;
- clear label `Working proposal — not canonical`.

Working edits support local/session undo/redo and later governed handoff.

## 10. ReadingIssue interaction

A ReadingIssue appears as a graphical marker/badge anchored to its geometry.

Selecting it opens a contextual inspector with:

- issue question;
- current candidate/readings;
- linked source evidence;
- unresolved fields;
- other relevant evidence;
- actions: Confirm, Modify, Unreadable, Open context, Leave open.

Issue lists filter/locate graphical markers but do not replace them.

## 11. Progressive disclosure interaction

Default inspector: work state/value/actions.

`Evidence` disclosure: source region + alternative readings + recognition origin.

`Provenance` disclosure: full IDs/hashes/epistemic/binding/promotion data.

The user never needs to copy an internal id to navigate normal work.

## 12. Keyboard model

Baseline shortcuts:

- `Space + drag` / arrows: pan;
- `+ / -`: zoom;
- `F`: fit;
- `1`: 100%;
- `R`: rotate 90°;
- `Esc`: clear/cancel selection/edit;
- `Enter`: open selected object/issue;
- `Ctrl/Cmd+Z`, `Ctrl/Cmd+Shift+Z` or platform equivalent: workbench undo/redo;
- tab order reaches toolbar, viewport, inspector and layer controls.

Shortcuts must not override browser/assistive-technology conventions without documented handling.

## 13. State recovery

Recoverable workbench state may persist locally/session-side by exact source/workbench revision:

- view mode;
- viewport positions;
- layer visibility;
- working edits;
- issue filter/selection.

Revision mismatch must invalidate or reconcile explicitly. Old working edits cannot silently attach to a new source/scene revision.

## 14. Error/fail-closed interaction

Examples:

- no registration → Sync spatial and Overlay disabled with explanation;
- missing technical scene → Source remains usable, Technical reports unavailable rather than fabricating geometry;
- stale evidence link → highlight disabled and issue marked stale;
- failed source tile → retry/error surface without substituting a different source/version;
- unsupported edit → read-only object, explicit reason.

## 15. Device modes

Desktop: split/overlay primary.

Tablet landscape: split where geometry remains usable; inspector may become drawer.

Narrow: Source/Technical tabs with inspector sheet; editing limited to operations that remain reliably usable.

## 16. Acceptance criteria

Interaction architecture is implemented only when automated/browser evidence proves:

- one typed state model drives all four modes;
- source/technical selection can round-trip through explicit links;
- SEMANTIC and SPATIAL_LOCKED are distinct;
- overlay cannot activate without verified registration;
- object editing is anchored to selected object;
- ReadingIssue is graphically anchored;
- provenance is progressively disclosed;
- keyboard alternatives cover essential interactions;
- revision mismatch fails closed.
