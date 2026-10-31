# CEW Mobile Review Bar v1 — design

Date: 2026-10-30
Status: APPROVED FOR IMPLEMENTATION
Base checkpoint: `work/cew-f7-native-review-ui@557e581efc899a0aaf4e063b2de97026089b092f`

## Problem

The current atlas/code-driven Human Review is too costly on a smartphone. The reviewer must be able to inspect the evidence at high scale, pan/zoom it, decide with one tap, and continue without transcribing candidate identifiers.

## Product decision

The canonical mobile review surface uses an evidence-first layout with a fixed bottom action bar. No decision control is overlaid on the drawing.

Bottom actions:

1. `PILASTRO` — graphical footprint confirmed.
2. `NON_PILASTRO` — proposed target rejected.
3. `INQUADRATO_MALE` — a column is present, but the proposed frame/target is not adequate.
4. `ALTRO_PILASTRO` — enter point-pick mode; the next tap on the evidence records an additional visible column occurrence.

Supporting controls:

- progress counter (`current / total`);
- `ANNULLA` for the last decision;
- automatic advance after terminal candidate decisions;
- optional rejection reason (`TRAVE`, `QUOTA`, `LINEA_DI_DISEGNO`, `RITAGLIO_INCOMPLETO`, `ALTRO`);
- evidence zoom/pan remains available;
- safe-area aware bottom bar and sufficient viewer padding so controls never hide evidence.

## Interaction contract

### Candidate decisions

`PILASTRO`, `NON_PILASTRO`, and `INQUADRATO_MALE` are terminal for the current candidate and auto-advance to the next candidate.

`ALTRO_PILASTRO` is not terminal. It arms point-pick mode. The next valid tap inside the evidence viewport creates an `ADDITIONAL_OCCURRENCE` event with normalized source-local coordinates `{x, y}` in `[0,1]`, then returns to the same candidate.

### Undo

History is append-only. `ANNULLA` never deletes an event; it appends an `UNDO_LAST` event referencing the last effective decision/event. The UI recomputes effective state from the event stream.

### Persistence/export

The first slice stores the review event stream locally in the review pack and supports JSON export. Integration with the native CEW receipt service is a successor step. Export is audit material only.

## Generic manifest

The reviewer is object-agnostic and must not be tied to COL-02. A review manifest supplies:

- `review_id`;
- source/evidence authority metadata;
- ordered candidates;
- for each candidate: stable `candidate_id`, evidence image URI, optional overlay image URI, optional source transform/locator, optional prompt.

COL-02 will be one producer of this manifest; other CEW object-recognition flows may reuse the same reviewer.

## Authority boundary

This surface confirms/rejects graphical candidates only. It does **not** authorize or infer:

- support identity or numeric identifier;
- structural identity;
- family or section assignment;
- fixed lines or analytical axes;
- canonical geometry or canonical writes;
- G2C/G3 promotion;
- merge.

All authority flags remain false in exported review bundles.

## Mobile constraints

- target viewport: smartphone portrait first;
- bottom controls fixed and thumb-reachable;
- minimum action target height: 48 CSS px;
- `padding-bottom` accounts for action bar plus `env(safe-area-inset-bottom)`;
- no action buttons over the evidence image;
- pinch-zoom / browser zoom and pan must remain possible;
- accidental double submission prevented per candidate action.

## Acceptance criteria

1. A reviewer can classify a candidate with one tap and is automatically advanced.
2. A reviewer can undo without destroying audit history.
3. A reviewer can mark a misframed positive without calling it negative.
4. A reviewer can tap an additional visible column directly on the evidence.
5. The point is stored normalized to the displayed evidence bounds.
6. Four primary actions remain visible on a 360 px-wide viewport without obscuring the image.
7. Export contains append-only events and closed authority flags.
8. The reviewer is generic and not coupled to COL-02 identifiers.
9. Existing F7 canonical-write prohibition is preserved.
