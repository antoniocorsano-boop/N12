# CEW-CAL-01 — Internal Dimension-Chain Discovery Design

## Intent

The qualified external-perimeter stage returned `PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED` with zero numeric observations. Exact-source overlay inspection shows that the four external rectangular bands lie predominantly in blank paper, while dimension text and graphic relations are concentrated inside the structural-plan envelope. The approved hierarchical search therefore advances to the internal stage.

This stage searches the structural-plan envelope only. It is not a return to unconstrained page-wide OCR: the title block and blank exterior remain excluded, and numeric text becomes a review candidate only after the existing semantic dimension grammar confirms a linear dimension rather than a section measure.

## Binding rules

- Exact TAV.5 remains the sole source: SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- The internal stage is enabled only after a qualified perimeter result with `candidate_count == 0` and `status == PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED`.
- Historical M0-G, historical affine coefficients, historical `S-*` annotations and TAV02 evidence remain forbidden inputs.
- Search occurs only inside the source-frame structural envelope already derived by the perimeter stage; the title block is excluded.
- OCR is a localizer and transcription proposal only. It never creates a metric relation by itself.
- No line suppression is used in the discovery OCR because dimension-line and terminal-tick context must remain visible.
- Multiple OCR families and rotations are preserved by location; conflicting readings are not repaired or silently reconciled.
- A location becomes `INTERNAL_LINEAR_DIMENSION_CANDIDATE` only when the existing semantic role gate returns `LINEAR_DIMENSION` from OCR consensus plus dimension-tick grammar and without section-role conflict.
- `SECTION_MEASURE` and `UNRESOLVED` remain rejected from the planimetric candidate set.
- Every candidate requires human `PRIMARY_VISUAL_VALIDATED` review before it may enter the governed metric-relation inventory.
- `primary_anchor_count` remains `0` throughout this stage.
- No canonical geometry, structural identity, M0-G binding or canonical write is authorized.

## Search frame and OCR

The search region is `structural_plan_envelope.envelope_bbox_source_px` from the qualified perimeter artifact, mapped directly in the exact-source raster. OCR runs on this single bounded region at the native 300 dpi source resolution with:

- preprocessing: `RAW_GRAYSCALE`, `CLAHE`, `BINARY_OTSU`;
- rotations: `0`, `90`, `180`, `270` degrees;
- Tesseract PSM 11;
- numeric whitelist `0123456789.,`;
- no geometric line removal;
- scale `1.0` to avoid unnecessary enlargement of the already 300 dpi raster.

Tokens are back-projected to exact-source coordinates and clustered by physical location. All alternate readings and OCR-family evidence remain inspectable.

## Semantic gate

For each location cluster:

1. establish bounded OCR consensus without digit repair;
2. collect local primary line segments and the bounded short-tick channel from the exact raster;
3. detect nearby closed-frame context;
4. apply `classify_numeric_graphic_role` with the observed OCR orientation;
5. retain only role `LINEAR_DIMENSION` as an internal candidate.

The resulting dimension relation records the two tick-defined source endpoints. These endpoints are document relations, not yet affine calibration anchors.

## Outputs

The stage writes:

- `internal/internal-dimension-discovery.json`;
- `internal/internal-dimension-search-overlay.png`.

The JSON records source digest, triggering perimeter result, exact search ROI, OCR strategy, location clusters, consensus/role results, candidates, rejected locations, counts, and closed authority.

Zero candidates is a valid governed result. It must not trigger fabricated anchors or relaxed semantic gates.

## Success criterion

The stage succeeds when it deterministically identifies which numeric locations inside the structural-plan envelope satisfy the already established TAV.5 linear-dimension grammar, preserves conflicting OCR evidence, and emits source-bound candidate relations for one-at-a-time human review without changing engineering authority.
