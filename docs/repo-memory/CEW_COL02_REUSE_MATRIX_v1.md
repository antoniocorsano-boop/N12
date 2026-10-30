# CEW-COL-02 Reuse Matrix v1

**Status:** ACTIVE / PRE-IMPLEMENTATION GATE  
**Date:** 2026-10-30  
**Purpose:** identify the smallest reusable OA/OAR capability slices before any COL-02 implementation and prevent another standalone column detector.

## Decision summary

COL-02 must not start from a new global detector. The reusable historical path is:

`human/project-local footprint prototype -> page-wide geometric occurrence proposals -> local topology -> explicit text-to-footprint binding -> target-explicit Human Review`

Only the **text-to-footprint binding** and the **target-explicit review presentation** are clearly residual capabilities not already represented by the historical OA/OAR stack.

## Reuse matrix

| Capability | Historical source | Disposition | Reusable core | Required adaptation / residual gap | Authority |
|---|---|---|---|---|---|
| Project-local human prototype | PR #136 `scripts/cew_oar_g4_prototype_search.py`; PR #118 `scripts/cew_oa2_workbench_runtime.py` | **ADAPT, DO NOT REBUILD** | human-selected rectangular footprint; governed prototype receipt; source/page provenance; project-local training example | decouple prototype creation from a pre-known support ID/family when used for discovery; preserve explicit human teaching | training/retrieval only |
| Page-wide footprint similarity | PR #136 `scripts/cew_oar_g4_prototype_search.py` | **REUSE CORE** | scale similarity, aspect-ratio similarity, rectangularity, envelope preference, prototype-region exclusion, NMS, no tap-distance dependency | remove dependence on historical family expected-count as anything beyond benchmark/context; requalify thresholds on current exact source | proposal only |
| Raster footprint proposal generation | PR #136 `scripts/cew_oar_g4_snap_worker.py` | **ADAPT CORE** | `LONG_AXIS_SUPPRESSED` channel; raw contour channel; nested-subcontour suppression; rectangularity/envelope measurements | historical `FAMILY_RATIOS` must not become a production identity oracle; candidate admission should be driven by prototype compatibility / broad geometry rather than known support family labels | interaction/retrieval aid only |
| Axis handling | PR #136 `cew_oar_g4_snap_worker.py` | **DIRECT PRINCIPLE REUSE** | long horizontal/vertical line suppression before contouring; axes not required for a candidate | retain axes only as optional downstream evidence; never use axis absence to reject a prototype-compatible elongated footprint | non-authoritative evidence |
| Similarity signal framework | PR #118 `scripts/cew_oa3_workbench_runtime.py` | **ADAPT** | explainable deterministic signals; `GEOMETRY_KIND`, `DIMENSION_RATIO`, `ORIENTATION`, `TOPOLOGY_HINT`, `SPATIAL_CONTEXT`, `ASSOCIATED_TEXT`; human review required | `ASSOCIATED_TEXT` must be replaced/refined by an explicit spatial relation such as `TEXT_CONTAINED_IN_FOOTPRINT` or strongly bound text; global nearby OCR must not raise identity | ranking only |
| Numeric/text extraction | COL-01 exact-source OCR runner | **KEEP AS AUXILIARY, NOT PRIMARY** | deterministic OCR observations and visible OCR failure | run OCR in/around a selected footprint; record containment/overlap and distinguish dimension text outside the footprint; no expected-ID repair | relational evidence only |
| Human cluster review persistence | PR #118 `scripts/cew_oa4_workbench_runtime.py` | **REUSE GOVERNANCE / ADAPT UI** | explicit candidate selection; per-candidate decision; governed append-only receipt linked to prototype; no implicit cluster acceptance | review panel must show exact machine footprint and exact OCR/text target, plus unmodified source crop; panel-level “column visible” must not validate an unrelated OCR ID | human graphical decision only |
| G4 support/family register | PR #132 `automation/CEW_OAR_G4_COLUMN_PILOT_INPUT_v1.json` | **BENCHMARK ONLY** | 34 support identities; five candidate families; elongated witnesses `18`,`23`,`30` | prohibited as candidate generator, missing-ID injector or automatic family assignment | historical evidence / recall benchmark |
| Fixed lines / analytical axes / section placement | issues #2 and #5 | **OUT OF COL-02** | downstream requirements and blockers are already documented | do not mix retrieval with fixed-line, offset, section or chain attribution | downstream engineering gate |
| Structural identity / canonical CAD promotion | OA-5/OA-G5 governance | **OUT OF COL-02** | existing fail-closed authority boundary | no promotion from prototype similarity, OCR containment or graphical Human Review | not authorized |

