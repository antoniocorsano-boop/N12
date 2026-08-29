# CEW Professional Evidence Workbench — Product / UX / Architecture Audit v1

**Status:** `AUDIT_COMPLETE — REWORK_REQUIRED_BEFORE_HVA`  
**Program:** CEW-GOAL-01 / CEW-B1 Source–Evidence Journey  
**Audited candidate:** `d510da26eef8293ed169c5d173962536a2a03b53`  
**Audited route:** `/evidence/dual-workspace?task=ERW-N12-001`  
**Authority effect:** `NONE`  
**Canonical write:** `false`  
**HVA consequence:** `PAUSED — PROFESSIONAL WORKBENCH REWORK REQUIRED`

## 1. Executive decision

The current B1.8 dual workspace is a valid **provenance-safe proof of concept**, but it is **not yet a professional engineering drawing workbench**.

The correct product direction is:

`governed evidence page → governed professional graphical workbench`

The existing CEW provenance, immutable-source, authority and fail-closed foundations are retained. The interaction and technical representation layer above them requires redesign before a new HVA round.

### Governing design principles

1. **Drawing first.** The drawing is the primary working surface.
2. **Direct manipulation.** Pan, zoom, selection, edit, compare and issue resolution happen on/around the drawing.
3. **Progressive disclosure.** Governance metadata is reachable in one step but does not dominate the working surface.
4. **Provenance everywhere, provenance UI only when needed.** Every derived object remains traceable without forcing the engineer to read internal IDs during normal work.
5. **No invented engineering facts.** A richer technical projection must never imply a governed structural identity that does not exist.

## 2. Strong foundations to preserve

The current implementation correctly preserves:

- verified primary source as authority;
- immutable SourceVersion / Page / Transform / EvidenceRegion chain;
- `geometry != identity`;
- `OPEN/ND` and `UNREADABLE` without silent completion;
- proposal editing as non-canonical session work;
- `canonical_write_authorized=false`;
- no engineering-authority effect;
- exact-revision HVA identity;
- fail-closed behavior when provenance is missing;
- managed-runtime render-cache hardening.

These are not redesign targets. They are constraints for the redesign.

## 3. Fundamental architectural finding — three geometries must be separated

The current implementation is too conservative at the presentation layer because it effectively collapses technical representation into documentary provenance.

CEW must distinguish three separate layers:

### 3.1 Document Geometry

Geometry directly recoverable from the source document:

- lines;
- polylines;
- arcs;
- contours;
- text bounding boxes;
- symbols;
- dimensions as graphic/text constructs;
- source-space regions.

This layer may be reconstructed graphically without asserting structural identity.

### 3.2 Technical Recognition

Candidate technical meaning derived from document geometry and recognition:

- recognized text;
- recognized dimensions;
- candidate grid axes;
- candidate beams/columns;
- candidate reinforcement annotations;
- candidate section labels;
- unresolved/alternative readings.

These remain candidates until governed validation. They do not create canonical structural identity.

### 3.3 Structural Interpretation

Governed engineering objects and relations:

- member identity;
- node identity;
- structural connectivity;
- model coordinates;
- authoritative section/armature assertions;
- promoted engineering claims.

This layer remains under the existing CEW authority/promotion process.

### Audit rule

`document geometry != technical candidate != structural identity`

A professional technical drawing can therefore be rich and useful before structural identity is promoted, provided every object carries provenance and state.

## 4. Current surface audit

| Area | Status | Finding |
|---|---|---|
| Source authority / provenance | STRONG | Correct and should be preserved |
| Visual hierarchy | CRITICAL | Governance and metadata precede engineering work |
| Source Panel | PARTIAL | Source is visible, but viewer is not yet a full professional drawing viewport |
| Technical Panel | BLOCKING | Current page-region map is not a technical drawing |
| Spatial comparison | BLOCKING | No governed source↔technical registration/synchronization |
| Technical object selection | BLOCKING | No selectable vector technical objects |
| In-place technical editing | BLOCKING | Proposal text is detached from drawing objects |
| Reading-issue resolution | BLOCKING | Uncertainty is not anchored to graphical technical objects |
| Overlay / comparison modes | MISSING | No professional overlay workflow |
| Layer control | MISSING | No layer manager for source/recognition/candidates/issues/validated data |
| Saved views | MISSING | View state is not a reusable engineering work object |
| Performance architecture | PARTIAL | Build-time raster cache solves runtime crashes but not final large-drawing navigation |
| Front-end architecture | CRITICAL | Python HTML templates + iframe + string-replacement enhancement are unsuitable for the target interaction complexity |
| Keyboard accessibility | PARTIAL | Existing zoom/pan keyboard support is useful and should be retained |
| Mobile strategy | MISALIGNED | Full dual-pane engineering editing should be desktop-first, not forced into narrow mobile parity |
| HVA design | REWORK | Existing HVA validates safety boundaries but not enough real engineering problem-solving |

