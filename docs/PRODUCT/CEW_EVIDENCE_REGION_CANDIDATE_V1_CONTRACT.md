# CEW EvidenceRegion Candidate v1 — Product Contract

Status: `B1.6 PREPARATION`  
Program: `CEW-GOAL-01`

## Purpose

Allow an engineer to select a meaningful region on a governed drawing and create a reviewable **EvidenceRegionCandidate** without mutating the current F2 `EvidenceRegion` registry.

## Journey

`READY Page -> drawing viewer selection -> normalized page bbox -> candidate proposal -> append-only product audit -> human/geometric review -> separate governed F2 promotion`

## Candidate is not EvidenceRegion

An `EvidenceRegionCandidate` is a product/workflow proposal only. It does not become `EvidenceRegion` because it was drawn by a user, detected by AI or stored in the audit database.

Promotion requires a separate F2-compatible decision proving:

- immutable SourceVersion identity;
- Page identity;
- coordinate space and transformation;
- real geometric region;
- reproducibility from SourceVersion without conversational/manual hidden coordinates;
- declared evidence purpose;
- human authority where required.

## Required fields

- candidate_id;
- source_version_id;
- page_id;
- geometry_type = `BBOX` for v1;
- coordinate_space = `NORMALIZED_0_1`;
- x, y, width, height;
- author_type (`HUMAN` or `MACHINE_PROPOSAL`);
- purpose;
- created_at;
- state;
- canonical_write_authorized = false.

Optional:

- human_note;
- originating_document_feature_candidate_id;
- originating_task_id;
- target_entity_hint;
- detector/source basis;
- review note.

## States

- `DRAFT`
- `PROPOSED`
- `REVIEW_REQUIRED`
- `REJECTED`
- `READY_FOR_F2_PROMOTION_REVIEW`
- `SUPERSEDED`

No state in this contract is equivalent to `EvidenceRegion.READY`.

## Geometry rules

- Page must exist and be `READY`.
- SourceVersion must exactly match the Page registry.
- bbox must be inside normalized page coordinates.
- zero/negative regions are rejected.
- region area must be non-trivial and not silently expanded/cropped by the server.
- viewer rotation/zoom/pan are display state only; the client must project the selection back into unrotated Page coordinates before submission.
- the server revalidates the normalized bbox.

## Storage

Candidate persistence, when enabled, is append-only product audit state. Proposed table/migration is versioned in the repository but **must not be applied to Production while B1.6 is preparation-only**.

Candidate storage may never update `CEW_EVIDENCE_REGION_REGISTRY_v1.csv` directly.

## Human-centred acceptance

Representative task:

> Open TAV-05A, orient it for reading, select the exploded reinforcement area of interest, explain why you selected it, and confirm that CEW has created a candidate—not approved engineering evidence.

Measure:

- task success / false success;
- time and interactions;
- selection recovery/backtracks;
- ease/confidence;
- whether user understands viewer rotation is not source rotation;
- whether user understands candidate ≠ EvidenceRegion ≠ structural binding;
- whether user can return to full drawing context.

## Forbidden

- direct write to current F2 EvidenceRegion registry;
- nearest-member automatic binding;
- automatic DOC/MIS promotion;
- storing viewer-space coordinates without Page projection;
- hidden coordinate correction;
- candidate-to-Observation automatic promotion;
- candidate-to-structural-property automatic promotion;
- claiming persistence/promotability while the append-only candidate store is not configured and validated.
