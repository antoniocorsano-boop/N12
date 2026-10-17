# ETW-1 — eTwin Document Engine Core (v1.1)

## TL;DR
Build the document engine that proves: **large PDF → persistent map → adaptive tessellation → evidence → eTwin entity/candidate → verification → exact return to original region**. Start from baseline `d521f11`. No new subsystems unless required by ETW-1 gate.

## Objective
Demonstrate a complete, reproducible document chain from one original carpenteria PDF through OriginalDocument → DocumentMap → SemanticRegion → adaptive Tiles → EvidenceCrops → eTwin entity/candidate binding → Verification with multi-criteria result, using the terrace region as the test case. Prove knowledge persistence across interruptions.

## Non-goals
- FEM modeling, EdiLus, IFC, Sismabonus, interventions
- Modifying existing canonical data
- Automatic promotion of ND/INF to DOC
- New dependencies beyond Python standard library + Pillow + numpy
- Dashboard UI changes (dashboard is downstream consumer)

## Discovery
- `archive/documentazione_originaria/`: 18 PDFs, all pure JPEG2000 raster (0 text, 0 vectors)
- `docs/FOGLIO_LAVORO/M0S_DXF_TEXT_INVENTORY_TAV5.csv`: 750 text entities with handles, layers, coordinates
- `docs/FOGLIO_LAVORO/M0S_DXF_TEXT_MEANINGFUL_TAV5.csv`: 502 filtered entities
- `data/canonical/tavole_originali_manifest.csv`: 18 PDFs with SHA256
- `data/canonical/m0s1a_level_sheet_crosswalk.csv`: level→PDF mapping (6 rows)
- No DXF files in repo (referenced but not committed)
- No eTwin code/data exists anywhere
- **PDF rendering**: Pillow may not handle JPEG2000 natively — must verify before building anything

## Decisions
1. **Python for document engine** — PDF handling, image processing, tile generation all natural in Python. Dashboard stays TypeScript.
2. **No new dependencies** — use only PIL/Pillow, numpy (already in .venv), standard library. No opencv, no pytesseract. If Pillow cannot render PDFs without degradation, ETW-1 declares the gap.
3. **DXF as supplementary source only** — since DXFs are not in repo, use extracted inventories as evidence. Real DXF parsing when files are committed.
4. **Evidence-first architecture** — every eTwin property must trace to a crop, claim, and original document. No "magic" inference.
5. **Terrace as test case** — already has RIF evidence, 4 pillars, known terminal node. Proves the chain end-to-end.
6. **Append-only state** — reading progress persists to JSON. Resume from any point without data loss.
7. **N041 remains a candidate** — not promoted to StructuralEntity until riconciliazione. R-R1-01 identity gap is active.
8. **Adaptive hierarchical tessellation** — grid size is not fixed; the system chooses tile size based on content density and text legibility.
9. **Multi-criteria verification** — MATCH requires combination of EVIDENCE_EXISTS + SPATIAL_ALIGNMENT + IDENTITY_MATCH + PROPERTY_SUPPORT + SOURCE_CONSISTENCY. Existence alone is insufficient.

## Architecture

