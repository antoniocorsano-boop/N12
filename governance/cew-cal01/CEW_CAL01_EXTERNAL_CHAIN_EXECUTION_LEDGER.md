# SDD ledger — plan: docs/superpowers/plans/2026-11-02-cew-cal01-external-dimension-chain.md

- Execution mode: inline on existing branch `feat/cew-cal01-primary-metric-calibration`; local container cannot resolve github.com, so GitHub Actions is the execution/verification environment.
- Pre-flight: Task 1 produces `detect_external_dimension_chains()` consumed by exact-source integration; no interface conflict with existing TAV.5 grammar because `numeric_role.py` and `dimension_tick_relation()` are unchanged.
- Task 1 RED: exact SHA `69d2f416d41851249a40ea725b30aa05a156169c`, CEW-CAL-01 run `41429351117`, `cal01-contracts` failed after 95 tests with the sole new error `ModuleNotFoundError: No module named 'experiments.cew_cal01.external_dimension_chain'`; existing tests were green.
- Task 1 GREEN contract evidence: exact SHA `176fd18fd1ca5fe322e761be4e225b0742a6a48d`, CEW-CAL-01 run `41429506489`, `cal01-contracts` SUCCESS; Repository Memory Gate `41429506739` SUCCESS. Exact-source jobs were still running when Task 2 started.
- Task 2 Ruling: implement the first exact-source integration as a separate post-processor/workflow rather than editing `structural_grid_dimension.py` immediately. Reason: the approved design explicitly requires preservation of legacy `candidate_count/candidates` during first qualification, and a separate post-process stage gives the cleanest A/B evidence while avoiding a large replacement edit of an already-qualified discovery module. Cost if wrong: one extra intermediate artifact/workflow; promotion into the main structural-grid discovery can follow after source evidence is satisfactory.

## Qualified interval OCR checkpoint — 2026-11-02

- Exact qualified candidate: `f415433b070ba8a539460cd66a74841e63dca433`.
- CEW-CAL-01 Primary Metric Calibration run `41448174196`: PASS.
- CEW-CAL-01 External Dimension Chains run `41448174359`: PASS.
- Repository Memory Gate run `41448174420`: PASS.
- Governed artifact `13144370491`, digest `sha256:c723d68b20d202e91986c5d77637fecc338b04d01ce3db8af382377f73018627`.
- TAV-01S: 15 exact intervals; local comparative OCR produced 12 `OCR_NO_PROPOSAL`, 3 `OCR_COMPARATIVE_INSUFFICIENT`, 0 cross-family agreements; comparison digest `sha256:6715d8117af894473c3304039f318bb32cf881a758390ecf4cb759fadd170b49`.
- TAV-02S: 19 exact intervals; local comparative OCR produced 18 `OCR_NO_PROPOSAL`, 1 `OCR_COMPARATIVE_INSUFFICIENT`, 0 cross-family agreements; comparison digest `sha256:e0eba10872cbc71552b44eb97182e664ae19583865ec62ab6b6411226223ee3c`.
- TrOCR remains optional and external-observation-only, bound by exact `review_id + crop_sha256`; no model download or network inference is part of the governed replay.
- OCR output remains diagnostic only: `primary_anchor_count = 0`, `eligible_for_metric_calibration = false`; structural identity, canonical geometry, M0-G and canonical write authority remain closed.

## Qualified external-chain human-review preparation checkpoint — 2026-11-02

Design and plan:

- `docs/superpowers/specs/2026-11-02-cew-cal01-external-chain-human-review-design.md`
- `docs/superpowers/plans/2026-11-02-cew-cal01-external-chain-human-review.md`

Qualification evidence:

- Exact qualified implementation candidate: `bd57285c43bd2557891aeffed15273496900dc9c`.
- CEW-CAL-01 Primary Metric Calibration run `41453478709`: PASS.
- CEW-CAL-01 External Dimension Chains run `41453478759`: PASS.
- Repository Memory Gate run `41453478731`: PASS.
- Governed external-chain artifact `13145119457`, digest `sha256:803fa42b04d91bbdc8b8cc89575ca6fe6caae1160026021908dba307d837cf14`.

Deterministic human-review packets:

- TAV-01S packet digest `sha256:b93ded1fbf84c805b5c59dd6ad4cb7c3bf2004d56f1efe2a3a69cfcfe2616051`: 15 intervals = 1 `REUSED_HUMAN_RECEIPT` + 14 `PENDING_HUMAN_REVIEW`.
- TAV-02S packet digest `sha256:0f81a80faf0915c01f69d2f1c57116fc8cfeb84c76bc296cda43eecf99be34bc`: 19 intervals = 2 `REUSED_HUMAN_RECEIPT` + 17 `PENDING_HUMAN_REVIEW`.
- Total: 34 exact intervals = 3 existing qualified human receipts reused + 31 intervals still requiring professional review.

