# CEW Professional Evidence Workbench — Reuse Map v1

**Status:** `VERIFIED_REUSE_DISCOVERY`  
**Purpose:** prevent parallel reimplementation while redesigning the Professional Evidence Workbench.  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Decision

The professional-workbench redesign must be **reuse-first**.

Repository-wide verification after the initial audit found mature CEW components that are not integrated into the current B1.8 dual-workspace route. The correct classification is therefore not simply “missing”, but in several cases:

`AVAILABLE_NOT_INTEGRATED`

This discovery does not make the current B1.8 screen professionally acceptable. It changes the implementation plan: reuse existing CEW capabilities rather than create parallel viewers, extractors or structural scenes.

## 2. F3 Source Viewer — reusable deep-zoom foundation

### Existing files

- `scripts/build_cew_source_viewer.py`
- `automation/CEW_SOURCE_VIEWER_CONTRACT_v1.json`
- related F3 validation/build workflows.

### Verified capability

The F3 source-viewer contract and builder already provide a professional-scale source-navigation foundation:

- OpenSeadragon 5.0.1;
- DZI multiresolution pyramids;
- 300 dpi source rendering;
- libvips `dzsave` tile generation;
- navigator/overview;
- zoom/pan;
- deep-linking to task / EvidenceRegion context;
- verified-source/read-only boundary.

### Reuse decision

The future Workbench Source Viewport should **reuse/evolve F3** rather than continue to scale a single B1.8 PNG with CSS transforms.

### Current integration state

`AVAILABLE_NOT_INTEGRATED`

The live B1.8 `/evidence/dual-workspace` still embeds the current Evidence Workspace rather than the F3 DZI source viewer.

## 3. Dual Vector Agreement — reusable document-geometry extraction governance

### Existing files

- `.github/workflows/dual-vector-agreement.yml`
- `scripts/extract_vector_geometry.py`
- `scripts/cew_docling_parse_vector_adapter.py`
- `scripts/cew_dual_vector_agreement.py`
- `scripts/validate_cew_dual_vector_agreement.py`
- `automation/CEW_DUAL_VECTOR_AGREEMENT_CONTRACT_v1.json`

### Verified capability

The repository already has a governed two-extractor geometry comparison pipeline using:

- PyMuPDF;
- Docling Parse;
- page-dimension comparison;
- vector/line/drawing counts;
- text spans and coordinates;
- agreement / disagreement / blocked states;
- explicit audit-only/non-authority semantics.

Neither extractor writes canonical engineering truth.

### Reuse decision

This is the correct upstream foundation for `DocumentGraphicPrimitive` and recognition provenance. It should feed the technical scene through a normalized workbench projection contract rather than be replaced by a new extraction stack.

### Current integration state

`AVAILABLE_NOT_INTEGRATED`

The B1.8 technical panel does not consume these vector outputs as a technical scene.

## 4. F6 ERW Synchronized Workspace — reusable structural scene and semantic synchronization

### Existing files

- `.github/workflows/validate-cew-erw-synced-workspace.yml`
- `scripts/build_cew_erw_synced_workspace.py`
- `scripts/validate_cew_erw_synced_workspace.py`
- `automation/CEW_ERW_CONTRACT_v1.json`
- frozen structural ledgers used by the workflow:
  - `data/canonical/M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv`
  - `data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv`

### Verified capability

The previous ERW implementation already contains:

- source-viewer shell reuse;
- structural model generated as SVG from frozen M0G ledgers;
- node and member graphics;
- selectable/clickable member semantics;
- source-evidence ↔ structural-member synchronization through a semantic event bus;
- member highlighting and source evidence navigation;
- read-only/frozen-input validation;
- no canonical mutation.

### Important boundary

This is **semantic synchronization by governed member identity**, not yet a general continuous spatial registration:

`SourceCoordinates ↔ TechnicalCoordinates`

Therefore it is reusable for selection/highlighting/object-scene architecture, but it does not by itself satisfy the audit requirement for registered split/overlay pan/zoom synchronization.

### Current integration state

`AVAILABLE_NOT_INTEGRATED`

