# CEW Mobile Review Bar v1 — implementation plan

Date: 2026-10-30
Design: `docs/experiments/2026-10-30-cew-mobile-review-bar-design.md`

## Goal

Add a generic smartphone-first CEW graphical candidate reviewer on top of the native F7 review checkpoint, without canonical writes or structural promotion.

## Task 1 — Contract and TDD RED

Create `scripts/validate_cew_mobile_review_bar.py` with deterministic checks that require:

- exact primary actions `PILASTRO`, `NON_PILASTRO`, `INQUADRATO_MALE`, `ALTRO_PILASTRO`;
- terminal auto-advance semantics for the first three;
- non-terminal point-pick semantics for `ALTRO_PILASTRO`;
- normalized point coordinates in `[0,1]`;
- append-only `UNDO_LAST` semantics;
- optional rejection reasons;
- all CEW structural/canonical authority flags false;
- generated mobile HTML contract: fixed bottom bar, safe area, >=48 px touch targets, progress counter, undo control, evidence viewport and no action overlay on evidence.

Add a dedicated workflow. First run must fail causally because the production module does not exist.

## Task 2 — Pure review contract GREEN

Create `scripts/cew_mobile_review.py` implementing:

- manifest validation;
- event construction;
- point normalization;
- effective event replay with undo;
- authority-closed export bundle.

No I/O to canonical data.

## Task 3 — Mobile pack GREEN

Create `scripts/build_cew_mobile_review_pack.py` that converts a generic manifest into a self-contained review pack:

- evidence-first viewport;
- fixed safe-area bottom bar;
- four large actions;
- progress and undo;
- auto-advance;
- optional negative reason sheet/chips;
- additional occurrence point-pick;
- local append-only event stream;
- JSON export.

Use no product-specific COL-02 assumptions.

## Task 4 — Native-service integration

Expose a non-authoritative mobile review route from `cew_f7_native_review_service.py` or a generic static artifact route, while retaining the existing F7 route. Health and canonical-write prohibition must remain unchanged.

## Task 5 — Smartphone fixture qualification

Add a small fixture manifest with neutral candidate IDs and placeholder evidence produced from repository-local test assets. Generate the pack and verify:

- 360 px viewport contract;
- safe-area padding;
- no evidence obscuration;
- all four actions and undo present;
- exported authority closed.

No historical support IDs/families are used as oracle.

## Task 6 — PR qualification

Open a Draft PR against `work/cew-f7-native-review-ui`, run the dedicated workflow and existing F7 qualification where applicable, record exact SHA and artifact. No merge or deployment.

## Successor — COL-02 adapter

Only after the generic mobile reviewer is qualified, add an adapter that feeds COL-02 residual candidates into the generic manifest. Keep candidate graphical decisions distinct from text identity, family, section and structural identity.
