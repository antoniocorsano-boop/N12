# CEW PWB-005 — R2HR Human Gap Review Receipt Plan v1

## Purpose

R2HR makes the R2RV inspection package operationally reviewable by a professional without changing the authority of any raster-derived hypothesis.

A reviewer may classify each `GapContinuityHypothesis` as:

- `SUPPORTED_CONTINUITY_HYPOTHESIS`;
- `REJECTED_CONTINUITY_HYPOTHESIS`;
- `UNRESOLVED_FROM_CURRENT_VIEW`.

Every classification requires a human rationale. A supported hypothesis remains only **human review evidence**; it is not accepted document geometry, technical geometry, structural geometry or canonical truth.

## Revision binding

Each receipt MUST carry both identities used by pull-request CI:

- `candidate_head_sha`: the immutable PR head under review;
- `build_revision`: the exact CI checkout revision that produced the review artifact.

For pull-request Actions, these may differ because the job can execute on a synthetic merge commit. R2HR MUST never collapse them into one identity.

The receipt is additionally bound to:

- EvidenceRegion;
- source code;
- immutable SourceVersion;
- source SHA-256;
- Page;
- page transform;
- exact gap hypothesis IDs;
- immutable metric snapshots copied from R2BR/R2SN.

## Human interaction

R2HR generates one standalone review form for each governed EvidenceRegion. It contains:

1. the source raster crop;
2. the R2RV proposal overlays;
3. the measured review metrics;
4. one decision selector and rationale field per gap;
5. reviewer label;
6. explicit reviewer attestation;
7. a local `Export review JSON` action.

The browser performs validation locally. Export is disabled until every gap in the selected EvidenceRegion has:

- one allowed decision;
- a non-empty rationale;
- reviewer attestation.

No receipt is submitted to CEW by the browser. The generated JSON is an external human-review receipt requiring a later governed ingestion/validation step.

## Receipt authority

Every generated receipt MUST encode:

- `receipt_authority = HUMAN_REVIEW_EVIDENCE_ONLY`;
- `supported_continuity_hypothesis_is_geometry = false`;
- `human_review_is_bridge_acceptance = false`;
- `bridge_candidate_authorized = false`;
- `geometry_materialization_authorized = false`;
- `r2c_scene_adapter_authorized = false`;
- `technical_identity_authorized = false`;
- `structural_identity_authorized = false`;
- `canonical_write_authorized = false`;
- `engineering_authority_effect = NONE`.

## Fail-closed rules

R2HR MUST fail closed when:

- R2RV or R2BR is missing;
- build revisions differ;
- candidate head SHA is missing or malformed in CI;
- a gap is added, removed or reordered without a matching receipt template update;
- a metric snapshot differs from R2BR;
- provenance identifiers drift;
- any upstream bridge/R2C/canonical authorization becomes true.

## Next admissible transition

A human-exported R2HR receipt may later be validated and attached as professional review evidence. Such validation is a separate governed transition.

Even a fully supported receipt MUST NOT automatically produce a bridge candidate or R2C geometry.

`human review evidence != bridge acceptance != technical identity != structural identity != canonical authority`
