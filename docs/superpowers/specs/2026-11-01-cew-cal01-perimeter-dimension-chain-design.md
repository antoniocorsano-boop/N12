# CEW-CAL-01 — Perimeter Dimension-Chain Discovery Design

## Intent

After the governed C0–C17 visual review, numeric discovery on TAV.5 is known to be dominated by section measures and structural identifiers. CEW-CAL-01 therefore needs a separate search path for planimetric span/dimension chains.

The search is hierarchical: first the bands immediately outside the structural-plan envelope, then internal plan areas only if the external search is insufficient.

## Binding rules

- The exact TAV.5 raster remains the sole input to this discovery stage: SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Historical M0-G, historical affine coefficients, historical `S-*` annotations and TAV02 evidence remain forbidden inputs.
- Search-region geometry is derivative localization only and carries no engineering authority.
- A number is not a dimension relation unless local graphic grammar binds it to a dimension line and two reference/extension endpoints.
- Section measures and structural identifiers are rejected from the planimetric relation set even when OCR is confident.
- A discovered relation is a candidate only. Human `PRIMARY_VISUAL_VALIDATED` review remains mandatory before it can enter the governed metric-relation inventory.
- `primary_anchor_count` remains `0` throughout this discovery stage.
- No canonical geometry, structural identity, M0-G binding or canonical write is authorized.

## Structural-plan envelope

For localization only, the exact raster is normalized to landscape orientation when needed. A reduced raster is thresholded and morphologically joined so the large structural drawing becomes one connected component while the title block remains separate.

The selected envelope must:

- span at least 45% of normalized page width;
- span at least 60% of normalized page height;
- be selected by maximum bounding-box area among components satisfying those constraints;
- fail closed with `CAL01_PLAN_ENVELOPE_NOT_FOUND` when no component qualifies.

The envelope is mapped back to exact-source coordinates and recorded with the normalization transform.

## External perimeter bands

Four deterministic bands are generated around the envelope: `TOP`, `RIGHT`, `BOTTOM`, `LEFT`. Each band includes an outer margin plus a small inner overlap so faint extension lines crossing the structural perimeter are retained.

Bands are clipped to the page and must never include negative or out-of-frame coordinates.

## Dimension-chain grammar

Within each band, OCR is only a localizer. A numeric token becomes `PERIMETER_LINEAR_DIMENSION_CANDIDATE` only when source geometry supports:

1. a principal dimension line near the token;
2. two distinct perpendicular reference/extension lines reaching the principal line;
3. two separated endpoints;
4. no promotion from the token alone.

The existing exact-source two-reference geometry detector is reused for this gate so the new path does not weaken the established contract.

## Output

The stage writes:

- `perimeter-dimension-discovery.json`;
- `perimeter-search-overlay.png` showing the structural envelope, four search bands and any geometrically bound candidates.

The JSON records source digest, normalization, envelope, bands, OCR observations, bound candidates, rejected observations, counts, and closed authority.

If no true perimeter chain is found, that is a valid governed result: `PERIMETER_DIMENSION_CHAINS_NOT_OBSERVED`. The next step is then internal-chain discovery; the system must not manufacture anchors to satisfy the affine-fit minimum.

## Success criterion

The stage is successful when it deterministically answers, from exact TAV.5 alone, which perimeter numeric observations are genuinely bound to dimension-chain geometry and whether perimeter evidence is sufficient to justify human review. It is not successful merely because it returns numbers.
