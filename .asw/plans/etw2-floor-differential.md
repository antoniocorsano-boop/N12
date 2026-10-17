# ETW-2 — Floor Differential Reconstruction

## Objective
Apply the ETW-1 evidence engine to TAV-02S..TAV-05S and reconstruct the per-level geometric differences of G1-G4 without manual transcription and without assuming a typical floor.

## Baseline
- ETW-1 gate: PASS
- Branch: `feat/structural-professional-workspace-r1`
- Source mapping:
  - G1 → TAV-02S → `tavola2-2.pdf`
  - G2 → TAV-03S → `tavola3-2.pdf`
  - G3 → TAV-04S → `tavola4-2.pdf`
  - G4 → TAV-05S → `tavola 5.pdf`
- M0-S1B previous state: BLOCKED because OCR could not read structural content.
- ETW-1 removes that tooling block through deterministic 300/600 DPI rendering, adaptive tiles, persistent reading and evidence crops.

## Invariants
1. Do not assume G1-G4 are identical.
2. Do not create TYPE_A/TYPE_B before evidence comparison.
3. Do not promote INF/ND to DOC automatically.
4. Preserve existing M0-G, M0-G-R1, Knowledge Graph R1 and canonical IDs.
5. Every detected difference must trace to source PDF region/crop.
6. Missing or ambiguous readings become residuals, not invented geometry.

## Output model
For each physical element/property comparison produce:

`level → document → region/tile → observation → claim → entity/candidate → comparison result`

Comparison statuses:
- `MATCH`
- `SECTION_CHANGE`
- `GEOMETRY_CHANGE`
- `ELEMENT_ADDED`
- `ELEMENT_REMOVED`
- `POSITION_SHIFT`
- `IDENTITY_UNRESOLVED`
- `UNREADABLE`

## Task 1 — Four DocumentMaps
Generate/reuse DocumentMap for TAV-02S, TAV-03S, TAV-04S, TAV-05S using identical parameters.

Acceptance:
- same DPI and overlap policy;
- deterministic normalized coordinates;
- all maps persisted;
- source SHA256 verified.

## Task 2 — Structural registration
Use G4/TAV-05S as reference surface only for coordinate registration, not as the assumed typical floor.

Build a normalized comparison frame for the four sheets using:
- page native coordinates;
- stable plan-region bounds;
- known canonical anchors where already verified;
- DXF text inventories as supplementary evidence.

Output: `floor_registration.json`.

## Task 3 — Evidence sweep
Read plan tiles progressively for each level. Capture evidence for:
- structural nodes/pillars;
- beam axes and labels;
- section annotations;
- slab boundaries/openings;
- stairs/terrace/roof-transition features;
- dimensions needed to disambiguate geometry.

Persist observations append-only.

## Task 4 — Element correspondence
Resolve cross-level correspondence using existing persistent identity first, then position/topology/evidence.

Never assign a new persistent identity from visual proximity alone.

Output: `floor_element_correspondence.json`.

## Task 5 — Floor Difference Matrix
Create one record per compared entity/property:

`entity_id, property, G1, G2, G3, G4, comparison_status, evidence_refs, confidence, residual_id`

Do not collapse differences into prose.

## Task 6 — Floor signatures
Derive a signature for each level from verified differences only.

A signature may include:
- node set/topology;
- beam membership;
- verified sections;
- slab/opening geometry;
- special regions.

Only after signatures exist may levels be proposed as the same `TypicalFloorGroup`.

## Task 7 — Residual handling
For each unresolved item record:
- scope;
- affected entity/property;
- source region;
- severity;
- resolution method;
- required evidence;
- blockingFor[].

Residuals block only dependent properties.

## Task 8 — ETW-2 Gate
PASS only when:
- TAV-02S..05S have reproducible DocumentMaps;
- cross-level registration is explicit;
- Floor Difference Matrix exists;
- every nontrivial difference has evidence refs;
- no automatic typical-floor assumption remains;
- at least one real inter-floor difference is verified end-to-end;
- unresolved differences are explicit residuals;
- existing canonical data is not silently rewritten.

## First execution target
Start with the same structural region on G4 and G3, then G2 and G1, because ETW-1 already provides a verified G4 evidence workflow. The first goal is not full-sheet completion but one verified cross-level difference through the complete chain:

`TAV-05S/G4 ↔ TAV-04S/G3 → evidence crops → same entity/property → difference status`.