Existing receipt reconciliation:

- `SG-T01-02` → `TAV-01S:RIGHT:RIGHT:R1:I0`, existing human reading `2.00 m`.
- `SG-T02-02` → `TAV-02S:BOTTOM:BOTTOM:R1:I2`, existing human reading `6.25 m`.
- `SG-T02-01` → `TAV-02S:BOTTOM:BOTTOM:R1:I3`, existing human reading `4.95 m`.
- `SG-T01-01` (`4.05 m`) does not geometrically bind to any qualified external-chain interval crop and is therefore deliberately not reused in this packet.

Governance boundary:

- Reconciliation requires `HUMAN_PROFESSIONAL_USER`, `PRIMARY_VISUAL_VALIDATED`, `LINEAR_DIMENSION`, exact source SHA and unambiguous transformed source-frame containment.
- The AI visual precheck remains `REFERENCE_ONLY` and cannot satisfy the human gate.
- Pending rows contain no generated human value: `validated_value_m = null` and `human_receipt_ref = null`.
- Reused receipts validate only an existing documented metric relation; they do not become absolute calibration anchors.
- For every row and at packet level: `eligible_for_metric_calibration = false`, `primary_anchor_authorized = false`; all structural/canonical/M0-G authority remains closed.
- The governed artifact contains `external-chain-human-review-packet.json` and `external-chain-human-review.html` for each source. The HTML board is review assistance only.
- No new `HUMAN_PROFESSIONAL_USER` receipt was generated automatically. The next gate is actual professional review of the 31 pending intervals.
- No merge or deploy is authorized by this checkpoint.

## Qualified direct human-decision reconciliation checkpoint — 2026-11-02

Professional decisions persisted before qualification:

- `TAV-02S:TOP:TOP:R1:I0` → `4.70 m`.
- `TAV-02S:TOP:TOP:R1:I1` → `5.10 m`.
- `TAV-02S:TOP:TOP:R1:I2` → `4.15 m`.
- `TAV-02S:TOP:TOP:R1:I3` → `4.15 m`.
- `TAV-02S:TOP:TOP:R1:I4` → `5.30 m`.
- `TAV-02S:TOP:TOP:R1:I5` → `4.70 m`.

Qualification evidence:

- Exact qualified implementation candidate: `0239a06c06d51c4dfb73ae786e8fcbce9beb699a`.
- CEW-CAL-01 Primary Metric Calibration run `41460061801`: PASS.
- CEW-CAL-01 External Dimension Chains run `41460061837`: PASS.
- Repository Memory Gate run `41460061779`: PASS.
- Governed external-chain artifact `13150340091`, digest `sha256:7b861b6168ba986f81641ea6f00bc974c0b51dd362c52236101a88e803cce479`.

Governed packet state verified from the uploaded artifact:

- TAV-01S packet digest `sha256:97f78c5c3deee6c10745f889074adf6a138bc557d1f1bc842acb10163684041c`: 15 intervals = 1 `REUSED_HUMAN_RECEIPT` + 0 `DIRECT_HUMAN_DECISION` + 14 `PENDING_HUMAN_REVIEW`; 1 validated human relation.
- TAV-02S packet digest `sha256:6b73018b972a61cd5d6102a706ccdd6da914dde39473dc170335807919625fa8`: 19 intervals = 2 `REUSED_HUMAN_RECEIPT` + 6 `DIRECT_HUMAN_DECISION` + 11 `PENDING_HUMAN_REVIEW`; 8 validated human relations.
- Total: 34 exact intervals = 9 validated human relations + 25 intervals still pending professional review.

Reconciliation behavior qualified on the exact candidate:

- Earlier human receipts remain a separate provenance path and require exact source SHA plus geometric reconciliation after the governed source-frame transform.
- Direct human decisions require exact source SHA + exact `interval_review_id + crop_sha256`; they do not require a source bounding box.
- Unknown interval ids, crop-digest mismatches, source mismatches, invalid human-decision state and conflicting values fail closed.
- Same-value duplicate direct evidence is deterministically deduplicated.
- A direct decision and a geometrically reused prior receipt on the same interval must agree; conflicting values fail closed.
- `DIRECT_HUMAN_DECISION` is kept distinct from `REUSED_HUMAN_RECEIPT` in the governed packet.
- Exact crop ids and digests remain the evidentiary binding. Human-facing rotation or context expansion is presentation-only and cannot mutate governed geometry.

Authority boundary remains unchanged:

- all validated entries are documented metric relations only;
- `primary_anchor_count = 0`;
- `eligible_for_metric_calibration = false`;
- `primary_anchor_authorized = false` for every row;
- structural identity, canonical geometry, M0-G and canonical write authority remain closed;
- no merge or deploy is authorized by this checkpoint.
