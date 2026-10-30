# CEW-B01 Hosted-Marker Graphical Repair Design

Status: `EXPERIMENT_ONLY / HUMAN_REVIEW_REWORK / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Intent

Repair three defects found during Human Graphical Review of PR #168 without changing semantic or structural authority:

- **D1 — incomplete transverse signature:** the current raster detector accepts a pair of transverse strokes on only one side of the carrier. The reviewed drawing convention instead shows the complete local configuration as **two transverse strokes on each side of the carrier section** (four strokes total around the marker).
- **D2 — carrier role confusion:** at least one reviewed occurrence is a pillar/support-like graphical element but enters the same hosted-marker candidate family as beam-like through carriers. The repair must introduce a neutral carrier-topology descriptor and must not call a carrier a beam automatically.
- **D3 — marker overlay mismatch:** at least one red review box does not coincide sufficiently with the actual black rectangular marker in the source. The repair must measure raster support for the frozen G1 marker geometry and flag misaligned geometry instead of silently snapping or rewriting provenance.

The human technical hypothesis remains separate from the detector: a complete bilateral double-pair configuration may correspond to a beam carrying the slab, while an isolated marker may correspond to a beam not carrying it. This mapping is not executable authority in this repair.

## Selected approach

Add a **neutral graphical refinement layer over the exact PR #168 occurrence search**, rather than rewriting G1 or replacing the existing hybrid evidence.

Pipeline:

`PR168 bound occurrence -> bilateral transverse evidence -> carrier-topology evidence -> marker-alignment evidence -> graphical repair role -> Human Review`

### Alternatives considered

1. **Rewrite the existing PAIR detector in place.** Rejected because it would erase the distinction between previously qualified evidence and the new review finding.
2. **Add a neutral refinement layer.** Selected because it preserves G1, raster, candidate IDs and provenance while allowing the Human Review to invalidate or refine the old family.
3. **Promote directly to beam/pillar/slab semantics.** Rejected because the current gate is graphical, not structural.

## D1 — bilateral transverse section signature

The existing local raster routine returns one selected side. The repair must inspect both cross-axis sides independently.

Neutral states:

- `BILATERAL_DOUBLE_PAIR` — two qualifying strokes before the carrier band and two qualifying strokes after it;
- `UNILATERAL_PAIR_OR_PARTIAL` — evidence exists on only one side, or one side lacks a complete pair;
- `NO_TRANSVERSE_SECTION` — no material local transverse pair on either side.

The old `RECT_PLUS_TRANSVERSE_PAIR_CANDIDATE` remains provenance only. It is not sufficient by itself for the repaired full-section state.

## D2 — carrier topology, not beam semantics

Every candidate receives neutral longitudinal-topology evidence measured relative to the marker:

- available carrier run before marker;
- available carrier run after marker;
- normalized run ratios;
- whether the marker sits on a through carrier, near an end, or in an ambiguous/junction-dominated local configuration.

Neutral topology values:

- `THROUGH_LINEAR_CARRIER`;
- `END_OR_TERMINATED_CARRIER`;
- `AMBIGUOUS_CARRIER_TOPOLOGY`.

No value may be named `BEAM`, `PILLAR`, `COLUMN`, or equivalent in executable output. Human Review may later map a specific graphical topology to a structural class.

The repair must conservatively keep ambiguous/non-through cases out of the prototype-family review set while retaining all provenance.

## D3 — exact marker alignment evidence

The frozen G1 `RECTILINEAR_CLOSED_SHAPE` remains the identity/provenance anchor. The repair must not move it automatically.

For each of its four sides, measure raster edge support in a narrow tolerance band around the claimed rectangle. Emit:

- per-side support fractions;
- minimum side support;
- mean side support;
- `alignment_state` = `ALIGNED`, `WEAK_EDGE_SUPPORT`, or `GEOMETRY_MISMATCH`.

If the claimed rectangle is visibly offset from the black source geometry, the candidate must be flagged for review and excluded from prototype induction. A later dedicated repair may create a new refined observation, but this slice cannot mutate the original G1 primitive.

## Repair roles

Each PR #168 review-eligible occurrence is preserved and receives one neutral `graphical_repair_role`:

- `REVIEW_ELIGIBLE_ALONE` — no transverse section, through carrier, aligned marker;
- `REVIEW_ELIGIBLE_BILATERAL_DOUBLE_PAIR` — bilateral double pair, through carrier, aligned marker;
- `PARTIAL_TRANSVERSE_REVIEW` — unilateral/partial transverse evidence;
- `CARRIER_TOPOLOGY_REVIEW` — carrier is not confidently through-linear;
- `MARKER_ALIGNMENT_REVIEW` — marker geometry lacks sufficient raster edge support.

Precedence is conservative: marker-alignment problem first, then carrier-topology problem, then partial transverse evidence, then the two review-eligible states.

## Human Review artifact

Produce a bounded corrective micro-atlas, not another full catalogue:

- up to 8 `REVIEW_ELIGIBLE_ALONE`;
- up to 8 `REVIEW_ELIGIBLE_BILATERAL_DOUBLE_PAIR`;
- all selected `CARRIER_TOPOLOGY_REVIEW` examples up to 6;
- all selected `MARKER_ALIGNMENT_REVIEW` examples up to 4;
- selected `PARTIAL_TRANSVERSE_REVIEW` examples up to 6.

Rendering must show:

- source raster;
- frozen marker box;
- carrier edges;
- both transverse-side pair overlays separately;
- alignment warning where applicable;
- topology label;
- primitive ID and evidence provenance.

## Acceptance criteria

1. A synthetic bilateral case requires two strokes on both sides; one-side pair alone cannot qualify as full bilateral evidence.
2. Reversing raster/primitive iteration preserves byte-identical evidence.
3. Carrier topology distinguishes through-linear from near-end/terminated synthetic cases without structural labels.
4. Marker alignment rejects an intentionally shifted rectangle and accepts an aligned rectangle.
5. Exact TAV.5 replay preserves every PR #168 occurrence and original IDs/provenance.
6. The repair produces a corrective micro-atlas and governed JSON receipt.
7. Human-review states remain `UNREVIEWED` in code.
8. Semantic classification, structural identity, canonical writes, G2C, G3 and merge authority remain false.

## Non-goals

- no automatic beam/pillar/column classification;
- no automatic slab-support semantic classification;
- no G1 rewrite;
- no automatic marker snapping;
- no full-corpus expansion beyond TAV.5;
- no G2C/G3 promotion;
- no merge authorization.
