# CEW PWB-005-R2 — Raster Geometry Candidate Plan v1

Status: `AUTHORIZED_R2A_R2B_IMPLEMENTATION`

## Basis

R1.1 + R1A prove that all four governed READY EvidenceRegions are embedded raster imagery:

- `CEW-N12-REG-G01-R06`
- `CEW-N12-REG-G05-R04`
- `CEW-N12-REG-G07-R07`
- `CEW-N12-REG-T6A-G03`

Each region has:

- `PDF drawings = 0`
- `PDF text spans = 0`
- `embedded images = 1`
- `image coverage = 1.0`

Therefore native-PDF Dual Vector Agreement cannot supply document primitives for these claims.

## Goal

Produce **raster geometry candidates**, not technical or structural objects, from immutable-source EvidenceRegions.

R2 is split into three gates.

### R2A — Raster candidate extraction

For each governed raster region:

1. reproduce the region from immutable SourceVersion/Page/EvidenceRegion;
2. render deterministic grayscale crops at `200 dpi` and `300 dpi`;
3. run a pinned build-only raster line detector;
4. retain raw line detections separately for each scale;
5. map coordinates back to `SOURCE_PAGE_PT` and normalized region coordinates;
6. retain provenance and hashes.

### R2B — Multi-scale stability

A line becomes a `StableRasterGeometryCandidate` only when a compatible detection exists independently at both 200 and 300 dpi.

Compatibility is deterministic and uses:

- endpoint distance in normalized region coordinates;
- angle difference;
- relative length difference.

Single-scale lines remain diagnostic only and cannot enter the Technical Scene.

### R2C — Technical Scene adapter

**Not authorized by this tranche.**

R2C may begin only after R2A/R2B real-source candidate counts and preview artifacts are inspected and an explicit quality gate is defined. Until then:

`scene_materialization_authorized=false`

## Build-only technology boundary

The application runtime remains unchanged.

Raster analysis runs in an ephemeral build environment with a pinned headless image-processing dependency. The runtime must not import OpenCV or perform on-request raster geometry extraction.

Initial build pin:

`opencv-python-headless==4.12.0.88`

CI is the compatibility proof. If the pin cannot install on the governed Python version, the gate fails rather than floating to another version.

## Extraction contract

Inputs per region:

- immutable SourceVersion identity and SHA-256;
- Page identity/index;
- EvidenceRegion identity and transform;
- normalized bbox;
- R1.1 classification `RASTER`;
- exact build revision.

Outputs per region:

- 200 dpi crop + SHA-256;
- 300 dpi crop + SHA-256;
- detector version and parameters;
- raw detection counts per scale;
- stable candidate list;
- unmatched counts per scale;
- deterministic SVG preview of stable candidates;
- artifact SHA-256.

Every stable candidate contains:

- stable `candidate_id`;
- `object_family=RasterGeometryCandidate`;
- line endpoints in normalized region coordinates;
- mapped line endpoints in `SOURCE_PAGE_PT`;
- 200/300 dpi supporting detection ids;
- endpoint/angle/length agreement metrics;
- `semantic_classification=UNASSIGNED`;
- `technical_identity_authorized=false`;
- `structural_identity_authorized=false`;
- `scene_materialization_authorized=false`;
- `canonical_write_authorized=false`.

## Determinism / safety

- no OCR in R2A/R2B;
- no beam/column/reinforcement classification;
- no automatic snap to F6 members;
- no source-to-technical RegistrationTransform is created;
- no candidate is promoted merely because it is long or repeated;
- raw and stable candidates remain derived evidence;
- no runtime compute fallback.

## Quality states

Per region:

- `STABLE_CANDIDATES_PRESENT`
- `NO_STABLE_CANDIDATES`
- `EXTRACTION_FAILED`

A pipeline `PASS` means the extraction is reproducible and safe. It does **not** mean the candidate geometry is professionally acceptable.

## Exit criteria R2A/R2B

- 4/4 raster regions processed from immutable sources;
- 8/8 scale crops hash-bound (200 + 300 dpi);
- build dependency pin recorded;
- all candidate coordinates valid and provenance-bound;
- stable candidates supported by both scales only;
- no technical/structural identity;
- no scene materialization;
- no canonical write;
- real-source candidate counts and previews available for the next quality decision.

## Authority

`raster line != technical object != structural identity`

`candidate stability != engineering correctness`

`R2A_R2B_SCENE_MATERIALIZATION_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

`HVA_EXECUTION_AUTHORIZED = false`