```
archive/documentazione_originaria/*.pdf  (18 files, immutable)
         │
         ▼
  ┌─────────────────────────────────────────────┐
  │  OriginalDocument                           │  SHA256, metadata, page count
  │  (from manifest CSV)                        │  page dimensions, raster resolution
  └──────────────┬──────────────────────────────┘
                 │
  ┌──────────────▼──────────────────────────────┐
  │  DocumentMap                                │  PDF → page → semantic regions
  │  (persistent, versioned)                    │  Each region has bboxNative + bboxNormalized
  └──────────────┬──────────────────────────────┘
                 │
  ┌──────────────▼──────────────────────────────┐
  │  SemanticRegion                             │  PLAN | TITLE_BLOCK | SCHEDULE | DETAIL
  │  (semantic, not spatial)                    │  bboxNative + bboxNormalized
  └──────────────┬──────────────────────────────┘
                 │
  ┌──────────────▼──────────────────────────────┐
  │  Tile                                       │  Adaptive spatial window for reading
  │  (deterministic, overlapping)               │  bboxNative + bboxNormalized + pixel coords
  └──────────────┬──────────────────────────────┘
                 │
  ┌──────────────▼──────────────────────────────┐
  │  EvidenceCrop                               │  Proof of a claim
  │  (per-element, reproducible)                │  bboxNative + bboxNormalized + crop path
  └──────────────┬──────────────────────────────┘
                 │
  ┌──────────────▼──────────────────────────────┐
  │  eTwin Entity/Candidate Binding             │  Entity OR Candidate → property → claim
  │  (N041 remains candidate until reconcile)   │  → evidence → crop → PDF
  └──────────────┬──────────────────────────────┘
                 │
  ┌──────────────▼──────────────────────────────┐
  │  Verification (multi-criteria)              │  EVIDENCE_EXISTS | SPATIAL_ALIGNMENT |
  │  (not just "crop exists")                   │  IDENTITY_MATCH | PROPERTY_SUPPORT |
  └─────────────────────────────────────────────┘  SOURCE_CONSISTENCY → MATCH
```

## Coordinate System

Every observation stores:
- `bboxNative`: coordinates in the original PDF coordinate space (points, origin bottom-left)
- `bboxNormalized`: coordinates as fractions [0..1] of page dimensions
- `pixelCoords`: (x, y, width, height) in raster image space at current DPI
- `dxfCoords`: (x_mm, y_mm) when mapped to DXF TAV5 coordinate system

Coordinate transformations:
- `PDF → pixels`: multiply by DPI/72
- `PDF → normalized`: divide by page width/height
- `PDF → DXF`: affine transform calibrated from known control points (pillars, grid intersections)

## TODOs

### Task 0: Source Rendering Fidelity Gate
Verify that the rendering pipeline produces output faithful to the original PDFs.

- **Files:** `model/etwin/rendering_fidelity.py`
- **What:** Select one of the 18 PDFs (tavola 5, carpenteria G4 — 1160KB, 1 page). Determine:
  - Physical page size (points and mm)
  - Embedded raster dimensions (pixels)
  - Effective resolution (DPI)
  - Whether JPEG2000 can be extracted losslessly
  - Whether overview and crops can be produced without destructive resampling
  - Coordinate transformation: page coordinates ↔ source pixels
  - Generate: full-page overview, crop of small text (cartiglio), crop of a dimension annotation, crop of a structural detail
  - Visually compare with original PDF viewer
- **RED:** If Pillow cannot open the PDF or produces visibly degraded output, STOP and declare the gap.
- **GREEN:** Overview is indistinguishable from PDF viewer at 100%. Crops preserve text legibility. Coordinate transform is invertible.
- **Real-surface QA:** Open generated overview in image viewer. Open original PDF in PDF viewer. Compare side-by-side at same zoom. Check a dimension annotation crop for legibility.
- **Cleanup:** Remove failed outputs if fidelity is insufficient.
- **Commit:** YES — `feat(eTwin): source rendering fidelity gate`
- **Note:** This is the critical gate. If rendering degrades the source, all downstream work is compromised.

### Task 1: Document Engine Data Model
Define the Python dataclasses that represent the eTwin document chain.

- **Files:** `model/etwin/__init__.py`, `model/etwin/document_engine.py`
- **What:** Create dataclasses:
  - `OriginalDocument`: SHA256, path, metadata, page count, page dimensions
  - `DocumentMap`: page → semantic regions (persistent, versioned)
  - `SemanticRegion`: PLAN | TITLE_BLOCK | SCHEDULE | DETAIL | ELEVATION | SECTION; bboxNative + bboxNormalized; semantic label
  - `Tile`: adaptive spatial window; bboxNative + bboxNormalized + pixel coords; overlapping, deterministic
  - `EvidenceCrop`: proof of claim; bboxNative + bboxNormalized + crop path; method, status, confidence
  - `Claim`: what is asserted; source entity; evidence refs
  - `StructuralEntity`: confirmed identity (N002, N005, N039 only for terrace)
  - `DocumentEntityCandidate`: unresolved identity (N041 — R-R1-01 active)
  - `PropertyResolution`: entity/candidate → property → claim → evidence → crop → PDF
  - `VerificationResult`: multi-criteria (EVIDENCE_EXISTS | SPATIAL_ALIGNMENT | IDENTITY_MATCH | PROPERTY_SUPPORT | SOURCE_CONSISTENCY)
  - Include serialization to/from JSON. All coordinate fields present on every geometric object.
