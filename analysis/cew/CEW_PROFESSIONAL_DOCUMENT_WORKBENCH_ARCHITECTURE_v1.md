# CEW Professional Document Workbench v1

## Purpose

Replace incremental viewer layout experiments with one stable professional inspection architecture while preserving the validated Document Discovery acquisition engine and authority boundaries.

The design follows mature technical-editor conventions: persistent primary navigation, dominant central canvas, contextual properties/decision inspector, viewport-anchored navigation controls, and a compact status bar.

## Frozen upstream baseline

- Document acquisition/runtime HVA baseline: `320755e66a7263f1842f73dc14fb9a0ea8ccd7f8`.
- Human orientation/zoom/pan/cluster-selection tranche: `5db4e6bdf1b7a6853edd342ef9cc914e0e74ad91`.
- The new workbench is UI-only and must not change PDF parsing, primitive discovery, clustering, SourceVersion/Page governance, learning receipts, or canonical write authority.

## Canonical workbench composition

`PRIMARY_SIDEBAR -> DOCUMENT_CANVAS -> CONTEXTUAL_INSPECTOR -> STATUS_BAR`

### Primary sidebar

A narrow activity rail selects vertically organized panels:

- Pagine
- Primitive
- Cluster
- Da verificare

The sidebar is for navigation and evidence discovery, not global viewport commands.

### Document canvas

The document remains the dominant visual authority. Supported viewport operations are:

- fit page;
- fit width;
- zoom in/out/reset;
- mouse-wheel zoom;
- drag pan;
- 90-degree rotation;
- direct cluster hotspot selection.

Viewport controls stay anchored to the viewport and do not move away with the document during pan.

### Contextual inspector

Without a selection, the inspector reports document/acquisition state. With a cluster selection, it reports geometry/provenance-oriented properties and explicitly states that semantic meaning is not assigned automatically.

The human decision form is shown only when project-local teaching is actually enabled by governed immutable SourceVersion + READY Page identities.

### Status bar

The bottom status bar provides compact persistent state:

- page;
- zoom;
- rotation;
- renderer/mode;
- primitive count;
- cluster count;
- source registration state;
- training state.

## Result semantics

Execution completion and evidence acquisition are separate states.

`ANALYSIS_COMPLETED` does not imply `GRAPHIC_EVIDENCE_FOUND`.

If analysis completes with `0 primitive` and `0 cluster`, the UI must show a warning/review-required state rather than a green success state:

`NESSUNA_REGIONE_GRAFICA_ACQUISITA -> VERIFICA_NECESSARIA`

## Authority invariants

- `semantic_authority = NONE` until explicit human project validation;
- automatic semantic labels remain disabled;
- unregistered preview training remains blocked;
- canonical write remains blocked;
- structural identity remains blocked;
- the original document remains evidentiary authority;
- the professional workbench is a reading/review surface only.

## Acceptance gate

The v1 tranche passes only when deterministic validation proves:

1. primary sidebar + dominant canvas + contextual inspector + status bar are present;
2. viewport navigation is compact and viewport-anchored;
3. zero-evidence completion is warning/review-required, not green success;
4. the decision form is contextual and hidden while training is blocked;
5. the new shell shadows only the HTML route and reuses validated async/session APIs;
6. canonical-write and semantic-authority boundaries remain unchanged.
