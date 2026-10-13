# CEW-GATE-AUTHORITY-01 Implementation Program

This file fixes the execution order and cross-plan interfaces for the approved CEW-GATE-AUTHORITY-01 design.

## Plans

1. `docs/superpowers/plans/2026-10-13-cew-gate-authority-01-bootstrap.md`
2. `docs/superpowers/plans/2026-10-13-cew-contract-01-trusted-migration.md`

Plan 2 must not begin until Plan 1 reaches `CEW-GATE-AUTHORITY-01 G0/A0 = OPERATIONAL`.

## Cross-plan contract C1 — Candidate payload profile

A0 created by Bootstrap Task 2 must freeze the **exact 21-path Candidate Payload Profile** defined in the migration plan under `qualification/cew-contract-01/n12/`.

No prefix/glob authority is sufficient for A0. Each of the 21 paths is explicit. A qualification Candidate containing a declared qualification path outside this set fails closed. Candidate workflows/scripts/tests are never part of this profile.

## Cross-plan contract C2 — G0 immutable identity

`G0` is the exact commit that contains the reviewed Gate Core source, A0, schemas, manifest, tests relevant to source qualification, and trusted runtime dependency declarations.

Later commits that add:

- assurance reports,
- human promotion record,
- deployment workflow,
- repository-governance documentation,
- attestation/promotion plumbing,

do **not** silently redefine G0.

The production trusted workflow must pin and materialize the exact promoted G0 commit SHA. Its Receipt separately records B, so a later base/control-plane commit cannot be confused with G0.

Any modification to Gate Core source or A0 after the G0 source commit creates a new G0 candidate identity and requires the bootstrap assurance + independent review + human promotion gate again.

## Cross-plan contract C3 — Promotion sequence

The required sequence is:

`design approved → plans approved → G0/A0 source candidate → bootstrap assurance → independent review → human promotion of exact G0/A0 → deployment/control-plane commit pinning G0/A0 → live acceptance → G0/A0 OPERATIONAL → clean qualification Candidate H → Receipt/attestation → human promotion → optional #147 supersession`.

No green CI result replaces either human promotion decision.

## Cross-plan contract C4 — #147

PR #147 is read-only audit source during both plans. It receives no new parser-hardening commits. It remains open until the replacement qualification is successfully integrated and the user explicitly authorizes closure as superseded.

## Cross-plan contract C5 — Failure ownership

During migration:

- a Candidate data defect is fixed only in the qualification Candidate and only from supported #147/O evidence;
- a Gate Core defect is handled through G → G+1 outside the Candidate branch;
- a platform/policy failure is `BLOCKED_CONTROL_PLANE` and does not trigger candidate changes;
- a replay/authority mismatch fails closed and does not authorize new engineering assumptions.
