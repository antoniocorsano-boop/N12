# CEW PWB-005 — R2HR System Review Integration v1

## Decision

The R2HR professional human review is a CEW system operation.

The reviewer MUST NOT be required to download a review package, open a local `index.html`, export JSON, or manually re-upload a receipt.

The prior CI artifact remains useful as immutable build evidence and as a deterministic source for runtime review material, but it is not the human interaction surface.

## Required runtime flow

`authenticated CEW runtime -> R2HR review surface -> source raster + proposal overlay -> human decision + rationale -> reviewer attestation -> server-side validation -> append-only runtime audit receipt`

The system must present the exact revision-bound review material generated from R2/R2Q/R2M/R2T/R2S/R2SN/R2BR/R2RV. The runtime rejects the review surface if its `candidate_head_sha` does not match the deployed runtime revision.

## Authority boundary

An in-system R2HR receipt has:

- `receipt_authority = HUMAN_REVIEW_EVIDENCE_ONLY`;
- `human_review_is_bridge_acceptance = false`;
- `supported_continuity_hypothesis_is_geometry = false`;
- `r2c_scene_adapter_authorized = false`;
- `technical_identity_authorized = false`;
- `structural_identity_authorized = false`;
- `canonical_write_authorized = false`;
- `engineering_authority_effect = NONE`.

The submission endpoint persists an append-only audit record only. It MUST NOT invoke the F7 promotion engine for R2HR receipts and MUST NOT create a canonical patch candidate.

## Human requirements

For every gap in a reviewed EvidenceRegion the reviewer must provide exactly one decision:

- `SUPPORTED_CONTINUITY_HYPOTHESIS`;
- `REJECTED_CONTINUITY_HYPOTHESIS`;
- `UNRESOLVED_FROM_CURRENT_VIEW`.

Each decision requires a non-empty rationale. The region submission additionally requires a reviewer label and explicit attestation.

## Fail-closed requirements

Submission is rejected when:

- runtime revision and review candidate SHA differ;
- provenance or metric snapshots differ from the generated template;
- the set of gap IDs changes;
- any decision or rationale is missing;
- reviewer attestation is missing;
- any authority field is promoted;
- the persistent audit backend is unavailable in managed runtime.

## Build/deploy requirement

The managed runtime build reproduces the complete R2 diagnostic/review chain and generates R2HR assets for `RENDER_GIT_COMMIT`. Therefore the review shown by the system is tied to the deployed revision, not to a downloaded CI artifact from another revision.

## Superseded interaction

`download artifact -> local index.html -> export JSON -> manual ingestion`

is superseded as the product interaction path.

The CI artifact may remain as non-interactive evidence until its workflow is separately simplified.

`system review evidence != bridge acceptance != technical identity != structural identity != canonical authority`
