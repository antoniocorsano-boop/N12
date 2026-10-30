# CEW-B01 Prototype-Guided Beam Graphical Match Review — Design

## Intent

Use the two human-approved graphical prototypes from `BEAM_GRAPHICAL_TYPE_PROTOTYPES_v1.json` as separate visual references to review all eight frozen TAV.5 DOUBLE candidates.

The output is a governed **graphical similarity proposal**, not an automatic semantic beam classification.

## Goals

- Reuse the already-qualified exact-source artifact from run `41044608383`, artifact `12971414043`.
- Compare every current DOUBLE candidate against both approved prototypes:
  - `CEW-B01-BEAM-GRAPH-T1-v1` — human reference label `trave emergente`;
  - `CEW-B01-BEAM-GRAPH-T2-v1` — human reference label `trave a spessore di solaio`.
- Record one proposed review bucket per candidate:
  - `SIMILAR_TO_T1`;
  - `SIMILAR_TO_T2`;
  - `NEITHER`;
  - `UNCERTAIN`.
- Keep every non-reference candidate `PENDING_HUMAN_REVIEW`.
- Preserve the existing authority boundary: no semantic classification, structural identity, canonical CAD write, G2C, G3 or merge authority.

## Non-goals

- No new detector threshold.
- No retraining or embedding model.
- No promotion of the human labels into executable semantics.
- No change to the frozen source candidate set.
- No re-extraction of TAV.5.

## Matching rule for this micro-pilot

The comparison is relational rather than absolute-orientation based.

- **T1 relation:** the visible double-band direction is orthogonal to the marker major axis.
- **T2 relation:** the visible double-band direction is parallel to the marker major axis.
- A candidate is `UNCERTAIN` when the source-only crop does not make that relation visually reliable.
- A candidate is `NEITHER` when the visible source geometry is reliable but matches neither approved relation.

The source-only 300-dpi crop remains the visual authority. Recorded marker geometry, major-axis orientation and carrier provenance are supporting metadata, not a substitute for source inspection.

## Approaches considered

1. **Relational source-only review — selected.** Compare the orientation relation between marker and double band. This is invariant to page rotation and directly reflects the distinction approved by Human Review.
2. **Raw pixel or embedding similarity — rejected for this stage.** It could be dominated by annotations, crop scale and absolute orientation and would introduce a new model/threshold.
3. **Promote detector output directly to T1/T2 — rejected.** The current detector was not qualified for semantic or prototype-family classification.

## Expected pilot proposal

Using the frozen source-only crops:

- D01 → `REFERENCE_T1`;
- D02 → `SIMILAR_TO_T1`;
- D03 → `SIMILAR_TO_T2`;
- D04 → `SIMILAR_TO_T2`;
- D05 → `REFERENCE_T2`;
- D06 → `SIMILAR_TO_T2`;
- D07 → `SIMILAR_TO_T2`;
- D08 → `SIMILAR_TO_T2`.

This remains a proposal until Human Review confirms or changes the candidate decisions.

## Authority boundary

All of the following remain false:

- automatic semantic classification;
- structural identity;
- canonical writes;
- G2C promotion;
- G3;
- merge authorization.

The only approved semantic text remains the human reference mapping attached to the two prototype records themselves.