## 5. Target product — CEW Professional Evidence Workbench

The next surface is not defined as “two HTML columns”. It is a graphical engineering workbench with four display modes:

- **Source** — verified original drawing at maximum usable area;
- **Technical** — derived technical/vector representation;
- **Split** — coordinated source and technical views;
- **Overlay** — source and technical projection registered in the same viewport with controllable opacity/layers.

A typical desktop work surface should prioritize the drawings and keep metadata in contextual inspectors.

## 6. Source viewport requirements

The source viewport should support:

- automatic useful orientation while retaining original orientation metadata;
- continuous pan;
- cursor-centred zoom;
- pinch-to-zoom;
- fit page / fit width / 100%;
- rotate;
- zoom-to-area;
- minimap or equivalent location awareness for long drawings;
- direct navigation to EvidenceRegions;
- return from evidence detail to full context without losing location;
- keyboard equivalents for pointer operations;
- stable viewport state.

### Rendering architecture finding

The current CSS-transform raster viewer is adequate for a governed prototype but not the final architecture for very large drawings. The target should use multiresolution/tiled delivery or an equivalent progressive source renderer so that zoom does not depend on one complete large raster.

The deterministic build-time render cache remains valuable as fallback/test infrastructure.

## 7. Technical viewport requirements

The technical panel must become an interactive vector/scene surface, not a metadata panel.

Minimum derived object families:

- `DocumentGraphicPrimitive`;
- `RecognizedText`;
- `RecognizedDimension`;
- `TechnicalObjectCandidate`;
- `EvidenceLink`;
- `WorkingEdit`;
- `ReadingIssue`;
- `RegistrationTransform`.

Every visible technical object must expose provenance and state.

### Example: recognized reinforcement text

A visible `2 Φ12` should be an object with, conceptually:

- text/value;
- source-space bbox/geometry;
- source/EvidenceRegion link;
- recognition state/confidence;
- validation state;
- proposed edit;
- history/receipt link where applicable.

Editing changes the working representation, not the source or canonical engineering state.

## 8. Source ↔ technical spatial registration

The workbench requires an explicit governed transformation:

`SourceCoordinates ↔ TechnicalCoordinates`

When a verified registration exists, the user may enable synchronized views:

- pan/zoom one viewport and follow the same location in the other;
- select a technical object and highlight its source evidence;
- select source evidence and centre the linked technical object;
- switch between split and overlay without losing location.

When registration is absent or uncertain, synchronization must be unavailable or explicitly degraded. Visual coincidence is never sufficient.

## 9. Layer model

The architecture must support layers even if the first implementation exposes only a subset.

Target conceptual layers:

- Original source;
- Extracted linework;
- Recognized text;
- Dimensions;
- Candidate axes;
- Candidate structural objects;
- Reinforcement annotations;
- Reading issues;
- Engineer annotations;
- Validated/promoted objects.

Layer visibility is a view preference, not an authority mutation.

## 10. Reading-issue workflow

Unknowns must be graphical work objects, not detached form fields.

A `ReadingIssue` is anchored to source and/or technical geometry and supports at least:

- `OPEN`;
- `IN_REVIEW`;
- `RESOLVED`;
- `NOT_RESOLVABLE_FROM_CURRENT_SOURCES`.

The contextual inspector should expose only what the engineer needs for the selected item:

- current reading;
- unresolved fields;
- proposed reading;
- source evidence;
- alternatives;
- actions: confirm / modify / unreadable / open context / inspect other evidence.

No action may silently promote canonical engineering facts.

## 11. Progressive disclosure

Three information levels are required:

### Level 1 — Work

Drawing, selected object, value, state, direct actions.

### Level 2 — Evidence

Source region, recognized reading, alternatives, relevant context.

### Level 3 — Provenance / audit

SourceVersion, Page, Transform, EvidenceRegion IDs, Observation IDs, hashes, epistemic ceiling, binding/promotion state.

