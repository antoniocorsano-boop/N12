# CEW-CAL-01 — Targeted Inter-Source Human Review checkpoint

Date: 2026-11-02

## Purpose

This checkpoint records the first qualified preparation surface for professional TAV.5 ↔ TAV-02S primary-homology review. It prepares evidence only. It does **not** create human decisions, homology proposals, affine registration, structural identity, canonical geometry, M0-G or engineering authority.

## Qualified predecessor

The review preparation is anchored to the already-qualified exact-source Task 5 predecessor rather than rebuilding or mutating that chain:

- predecessor exact SHA: `ebac21fc2cc49bff75e0cc7656ee30d219d44f14`;
- predecessor artifact: `13168600387`;
- predecessor artifact digest: `sha256:116b00d94bf1e2c427eb7b873d531b27adcf97d9a027dc47f41076764f553def`;
- predecessor state: 22 TAV.5 `StructuralObjectCandidate`, 22 `UNMATCHED`, 0 `HOMOLOGY_PROPOSAL`, 0 `AMBIGUOUS`, 0 governed correspondence, `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES`, `ready_for_affine_fit=false`.

The dedicated workflow verifies the predecessor artifact digest before consuming any bytes.

## Controlled implementation ruling

The approved implementation plan originally described adding review materialization to the existing exact-source external-chain workflow. During RED/GREEN execution, the integration was deliberately realized as a **dedicated downstream qualification workflow**:

`.github/workflows/validate-cew-cal01-targeted-intersource-review.yml`

Reason: the existing Task 5 exact-source chain was already independently qualified and had produced an immutable governed artifact. Rewriting that large workflow solely to add presentation/review assets would increase regression surface without increasing evidentiary authority. The dedicated workflow consumes the frozen qualified artifact, verifies its exact SHA-256, materializes only the review package, and reasserts the predecessor fail-closed state.

This is an implementation isolation decision, not an authority relaxation. The predecessor artifact is a historical qualification dependency and expires under the normal GitHub artifact-retention policy; the checkpoint remains the durable record of the exact dependency.

## TDD evidence

### Task 1 — source-only batch selection

- RED exact SHA `6859620e5fca29f123bf2c50517ec95bd296f490`.
- CEW-CAL-01 contract job failed causally with the sole new error `ModuleNotFoundError` for `experiments.cew_cal01.intersource_human_review`; the 204 predecessor tests remained green.
- GREEN implementation SHA `adca417e4bef7123936cbb58ad57179064c7342b`.
- Selection is deterministic and uses only TAV.5 normalized source geometry plus source-evidence strength.
- Changing or reordering TAV-02S node geometry is contract-tested not to change the selected TAV.5 occurrence IDs.

### Task 2 — exact-source visual assets

- RED exact SHA `3ccd7e6731dd04b1f26e6107f408edd4060c2bd3`.
- The sole new failure required the not-yet-implemented review-board/materialization interfaces.
- GREEN implementation SHA `54d0b2d1fdc666a2399c6ba69ec362820f76014e`.
- TAV.5 crops are clamped to the governed 7016×12530 raster frame.
- TAV-02S presentation uses the explicit `ROTATE_90_COUNTERCLOCKWISE` normalization transform and normalized 12914×7016 frame.
- All 21 TAV-02S lattice nodes are drawn uniformly; no node is marked preferred.

### Task 3 — qualification workflow

- Workflow-contract RED exact SHA `d4e23470914817271b75c99fec1445ece7a4dbe6`.
- Contract run executed 213 tests with exactly one failure: the targeted materialization workflow was absent; all other 212 tests passed.
- First integrated qualification candidate: `eb9370ea94fdfc2295c42862b6c49b26a3f9999c`.
- CEW-CAL-01 contract job on that candidate: 213/213 PASS.
- Targeted Inter-Source Human Review run `41503278956`: PASS.
- Generated review artifact `13168823365`, digest `sha256:6fc4f67e20342ef0b87d67de1cc943a46d65269aa9617cedd533bd0fc522b1a1`.
- Review-package digest: `sha256:11e23b41e4fcdf8552bbce06996f7c1a94456267b1128d9be311cbfc957f4a74`.

## Qualified review package

Selection strategy:

`SOURCE_ONLY_FARTHEST_POINT_COVERAGE_V1`

The first bounded professional-review batch is:

1. `COL-OCC-0013`
2. `COL-OCC-0016`
3. `COL-OCC-0005`
4. `COL-OCC-0002`
5. `COL-OCC-0022`
6. `COL-OCC-0020`
7. `COL-OCC-0001`
8. `COL-OCC-0021`

The uploaded artifact was inspected directly and contains exactly:

- 8 TAV.5 source-context PNG crops;
- 1 normalized TAV-02S lattice-overview PNG;
- `targeted-intersource-human-review.json`;
- `targeted-intersource-human-review.html`;
- `qualification-summary.json`.

The overview asset digest is `sha256:02830d1348b663cbcdbba4cd19bf56b92378aa8fccde8aa4628d6fee60859243`.

The manifest explicitly records:

- `target_geometry_used_for_selection=false`;
- `target_node_ranking_performed=false`;
- `automatic_homology_proposed=false`;
- `decision_required=IDENTIFY_PRIMARY_HOMOLOGOUS_LATTICE_NODE_OR_REJECT`;
- `eligible_for_registration_fit=false`;
- `historical_comparator_loaded=false`;
- `historical_affine_loaded=false`;
- `historical_m0g_loaded=false`.

No `nearest`, suggested-target/identity, similarity-score or confidence-score field is permitted in the qualified manifest or review board.

## Authority boundary after review preparation

The predecessor state is deliberately unchanged:

- governed correspondences: `0`;
- registration state: `INSUFFICIENT_INTERSOURCE_CORRESPONDENCES`;
- affine fit performed: `false`;
- ready for affine fit: `false`;
- structural identity authorized: `false`;
- canonical geometry authorized: `false`;
- canonical write authorized: `false`;
- M0-G authorized: `false`;
- engineering authority effect: `NONE`.

The next admissible professional action is to review the eight prepared TAV.5 cases against the labelled TAV-02S lattice and, for each case, either identify one exact homologous lattice node with explicit human confirmation or reject the correspondence.

No merge or deploy is authorized by this checkpoint.

## Final-head qualification rule

This checkpoint commit changes the candidate SHA. Therefore final promotion evidence must be fresh on the post-checkpoint exact SHA and must include PASS for:

- CEW-CAL-01 Primary Metric Calibration;
- CEW-CAL-01 External Dimension Chains;
- CEW Repository Memory Gate;
- CEW-CAL-01 Targeted Inter-Source Human Review.

The final exact SHA and fresh run/artifact identifiers are recorded in PR #187 after those four checks complete successfully.