- **RED:** No existing tests to break.
- **GREEN:** `python -c "from model.etwin.document_engine import *; print('OK')"` succeeds.
- **Real-surface QA:** Import works, dataclasses can be instantiated with example data, JSON round-trip preserves all fields.
- **Cleanup:** None needed.
- **Commit:** YES — `feat(eTwin): define document engine data model`
- **Files:** `model/etwin/__init__.py`, `model/etwin/document_engine.py`

### Task 2: Document Registry Loader
Load the 18 PDFs from manifest into `OriginalDocument` objects.

- **Files:** `model/etwin/document_registry.py`
- **What:** Read `data/canonical/tavole_originali_manifest.csv`, create `OriginalDocument` instances with SHA256, path, metadata. Validate file existence against `archive/documentazione_originaria/`. Use rendering fidelity results (Task 0) to populate page dimensions and resolution.
- **RED:** Write a test that tries to load non-existent manifest — should raise error.
- **GREEN:** `python -m model.etwin.document_registry` prints 18 documents loaded with page dimensions.
- **Real-surface QA:** Run script, verify all 18 PDFs found and SHA256 match manifest.
- **Cleanup:** None.
- **Commit:** YES — `feat(eTwin): document registry loader from manifest`

### Task 3: Adaptive Document Map Generator
Generate semantic regions and adaptive tile grids for any PDF page.

- **Files:** `model/etwin/document_map.py`
- **What:** Given an `OriginalDocument` + page number:
  1. Detect semantic regions (cartiglio, plan, schedule, detail) based on page content and known structure from DXF inventories
  2. For each region, generate adaptive tile grid:
     - Start with coarse tiles (overview level)
     - Subdivide if text is illegible at current resolution
     - Add deterministic overlap between tiles (configurable, default 10%)
     - Record bboxNative + bboxNormalized + pixel coords for each tile
  3. Persist map to JSON (append-only, resumable)
  4. Generate actual tile images from PDF using the rendering pipeline validated in Task 0
- **RED:** Test with a non-existent page number — should raise ValueError.
- **GREEN:** Generate document map for page 1 of tavola 5 (carpenteria G4). Save tiles to `docs/FOGLIO_LAVORO/etwin_crops/tav5_page1/`. Map persisted to JSON.
- **Real-surface QA:** View generated tiles visually. Verify overlap exists, coordinates are deterministic (regenerate → identical output), image quality matches source.
- **Cleanup:** Remove test crops if validation fails.
- **Commit:** YES — `feat(eTwin): adaptive document map generator`

### Task 4: Persistent Reading State
Reading state that survives process restarts.

- **Files:** `model/etwin/reading_state.py`
- **What:** JSON-based state persistence. Track: which tiles have been read, what observations were made, extraction method used, confidence, claims generated. Support resume from last saved state. Append-only: new observations never delete previous ones. Demonstrate: analyze some tiles → stop → restart → analyze more → verify earlier observations intact.
- **RED:** Write state, delete process, reload — state must be identical.
- **GREEN:** Create state, add 3 observations, save, reload, verify all 3 present. Then add 2 more, save, reload, verify all 5 present (including first 3).
- **Real-surface QA:** Manual write/save/reload cycle with verification of append-only behavior.
- **Cleanup:** None.
- **Commit:** YES — `feat(eTwin): persistent reading state manager`

### Task 5: Terrace Case — Document Map + Evidence Crops
Generate document map for the terrace region test case.