Level 3 must be reachable quickly but must not occupy the normal drawing work surface.

## 12. Front-end architecture finding

The existing implementation uses:

- Python-generated monolithic HTML;
- iframe composition for the source surface;
- post-generation HTML enhancement through string replacement for viewer interaction.

This is acceptable as proof-of-concept infrastructure but is not an appropriate final base for:

- two synchronized viewports;
- vector object selection and hit-testing;
- layer management;
- overlay/registration;
- object inspectors;
- undo/redo;
- complex keyboard interaction;
- persistent views;
- large technical scenes.

### Target boundary

Preserve:

- FastAPI/runtime services;
- CEW data contracts and registries;
- source authority and provenance rules;
- managed-runtime hardening.

Introduce a dedicated typed client workbench/viewport layer above those services. The redesign must not create a parallel authority model.

## 13. Device strategy

The professional editing experience is **desktop/laptop first**.

- Desktop/laptop: full split/overlay workbench;
- Tablet landscape: split or rapid panel switching;
- Narrow/mobile: source/technical tabs, review/inspection capability, not forced parity with dense dual-pane graphical editing.

Responsive design is still required, but operational equivalence is not mandatory when the physical viewport makes professional dual-drawing work impractical.

## 14. Accessibility requirements

The redesign must preserve or improve existing keyboard support.

At minimum:

- no essential function depends solely on dragging;
- keyboard/single-pointer equivalents exist for pan/zoom/selection where practical;
- visible focus;
- target sizes/spacing meet WCAG 2.2 requirements or documented exceptions;
- state is not communicated by colour alone;
- object inspector and layer controls are keyboard-operable.

Reference: WCAG 2.2 SC 2.5.7 Dragging Movements and SC 2.5.8 Target Size (Minimum).

## 15. Professional benchmark observations

The target interaction pattern is consistent with current professional document/drawing review tools:

- Bluebeam Revu supports split views, synchronized views, document comparison and overlays; overlay alignment can use picked points/regions.
- Autodesk Docs supports drawing comparison in overlay or side-by-side modes and permits alignment adjustments.
- Trimble Connect 2D Viewer saves reusable Views containing zoom/page/measurements/markups.

These products are benchmarks for interaction patterns, not authority/data-model templates for CEW.

Reference sources reviewed 2026-08-29:

- Bluebeam Technical Support — Compare original PDFs with revisions; Split/sync views; Overlay Pages / alignment.
- Autodesk Help — Compare Sheets.
- Trimble Help — 2D Viewer Views.
- W3C — WCAG 2.2.

## 16. HVA redesign

A new HVA must test an engineering task, not the user's knowledge of CEW internals.

Representative workflow:

`find → orient → compare → identify uncertainty/discrepancy → inspect source → propose/correct → resolve or leave OPEN`

Observed dimensions should include:

- task completion;
- wrong source/object selection;
- context switching/loss of orientation;
- help requests;
- recovery from navigation/selection errors;
- authority confusion;
- baseline time/interactions without arbitrary pass thresholds.

Safety/authority blockers remain non-compensable.

## 17. Required design deliverables before implementation promotion

The redesign is not considered implementation-ready until the following are versioned:

1. **Professional Workbench Product Contract**;
2. **Interaction Architecture**;
3. **Technical Projection Model**;
4. **Rendering Architecture**;
5. **UX Wireframes / state maps** for desktop, tablet and narrow views;
6. **Professional HVA Protocol**.

## 18. Audit acceptance criteria

The audit is satisfied only when implementation evidence proves, at minimum:

- drawing-first visual hierarchy;
- true technical/vector representation beyond a page-region placeholder;
- selectable technical objects;
- source↔technical provenance-backed registration;
- split and overlay modes;
- synchronized navigation only when registration is valid;
- contextual technical editing anchored to objects;
- graphical ReadingIssue workflow;
- progressive disclosure of provenance;
- layer-capable architecture;
- suitable large-drawing rendering architecture;
- dedicated workbench client architecture or an equivalently maintainable interaction layer;
- accessibility alternatives to drag-dependent operations;
- professional HVA protocol implemented but not automatically passed.

## 19. Current decision

For candidate `d510da26eef8293ed169c5d173962536a2a03b53`:

`PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED`

`HVA_EXECUTION_AUTHORIZED = false`

`B1_PROMOTION_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

The current PR remains useful evidence of runtime/provenance/safety foundations, but the visible dual-workspace surface is not accepted as the final professional workbench.
