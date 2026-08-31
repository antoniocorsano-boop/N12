# CEW OA-5 — Structural Resolver Logic v1

OA-5 is the first tranche allowed to construct a **structural identity candidate**, but it still cannot create an accepted structural identity.

Input is limited to human-reviewed family candidates from OA-4. Rejected, ambiguous or deferred candidates are not admissible.

A family assignment is not structural identity. At least one explicit, revision-matched relationship evidence item is required before a candidate can reach `READY_FOR_EXPLICIT_IDENTITY_REVIEW`.

Supported relationship evidence includes vertical continuity, frame membership, node connectivity, section continuity, explicit drawing callouts and verified cross-drawing registration.

The following are forbidden as identity authority:

- visual or geometric proximity alone;
- similarity score alone;
- family membership alone.

OA-5 outputs `STRUCTURAL_IDENTITY_CANDIDATE` with one of:

- `INSUFFICIENT_RELATIONSHIP_EVIDENCE`;
- `READY_FOR_EXPLICIT_IDENTITY_REVIEW`;
- `IDENTITY_CONFLICT`.

Even a review-ready candidate has `accepted_structural_identity=false`, `canonical_write_authorized=false` and `project_material_ready=false`.

The next boundary is an explicit OA-G5 structural identity review. OA-6 Project Material Gate remains blocked until that identity boundary is satisfied for the target scope.