The B1.8 dual workspace does not reuse this structural SVG/semantic synchronization surface.

## 5. B1.8 runtime and HVA hardening — reusable operational shell

### Existing capability

The current branch already provides:

- Render exact-revision identity;
- fail-closed authentication;
- persistent Neon audit readiness;
- deterministic managed-runtime render cache;
- revision-bound HVA session/receipt semantics;
- wrong-source non-compensable blocker;
- evidence zoom/pan/keyboard interaction prototype;
- provenance-safe proposal boundary;
- `canonical_write_authorized=false`.

### Reuse decision

These runtime, authority and HVA hardening mechanisms remain foundations. The visual/workbench redesign must not bypass or duplicate them.

### Current integration state

`IMPLEMENTED_FOUNDATION`

## 6. Capability reconciliation table

| Professional requirement | Existing CEW capability | Current status | Remaining work |
|---|---|---|---|
| Multiresolution source navigation | F3 OpenSeadragon + DZI | AVAILABLE_NOT_INTEGRATED | Integrate into new Source Viewport/runtime |
| Document vector extraction | PyMuPDF + Docling dual-vector agreement | AVAILABLE_NOT_INTEGRATED | Normalize primitives into technical-scene contract |
| Technical/structural SVG scene | F6 ERW M0G SVG | AVAILABLE_NOT_INTEGRATED | Reconcile with document/recognition layers and workbench client |
| Selectable technical/structural objects | F6 clickable members | AVAILABLE_NOT_INTEGRATED | Generalize hit-testing/object model beyond governed members |
| Semantic evidence↔member linking | F6 sync event bus | AVAILABLE_NOT_INTEGRATED | Preserve and generalize under explicit EvidenceLink |
| Continuous source↔technical spatial registration | none verified | NOT_IMPLEMENTED | Define `RegistrationTransform` and validity state |
| Synchronized pan/zoom | semantic sync only | NOT_IMPLEMENTED | Implement only when registration is valid |
| Overlay comparison | F6 contract anticipates overlay; no current B1.8 implementation verified | NOT_IMPLEMENTED | Design registered overlay mode |
| Layer manager | source/vector/structural capabilities exist separately | PARTIAL_FOUNDATIONS | Unify into typed layer model |
| Object-anchored recognized-text editing | no verified reusable implementation | NOT_IMPLEMENTED | Define WorkingEdit bound to technical object |
| Graphical ReadingIssue | states exist, graphical anchoring absent | NOT_IMPLEMENTED | Add ReadingIssue object + inspector |
| Dedicated workbench client/state engine | no verified reusable implementation | NOT_IMPLEMENTED | Design typed client architecture |
| Professional HVA | safety HVA exists | PARTIAL | Redesign around engineering task workflow |

## 7. Integration architecture rule

The redesign must connect existing components through explicit adapters/contracts rather than merge their authority semantics.

Target flow:

`SourceVersion/Page`
→ `F3 multires source viewport`

`SourceVersion/Page`
→ `dual-vector extraction/agreement`
→ `DocumentGraphicPrimitive / RecognizedText projection`

`M0G frozen structural records`
→ `structural scene adapter`

`EvidenceRegion / Observation`
→ `EvidenceLink / ReadingIssue`

all feeding:

`Professional Workbench Client`

while promotion remains outside the client under existing CEW governance.

## 8. Non-reuse / non-goals

Do not:

- build a second deep-zoom viewer while F3 exists;
- introduce a third independent vector extractor merely for the Workbench;
- rebuild M0G structural geometry from page pixels;
- infer structural identity from document coordinates;
- let F6 semantic links stand in for an unverified spatial registration transform;
- treat an SVG projection as canonical engineering state;
- let client edits write canonical registers directly.

## 9. Result

Repository verification materially reduces the redesign scope, but **does not clear professional readiness**.

The correct state is:

`FOUNDATIONS_REUSABLE = true`

`PROFESSIONAL_WORKBENCH_INTEGRATION = REQUIRED`

`PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED`

`HVA_EXECUTION_AUTHORIZED = false`

`B1_PROMOTION_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`