## Concrete historical evidence behind the dispositions

### 1. Prototype search already solves most of footprint-first retrieval

`cew_oar_g4_prototype_search.py` already:

- converts a human bbox into an `ObjectPrototype` with provenance;
- ranks page-wide proposals without tap distance;
- scores footprint size and aspect ratio against the human example;
- includes rectangularity and an axis-suppressed envelope preference;
- excludes the taught prototype region;
- performs candidate-level NMS;
- returns `support_identity = None`;
- requires human group review;
- keeps canonical and structural authority false.

This is the preferred retrieval core for COL-02.

### 2. The old raster worker already contains the relevant axis/inner-cell repair

`cew_oar_g4_snap_worker.py` creates both `LONG_AXIS_SUPPRESSED` and `RAW_CONTOUR` candidates. It removes long horizontal/vertical runs before contour extraction and suppresses nested raw candidates by containment/relative area. Its own documentation states that the earlier family-equality logic failed when a crossing axis made an internal cell look rectangular while the outer footprint remained the correct candidate.

COL-02 should reuse this **geometric repair principle**, not recreate an axis-intersection detector.

### 3. OA-3 already treated text as one signal, never as identity

OA-3 assigns `ASSOCIATED_TEXT = 0.15` in an explainable similarity score and explicitly keeps all resulting candidates non-authoritative. COL-01 shows that the old generic notion of “associated text” is too weak spatially for TAV-05S: a nearby dimension can be mistaken for the support number.

The residual capability is therefore **spatial text binding**, not the invention of text-aware similarity.

### 4. OA-4 already owns explicit human candidate decisions

OA-4 requires explicit candidate selection and persists a governed append-only review receipt linked to the OA-2 prototype. It forbids implicit cluster acceptance and leaves structural identity/canonical write false.

The missing element is presentation precision: the old candidate list is text-oriented and does not make the exact footprint target and exact OCR target visually explicit. COL-02 must adapt the review artifact/UI accordingly.

## Residual implementation scope for COL-02

A new implementation is justified only for these bounded residuals:

1. **Footprint candidate adapter** — feed current exact-source neutral/proposal geometry into the reusable prototype-search core without requiring a known support identity.
2. **Text-footprint spatial binder** — for each footprint proposal, classify OCR/text relation as at least:
   - `INSIDE_FOOTPRINT`;
   - `INTERSECTS_FOOTPRINT`;
   - `NEAR_OUTSIDE_FOOTPRINT`;
   - `UNRELATED_OR_UNBOUND`.
3. **Target-explicit review artifact** — visually distinguish:
   - proposed footprint;
   - proposed OCR/text token;
   - containment relation;
   - untouched source-only crop.
4. **Governed review adapter** — persist human graphical decisions through existing OA-style receipt semantics without creating structural identity.
5. **Exact-source qualification** — replay on immutable TAV-05S and measure recall/false associations, with mandatory witnesses `18`, `23`, `30` used only for benchmark evaluation.

## Explicit non-goals

COL-02 must not:

- create a new generic column detector if the historical prototype-search core can be adapted;
- require symmetry axes;
- infer support identity from nearest OCR text;
- inject expected IDs from the 34-support register;
- assign section/family automatically;
- solve fixed lines or analytical offsets;
- create structural identity;
- write canonical CAD/project data.

## Entry gate for implementation

Implementation may begin only after this matrix is treated as the active reuse contract. The first TDD test must target the **residual text-footprint binding behavior**, not re-test whether a completely new column subsystem exists.
