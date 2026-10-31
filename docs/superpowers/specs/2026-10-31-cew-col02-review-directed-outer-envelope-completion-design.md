# CEW COL-02 Review-Directed Outer-Envelope Completion — Design

## Intent

Close only the remaining graphical defect on `COL02-WSR-003` / `COL02-FP-0241` after the governed whole-symbol review identified `TOP_TRUNCATED_INTERNAL_LINE_SELECTED`.

The new stage is a bounded successor to the generic axis-aware repair. It must not reopen the 611 frozen proposals and must not change the generic detector in order to solve a single reviewed exception.

## Frozen evidence and authority

- PR: `#175` on `spike/cew-col02-residual-occurrence-reconciliation`.
- Frozen producer proposal count: `611`.
- Governed graphical review: `governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v1.json`.
- Authorized residual finding: `COL02-WSR-003` / `COL02-FP-0241` / `TOP_TRUNCATED_INTERNAL_LINE_SELECTED`.
- `COL02-WSR-001`, `002`, `004`, `005` are outside this completion stage.
- Support identity, text identity, family, section, fixed line, structural identity, canonical geometry/write, G2C, G3 and merge remain unauthorized.

## Required behavior

A review-directed completion may run only when the review receipt explicitly records `REWORK` with the supported finding `TOP_TRUNCATED_INTERNAL_LINE_SELECTED` for the source candidate.

For that finding the stage:

1. consumes the exact-source grayscale image and the already reconstructed graphical result;
2. requires the existing left, right and bottom boundary evidence to remain strong;
3. freezes left, right and bottom coordinates;
4. searches only upward, within a bounded distance derived from the current box height, for a coherent horizontal outer edge;
5. requires the candidate top edge to close against both frozen vertical sides;
6. rejects ambiguous competing outer edges instead of ranking through the ambiguity;
7. returns a derived graphical result with provenance identifying review-directed completion;
8. returns `None` when it cannot prove one bounded outer closure.

The stage must never use OCR content, expected dimensions, support numbers, family/section knowledge or structural identity.

## Failure behavior

If the review-directed stage is authorized but unresolved, the known-invalid base repair must not remain `READY_FOR_HUMAN_GRAPHICAL_REVIEW`; that repair becomes `UNRESOLVED_GEOMETRY_REPAIR`.

Unsupported review findings must never trigger the completion stage.

## Non-regression contract

Exact-source requalification must prove:

- `COL02-WSR-001` remains the run-80 corrected geometry;
- `COL02-WSR-002`, `004` and `005` remain byte-for-coordinate equivalent to their already accepted geometry;
- only `COL02-WSR-003` may change;
- proposal count remains `611` and proposal IDs remain immutable;
- all downstream authority remains closed.

## Acceptance

The engineering stage is acceptable only after RED→GREEN unit evidence, complete COL-02 suite PASS, exact-source Tav. 5 replay PASS and fresh graphical inspection of all five overlays. A v2 graphical review receipt may be recorded only if the fresh WSR-003 overlay visibly contains the complete outer symbol and the four preserved cases remain accepted.
