# CEW-CAL-01 Targeted Inter-Source Human Review — Design

## Intent

Convert the qualified fail-closed state `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES` into a bounded professional review surface that can produce explicit TAV.5 ↔ TAV-02S primary-homology decisions without introducing automatic matching, affine fitting, historical M0-G, historical affine coefficients, historical CEW geometry or structural identity.

The current exact-source checkpoint has 22 governed TAV.5 `StructuralObjectCandidate` occurrences, a 21-node TAV-02S local relative metric lattice, and zero governed correspondences. The next admissible action is `TARGETED_INTERSOURCE_HUMAN_REVIEW`.

## Goals

- Select a bounded first review batch from the 22 TAV.5 candidates.
- Make batch selection deterministic and **source-only**: TAV.5 geometry and TAV.5 evidence provenance may be used; TAV-02S geometry may not influence selection.
- Materialize one exact TAV.5 context crop per selected occurrence.
- Materialize one normalized TAV-02S overview with all 21 lattice nodes labelled.
- Produce a deterministic JSON review manifest and static HTML review board.
- Preserve exact TAV.5 source/raster and TAV-02S source/lattice bindings.
- Require the professional reviewer to choose one explicit lattice node or reject the occurrence; the system supplies no identity suggestion.
- Keep structural identity, canonical geometry, M0-G, canonical write and engineering authority closed.

## Non-goals

- No nearest-neighbour or source/target distance comparison.
- No automatic `HOMOLOGY_PROPOSAL` generation.
- No affine fit or fit/holdout split.
- No use of historical comparator, historical affine, historical M0-G, historical `S-*` geometry or historical support identifiers.
- No automatic creation of human-professional correspondence receipts.
- No merge or deploy.

## Source-only targeted selection

The default first batch size is **8**.

Selection is performed only over TAV.5 candidate centers in the governed TAV.5 raster frame:

1. Normalize each TAV.5 center by governed raster width/height for scale-independent coverage.
2. Define evidence strength as the number of unique `source_evidence_refs` attached to the occurrence.
3. Choose the seed with greatest evidence strength; ties resolve by `occurrence_id` ascending.
4. Repeatedly choose the remaining occurrence whose normalized center has the greatest minimum Euclidean distance from the already selected centers; ties resolve by greater evidence strength, then `occurrence_id` ascending.
5. Stop at the requested batch size.

The review manifest must state explicitly:

- `selection_strategy = SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1`;
- `target_geometry_used_for_selection = false`;
- `target_node_ranking_performed = false`;
- `automatic_homology_proposed = false`.

Changing TAV-02S node coordinates or their order must not change selected TAV.5 occurrence IDs.

For the qualified 22-occurrence exact-source artifact, the expected first batch is:

`COL-OCC-0013, COL-OCC-0016, COL-OCC-0005, COL-OCC-0002, COL-OCC-0022, COL-OCC-0020, COL-OCC-0001, COL-OCC-0021`.

This expected order is evidence for determinism, not a homology ranking.

## Review assets

### TAV.5 source context

For each selected occurrence, create a clamped square crop centred on `source_point_px`, preserving the governed `RASTER_PIXEL` frame. The default half-span is 700 px. Draw only a neutral crosshair/box at the reviewed occurrence. The asset record carries filename, pixel crop bounds and SHA-256 digest.

### TAV-02S target context

Use the exact frozen TAV-02S primary raster and the explicit normalization transform from its structural-grid discovery result. The current qualified transform is `ROTATE_90_COUNTERCLOCKWISE`; the implementation must validate rather than assume it. Draw all 21 lattice nodes with their exact `lattice_node_id` labels. No node is highlighted as preferred.

The overview is presentation-only. The authoritative target binding remains the TAV-02S source SHA plus `tav02_lattice_digest` and each node's exact `source_point_normalized_px` / `local_metric_xy_m`.

## Review manifest

Schema: `CEW_CAL01_INTERSOURCE_TARGETED_HUMAN_REVIEW_v1`.

Required content:

- candidate digest;
- exact TAV.5 source and raster binding;
- exact TAV-02S source and lattice digest;
- source candidate count and target lattice node count;
- selection strategy and batch size;
- selected review items in deterministic order;
- TAV.5 crop asset metadata/digests;
- TAV-02S normalized overview metadata/digest;
- professional decision contract: `IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT`;
- no suggested target IDs, no nearest-target fields, no similarity score;
- `historical_comparator_loaded=false`, `historical_affine_loaded=false`, `historical_m0g_loaded=false`;
- closed authority and canonical review-package digest.

## Static review board

The HTML board is a read-only evidence surface. It must show:

- exact source/digest identifiers;
- the eight selected TAV.5 crops with occurrence IDs and provenance refs;
- one TAV-02S normalized lattice overview and an ordered table of the 21 lattice nodes;
- explicit reviewer instruction: select one exact lattice node ID only when visually/professionally justified, otherwise reject;
- warning that local metric coordinates are not surveyed/project coordinates;
- warning that no match is suggested by the system.

The HTML must not contain `nearest`, `suggested_identity`, `suggested_target`, `similarity_score`, `confidence_score`, historical M0-G coordinates or historical affine coefficients.

## Decision and authority boundary

This slice stops at review preparation. It does not fabricate professional decisions.

A later explicit human confirmation must continue to use the existing `CEW_CAL01_INTERSOURCE_CORRESPONDENCE_DECISION_v1` contract and exact source/raster/lattice/point bindings before `govern_correspondences()` can promote it to a governed pair.

Until at least four governed correspondences exist and the registration-split gate independently passes, `affine_fit_performed=false` and `ready_for_affine_fit=false` remain mandatory.

## Failure behaviour

Fail closed on:

- candidate schema/digest or authority drift;
- TAV.5 raster dimension/frame drift;
- TAV-02S source/lattice binding drift;
- unsupported or missing TAV-02S normalization transform;
- duplicate/missing occurrence or lattice IDs;
- batch size outside `1..source_candidate_count`;
- any attempt to introduce target-derived ranking or automatic homology in the targeted-review package.
