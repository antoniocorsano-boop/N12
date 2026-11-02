# CEW-CAL-01 External Dimension Chain Detector Design

## Intent

Recover long, repetitive external dimension chains from the governed structural-grid rasters before binding individual OCR tokens to geometry. The detector exists to prevent a locally plausible two-reference/Hough relation from being mistaken for the actual external dimension carrier.

## Why this change

Human review of TAV-02S established that the documented values `4.95 m` and `6.25 m` are visible members of an external dimension chain, while their recorded local Hough endpoints lie on nearby structural/local edges. `SG-T02-04` also shows the inverse failure mode: a local `70` dimension was associated with a different long line. The failure is therefore geometric association, not merely OCR accuracy.

## Goals

- detect long external dimension carriers in the four structural-grid perimeter bands;
- detect repeated terminal/intermediate ticks on each carrier;
- convert ordered tick positions into consecutive dimension intervals;
- associate OCR observations to an interval only when the token lies close to that carrier and inside that interval;
- support multiple nested carriers on one side without cross-associating their tokens;
- preserve normalized-page coordinates and source observation IDs;
- emit external-chain evidence separately from the existing local candidate inventory for the first exact-source qualification;
- keep all metric-calibration, canonical-geometry, canonical-write and M0-G authority closed.

## Non-goals

- correcting OCR numeric text from geometric context;
- inferring missing dimensions from arithmetic closure;
- replacing human visual validation;
- modifying the shared TAV.5 `dimension_tick_relation()` grammar in this slice;
- promoting any external-chain observation to a primary calibration anchor.

## Chosen approach

### Chain-first detector in normalized page space

The structural-grid pipeline already normalizes page orientation before building TOP/BOTTOM/LEFT/RIGHT perimeter bands. The new detector works in that normalized frame.

For each band it receives axis-aligned Hough segments. A carrier candidate must:

1. have the expected axis for the band (horizontal for TOP/BOTTOM, vertical for LEFT/RIGHT);
2. be long relative to the structural-plan envelope on that axis;
3. contain at least three distinct intersecting short perpendicular or diagonal tick positions, yielding at least two consecutive intervals.

Carriers are ordered from the plan outward. Distinct parallel carriers remain separate chains, allowing nested chains on the same side.

An OCR observation becomes a chain member only when its center projects inside one carrier interval and its perpendicular distance from that carrier is within a bounded token-distance threshold. If more than one carrier/interval is plausible at effectively equal distance, the observation remains unresolved rather than being arbitrarily assigned.

## Alternatives considered

### Tighten the existing local two-reference grammar

Rejected for this slice. The existing grammar is shared with TAV.5 and has qualified behavior. Tightening it would couple the structural-grid repair to already-qualified primary-source discovery and would still reason token-first rather than chain-first.

### Use OCR sequence alone

Rejected. Repeated numeric values can be read correctly while belonging to local dimensions, section annotations or a different nested chain. Text order without carrier/tick geometry is insufficient provenance.

### Infer chains from human-transcribed values

Rejected. Human transcriptions are review evidence, not machine geometry. They may be used later to validate the detector but not as its input.

## Interfaces

New module: `experiments/cew_cal01/external_dimension_chain.py`.

Primary pure interface:

```python
def detect_external_dimension_chains(
    *,
    side: str,
    line_segments: list[tuple[float, float, float, float]],
    observations: list[dict],
    plan_envelope_bbox: list[float],
) -> dict:
    ...
```

The return value contains deterministic ordered `chains`, each with carrier geometry, ordered ticks, consecutive intervals, associated observation IDs, and closed authority. It also contains unresolved observation IDs and counts.

Integration: `structural_grid_dimension.py` extracts one Hough segment inventory per perimeter band from the normalized raster, invokes the detector, and stores:

- `external_chain_count`;
- `external_chain_member_count`;
- `external_chains`;
- `external_chain_unresolved_observation_ids`.

The existing `candidate_count/candidates` fields remain unchanged in the first qualification so the new detector can be compared against the already-governed baseline without silently rewriting history.

## Failure behavior

- no qualifying long carrier: valid zero-chain result;
- fewer than three ticks: not an external chain;
- local short dimension: not an external chain even if locally geometrically bound;
- nested carriers: separate chains;
- ambiguous token-to-chain assignment: unresolved, no promotion;
- OCR value disagreement: preserved as OCR evidence, never corrected from chain geometry.

## Governance

The first exact-source run is diagnostic/qualification evidence only. `primary_anchor_count` remains `0`; `eligible_for_metric_calibration` remains false; canonical geometry/write, structural identity, M0-G and engineering authority remain closed. Human validation is required before any external-chain relation replaces or supplements a governed metric relation.