- **Files:** `model/etwin/terrace_probe.py`
- **What:** Use tavola 5 (G4 carpenteria) as source. Generate document map for the terrace region (upper-right quadrant of plan). Link to 4 pillars (N002, N005, N039 as confirmed; N041 as candidate) using DXF position data. Create evidence crops for:
  - Cartiglio (title block)
  - Level label
  - Terrace region overall
  - Each of 4 pillar annotations (N041 labeled as candidate)
  - 3 dimension annotations
  - 3 beam labels
- **RED:** Terrace probe script should produce at least 15 evidence crops.
- **GREEN:** Run `python -m model.etwin.terrace_probe`, verify crops saved with metadata. Each crop has bboxNative + bboxNormalized. N041 crops are labeled as candidate evidence.
- **Real-surface QA:** View each crop, verify it contains the claimed structural element. Verify N041 crops exist but entity is DocumentEntityCandidate.
- **Cleanup:** Remove invalid crops.
- **Commit:** YES — `feat(eTwin): terrace probe with document map and evidence crops`

### Task 6: eTwin Entity/Candidate Binding
Bind terrace entities to eTwin properties.

- **Files:** `model/etwin/entity_binding.py`
- **What:** Create `StructuralEntity` instances for N002, N005, N039 (confirmed pillars). Create `DocumentEntityCandidate` for N041 (R-R1-01 active). Bind properties: position, vertical extent, termination reason. Link each property to evidence crops from Task 5. Demonstrate chain: `Entity/Candidate → Property → Claim → Evidence → Crop → PDF`. N041 chain must show: candidate → evidence → unresolved identity.
- **RED:** Each confirmed entity must have at least 1 bound evidence crop. N041 must be DocumentEntityCandidate with evidence but unresolved identity.
- **GREEN:** `python -m model.etwin.entity_binding` prints entity chain for each terrace pillar. N041 shows "candidate" status with evidence chain.
- **Real-surface QA:** Verify chain trace: select N041 → see candidate status → see evidence crop → see DXF source text → see UNRESOLVED identity.
- **Cleanup:** None.
- **Commit:** YES — `feat(eTwin): terrace entity/candidate binding with evidence chain`

### Task 7: Multi-Criteria Verification Engine
Compare eTwin entities against source documents with proper multi-criteria analysis.

- **Files:** `model/etwin/verification.py`
- **What:** For each bound entity/candidate, check:
  1. `EVIDENCE_EXISTS`: does evidence crop exist on disk?
  2. `SPATIAL_ALIGNMENT`: does crop bbox match expected region (within tolerance)?
  3. `IDENTITY_MATCH`: does crop text/content confirm entity identity?
  4. `PROPERTY_SUPPORT`: does crop support the claimed property value?
  5. `SOURCE_CONSISTENCY`: are there conflicting claims from other sources?
  
  Produce `VerificationResult` per entity per property. Only the relevant combination of criteria produces `MATCH`. Existence alone is insufficient.
  
  Verification statuses: `MATCH`, `PARTIAL_MATCH`, `MISSING_IN_TWIN`, `MISSING_IN_DOCUMENT`, `GEOMETRY_MISMATCH`, `CONFLICT`, `UNRESOLVED`.
- **RED:** Verification of unbound entity should return UNRESOLVED. Verification of entity with crop but no identity confirmation should return PARTIAL_MATCH or UNRESOLVED, not MATCH.
- **GREEN:** Run verification on terrace pillars. N002/N005/N039: at least EVIDENCE_EXISTS + SPATIAL_ALIGNMENT = true. N041: EVIDENCE_EXISTS = true, IDENTITY_MATCH = false → PARTIAL_MATCH or UNRESOLVED.
- **Real-surface QA:** Review verification report for N041: should show evidence exists, spatial alignment confirmed, but identity unresolved (candidate status). Review N039: should show stronger match on multiple criteria.
- **Cleanup:** None.
- **Commit:** YES — `feat(eTwin): multi-criteria verification engine`

### Task 8: Knowledge Persistence Proof
Demonstrate that analysis survives interruptions without data loss.

- **Files:** `model/etwin/persistence_proof.py`
- **What:** Two-phase proof:
  1. Phase 1: Analyze 5 tiles from terrace region → save state → "terminate" (simulate process end)
  2. Phase 2: Reload state → verify all 5 observations intact → analyze 5 more tiles → save → reload → verify all 10 observations intact
  
  Verify that claims, conflicts, and decisions from Phase 1 are unchanged after Phase 2.
- **RED:** After Phase 2, any observation from Phase 1 must be byte-identical in JSON.
- **GREEN:** Script runs both phases and prints verification results.
- **Real-surface QA:** Inspect JSON state file before and after Phase 2. Diff should show only additions, no modifications or deletions.
- **Cleanup:** Remove test state file after verification.
- **Commit:** YES — `feat(eTwin): knowledge persistence proof`

### Task 9: ETW-1 Gate Report
Document the complete chain demonstration.

- **Files:** `docs/FOGLIO_LAVORO/GATE_REPORT_ETW1.md`
- **What:** Write gate report documenting:
  - Source rendering fidelity results (Task 0)
  - Document chain: PDF → map → regions → tiles → crops → entities → verification
  - Terrace test case results
  - All evidence crops with paths
  - Entity/candidate binding chains (N041 explicitly as candidate)
  - Verification matrix (multi-criteria, not just "exists")
  - Knowledge persistence proof results
  - Residuals discovered
  - Verdict against PASS criteria
- **RED:** Report must reference real files that exist.
- **GREEN:** Report is complete and self-contained.
- **Real-surface QA:** User can follow report to reproduce entire chain.
- **Cleanup:** None.
- **Commit:** YES — `docs(eTwin): ETW-1 gate report`

## Parallel Execution Waves
- **Wave 0:** Task 0 (rendering fidelity) — CRITICAL GATE, must pass before anything else
- **Wave 1:** Task 1 (data model) — foundation, depends on Task 0
- **Wave 2:** Tasks 2, 3, 4 (registry, map, state) — independent of each other, all depend on Task 1
- **Wave 3:** Task 5 (terrace probe) — depends on Tasks 2, 3
- **Wave 4:** Tasks 6, 7 (binding, verification) — depend on Task 5
- **Wave 5:** Tasks 8, 9 (persistence, gate report) — Task 8 depends on Task 4, Task 9 depends on all

## Dependency Matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|---------------------|
| 0 | none | 1 | — |
| 1 | 0 | 2,3,4 | — |
| 2 | 1 | 5 | 3,4 |
| 3 | 1 | 5 | 2,4 |
| 4 | 1 | 5,8 | 2,3 |
| 5 | 2,3 | 6 | — |
| 6 | 5 | 7,9 | — |
| 7 | 6 | 9 | — |
| 8 | 4 | 9 | — |
| 9 | all | — | — |

## ETW-1 PASS Criteria

PASS **only** when the system demonstrates:

1. **1 OriginalDocument** loaded with verified SHA256 and page dimensions
2. **DocumentMap persistente** with semantic regions (not just spatial grid)
3. **At least 1 SemanticRegion** (PLAN, TITLE_BLOCK, or DETAIL)
4. **Adaptive tessellazione ad alta risoluzione** with deterministic overlap
5. **Lettura interrompibile/riprendibile** — analyze → save → interrupt → resume without loss
6. **Observation** recorded with coordinates and method
7. **Claim** generated from observation
8. **EvidenceCrop** saved with bboxNative + bboxNormalized + crop path
9. **PropertyResolution** linking entity/candidate → property → claim → evidence → crop → PDF
10. **eTwin entity/candidate** — confirmed entities for N002/N005/N039, DocumentEntityCandidate for N041
11. **VerificationResult** with multi-criteria analysis (not just existence)
12. **Exact return to original region** — select entity → trace back to exact PDF region
13. **Knowledge persistence** — no previous knowledge lost after interruption
14. **No automatic promotion** — N041 remains candidate, no ND→DOC conversions
15. **Working tree clean**
16. **Gate report complete**

## Baseline
- Commit: `d521f11` (DXF inventories)
- No existing eTwin code — this is greenfield within existing repo structure
- Existing infrastructure: `data/canonical/`, `archive/documentazione_originaria/`, `.venv/`

Next: `start-work etw1-document-engine`
