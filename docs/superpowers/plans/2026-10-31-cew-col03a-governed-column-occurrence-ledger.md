# CEW COL-03A Governed Column Occurrence Ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, fail-closed ledger containing exactly one neutral `COL-OCC-*` record for every governed positive column occurrence in the closed COL-02 evidence set, with complete exact-source provenance and no documentary or structural identity promotion.

**Architecture:** Add a successor package `experiments/cew_col03a` that consumes only governed COL-02 receipts plus fresh exact-source COL-02 evidence. First normalize positive graphical evidence, then attach frozen proposal/repair geometry, collapse only strong-lineage duplicates, detect geometry-only ambiguity without auto-merging, assign deterministic occurrence IDs, and emit ledger/reconciliation/closure artifacts. Exact-source reconstruction may replay the frozen 611-proposal producer only as a geometry lookup keyed by already-governed candidate IDs; it must never use regenerated proposals to discover or select new occurrences.

**Tech Stack:** Python 3.12.15, standard library JSON/hashlib/dataclasses-or-dicts consistent with existing CEW code, `unittest`, existing `cew_b01` exact-source toolchain, OpenCV/Tesseract only through the existing COL-02 replay path, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-31-cew-col03a-governed-column-occurrence-ledger-design.md`

## Global Constraints

- Implementation lineage starts from exact qualified COL-02 head `0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4`.
- Exact source remains `archive/documentazione_originaria/tavola 5.pdf`, SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`.
- Source identifiers remain `CEW-N12-SRC-TAV05S-V2143DBCF`, `CEW-N12-PAGE-TAV05S-P001`, `CEW-N12-XFORM-TAV05S-P001`.
- Frozen neutral proposal count remains exactly 611; `COL02-FP-*` IDs are immutable historical proposal identities.
- `col02-occurrence-coverage-closure.json` must be present from a fresh replay and must state `occurrence_coverage_complete = true` before COL-03A can close.
- COL-03A may create only neutral documentary occurrence IDs `COL-OCC-*`; it may not assign support number, text identity, family, section, fixed line, vertical chain, 57-node identity or canonical geometry.
- Regenerated COL-02 proposals are lookup evidence only. Candidate selection must come exclusively from governed positive review lineage.
- Geometry-only evidence must never auto-merge distinct candidate IDs in v1. Strong lineage may collapse records; substantial overlap between distinct final groups is a conflict requiring review.
- Representation precedence is: governed final whole-symbol/outer-envelope repair when present; otherwise frozen proposal geometry. The original proposal bbox remains the stable anchor for occurrence ordering.
- Per-occurrence defaults remain `documentary_label_state = NOT_EVALUATED`, `structural_identity_state = NOT_EVALUATED`, `canonical_geometry_state = NOT_AUTHORIZED`, and all canonical/G2C/G3 authorization booleans false.
- Historical COL-02 governance and evidence files are never rewritten.
- No merge, deploy, G2C, G3 or EdiLus promotion is authorized by COL-03A.

## Frozen governed inputs

Committed governance receipts:

- `governance/cew-col02/COLUMN_FOOTPRINT_HUMAN_REVIEW_v1.json` — positive prototype decisions.
- `governance/cew-col02/COL02_PROTOTYPE_GUIDED_HUMAN_REVIEW_v1.json` — positive S01–S24 target decisions.
- `governance/cew-col02/COL02_RESIDUAL_MOBILE_HUMAN_REVIEW_v1.json` — append-only residual review; effective state must be obtained through the existing `replay_mobile_review()` contract.
- `governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json` — five repair-eligible fragmented symbols plus the rejected `COL02-FP-0106`.
- `governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v2.json` — final 5/5 PASS graphical repairs.

Fresh exact-source evidence generated upstream in the same qualification run:

- `evidence/cew-col02/footprint-text-binding/col02-audit.json`
- `evidence/cew-col02/footprint-text-binding/col02-prototype-guided-search.json`
- `evidence/cew-col02/footprint-text-binding/col02-residual-occurrence-reconciliation.json`
- `evidence/cew-col02/footprint-text-binding/col02-axis-aware-whole-symbol-repair.json`
- `evidence/cew-col02/footprint-text-binding/col02-occurrence-coverage-closure.json`

Current frozen evidence implies, as a qualification witness rather than a production oracle: 2 prototype positives + 15 prototype-guided positives + 2 effective direct residual `PILASTRO` decisions + 5 final repaired PASS occurrences = 24 governed positive occurrences before any strong-lineage collapsing. The exact-source job must verify the derived count is 24; production selection logic must derive it from receipts rather than hard-code the 24 candidate IDs.

## File Structure

- Create `experiments/cew_col03a/__init__.py` — package marker only.
- Create `experiments/cew_col03a/governed_inputs.py` — validate authority/schema lineage and normalize governed positive evidence into a common evidence-item contract.
- Create `experiments/cew_col03a/occurrence_ledger.py` — attach source/repair geometry, perform strong-lineage grouping, detect ambiguous duplicates, assign stable occurrence IDs, and build ledger/reconciliation/closure payloads.
- Create `experiments/cew_col03a/exact_source.py` — file/path orchestration, fresh source/proposal replay as lookup, deterministic double-build, JSON emission and CLI summary.
- Create `tests/cew_col03a/test_governed_inputs.py` — receipt normalization and authority tests.
- Create `tests/cew_col03a/test_occurrence_ledger.py` — geometry precedence, dedup/conflict, stable ID and closure tests.
- Create `tests/cew_col03a/test_exact_source_writer.py` — temporary-file writer/emission contract without external source materialization.
- Create `.github/workflows/validate-cew-col03a-governed-occurrence-ledger.yml` — isolated COL-03A unit + exact-source qualification.

## Review Focus

- Append-only mobile receipt with multiple `UNDO_LAST` events: only the two effective `PILASTRO` decisions may enter as direct positives; undone decisions must not leak into the ledger. Pin in Task 1.
- A repaired occurrence has both original proposal bbox and reconstructed whole-symbol bbox: the original bbox must remain the stable anchor while the governed repair becomes the primary graphical representation. Pin in Task 2.
- Two evidence paths reference the same frozen proposal: they must collapse to one occurrence; two different candidate IDs with >= 90% overlap of the smaller bbox must not auto-merge and must produce `AMBIGUOUS_DUPLICATE`. Pin in Task 3.
- Input order changes, filesystem order changes or receipt decision order changes: resulting `COL-OCC-*` IDs and ledger digest must remain identical. Pin in Task 4.
- Any source SHA, closure state, exact-source reconstruction flag or downstream authority drift: `occurrence_ledger_complete` must remain false or validation must fail before a true closure is emitted. Pin in Tasks 1, 4 and 5.

---

### Task 1: Governed positive evidence adapters

**Files:**
- Create: `experiments/cew_col03a/__init__.py`
- Create: `experiments/cew_col03a/governed_inputs.py`
- Create: `tests/cew_col03a/test_governed_inputs.py`

**Interfaces:**
- Reuse: `experiments.cew_col02.residual_occurrence_reconciliation.replay_mobile_review(bundle: dict[str, Any]) -> dict[str, Any]`.
- Produce: `validate_col03a_input_authority(payload: dict[str, Any], label: str) -> None`.
- Produce: `collect_governed_positive_evidence(*, prototype_receipt: dict[str, Any], prototype_guided_receipt: dict[str, Any], mobile_receipt: dict[str, Any], reconciliation_manifest: dict[str, Any], reconciliation_receipt: dict[str, Any], repair_manifest: dict[str, Any], repair_review_receipt: dict[str, Any], coverage_closure: dict[str, Any]) -> list[dict[str, Any]]`.
- Normalized evidence item keys: `evidence_id`, `candidate_id`, `evidence_class`, `graphical_decision`, `discovery_path`, `human_review_receipt`, `repair_id | null`, `human_added_point_event_ids`, `lineage`.

- [ ] **Step 1: Write failing schema/authority tests**

Pin that:
- prototype receipt contributes exactly P01/P02 positive graphical evidence and ignores P03–P16 negatives;
- prototype-guided receipt contributes only `COLUMN_FOOTPRINT_CONFIRMED` decisions;
- mobile receipt is replayed through `replay_mobile_review()` and contributes only effective `PILASTRO`, never `NON_PILASTRO`, `INQUADRATO_MALE` or undone decisions;
- repair evidence contributes only candidates that are repair-eligible in reconciliation, present in the repair manifest and `PASS` in graphical review v2;
- `COL02-FP-0106` is never positive;
- coverage closure must be true and all downstream authority flags false;
- any structural/canonical authority drift raises `ValueError`.

Use actual committed receipts for the prototype/prototype-guided/mobile cases and synthetic minimal fresh manifests for generated evidence.

- [ ] **Step 2: Acquire causal RED**

Run: `python -m unittest discover -s tests/cew_col03a -p 'test_*.py' -v`

Expected: FAIL because `experiments.cew_col03a.governed_inputs` does not exist.

- [ ] **Step 3: Implement the minimal adapters**

Selection rules are exact:
- prototype: `column_graphic_decision == "COLUMN_FOOTPRINT_CONFIRMED"` and `prototype_eligible is True`;
- prototype-guided: `graphical_decision == "COLUMN_FOOTPRINT_CONFIRMED"`;
- residual direct: effective mobile action `PILASTRO` only;
- repaired successor: reconciliation `repair_eligible is True` + repair manifest source candidate + final v2 `decision == "PASS"`.

For repaired successors, preserve whether lineage came from `REFRAME_CONFIRMATION` or a human-added point binding by reading the fresh reconciliation manifest. Do not use OCR, support IDs, expected support counts or topology.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest discover -s tests/cew_col03a -p 'test_*.py' -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: normalize COL-03A governed positive evidence`.

### Task 2: Exact-source geometry attachment and representation precedence

**Files:**
- Modify: `experiments/cew_col03a/occurrence_ledger.py` (create in this task)
- Create/modify: `tests/cew_col03a/test_occurrence_ledger.py`

**Interfaces:**
- Produce: `build_proposal_geometry_index(proposals_payload: dict[str, Any]) -> dict[str, dict[str, Any]]`.
- Produce: `attach_exact_source_geometry(*, evidence_items: list[dict[str, Any]], proposal_index: dict[str, dict[str, Any]], repair_manifest: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]`.
- Each attached record must contain `candidate_id`, `anchor_bbox`, `primary_graphical_representation`, `source_version_id`, `source_path`, `source_sha256`, `page_id`, `page_index`, `page_transform_id`, `exact_source_reconstructible`, `lineage_complete` plus the evidence lineage from Task 1.

- [ ] **Step 1: Write failing geometry contracts**

Pin that:
- proposal index requires exactly 611 unique `candidate_id` values;
- every governed positive candidate must exist in the frozen proposal index;
- non-repaired occurrence uses proposal bbox for both `anchor_bbox` and primary representation;
- repaired occurrence keeps proposal bbox as `anchor_bbox` but uses `repair_manifest.repairs[].reconstructed_bbox` as primary representation and preserves `repair_id`;
- missing proposal, missing reconstructed repair bbox, wrong source SHA or missing page-transform lineage marks reconstruction invalid or raises before closure;
- no new candidate is created from proposal geometry alone.

- [ ] **Step 2: Acquire RED**

Run: `python -m unittest tests.cew_col03a.test_occurrence_ledger -v`

Expected: FAIL on missing geometry APIs.

- [ ] **Step 3: Implement geometry lookup only**

Use normalized source coordinates already produced by COL-02. Do not run OCR or candidate selection. `build_proposal_geometry_index()` is a keyed reconstruction table, not a detector interface.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.cew_col03a.test_occurrence_ledger -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: attach exact-source geometry to COL-03A evidence`.

### Task 3: Strong-lineage deduplication and ambiguity detection

**Files:**
- Modify: `experiments/cew_col03a/occurrence_ledger.py`
- Modify: `tests/cew_col03a/test_occurrence_ledger.py`

**Interfaces:**
- Produce: `collapse_strong_lineage(records: list[dict[str, Any]]) -> list[dict[str, Any]]`.
- Produce: `smaller_bbox_overlap(a: dict[str, float], b: dict[str, float]) -> float`.
- Produce: `detect_ambiguous_duplicates(groups: list[dict[str, Any]], *, overlap_threshold: float = 0.90) -> list[dict[str, Any]]`.

- [ ] **Step 1: Write failing dedup/conflict tests**

Pin that:
- two evidence records with the same frozen `candidate_id` collapse to one group while retaining both discovery paths and receipts;
- repair lineage for a source candidate remains one occurrence, not a new occurrence;
- different candidate IDs are never auto-merged by geometry in v1;
- different candidate IDs whose primary bboxes overlap by at least 90% of the smaller bbox produce `AMBIGUOUS_DUPLICATE` with both IDs recorded;
- adjacent/non-overlapping candidates remain independent with no conflict;
- contradictory positive/negative governed decisions for the same candidate produce `CONTRADICTORY_GRAPHICAL_DECISIONS`, not silent precedence.

- [ ] **Step 2: Acquire RED**

Run the focused occurrence-ledger tests. Expected: only new dedup/conflict tests fail.

- [ ] **Step 3: Implement strong-lineage-only collapsing**

Group on immutable proposal lineage (`candidate_id`) and explicit repair-source lineage. Union evidence arrays deterministically. Geometry is used only to flag ambiguity across different groups, never to merge them.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.cew_col03a.test_occurrence_ledger -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: reconcile COL-03A occurrence lineage fail closed`.

### Task 4: Deterministic `COL-OCC-*` IDs, ledger and closure semantics

**Files:**
- Modify: `experiments/cew_col03a/occurrence_ledger.py`
- Modify: `tests/cew_col03a/test_occurrence_ledger.py`

**Interfaces:**
- Produce: `assign_occurrence_ids(groups: list[dict[str, Any]]) -> list[dict[str, Any]]`.
- Produce: `build_occurrence_ledger(*, records: list[dict[str, Any]], source: dict[str, Any]) -> dict[str, Any]`.
- Produce: `build_reconciliation_report(*, evidence_items: list[dict[str, Any]], occurrences: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> dict[str, Any]`.
- Produce: `build_ledger_closure(*, ledger: dict[str, Any], reconciliation: dict[str, Any], col02_closure: dict[str, Any], qualified_base_sha: str) -> dict[str, Any]`.

- [ ] **Step 1: Write failing stable-ID tests**

The stable sort key must be:

`(source_version_id, page_index, anchor_bbox.y, anchor_bbox.x, anchor_bbox.height, anchor_bbox.width, candidate_id)`.

Pin that:
- shuffled input evidence produces byte-identical occurrence order and IDs;
- first ID is `COL-OCC-0001` and IDs are contiguous/unique;
- repaired primary bbox changes do not affect ordering while the original proposal `anchor_bbox` is unchanged;
- support number, OCR token, family, 57-node ID or 27x5 membership cannot affect the sort key.

- [ ] **Step 2: Write failing closed-set and authority tests**

Pin bidirectional accounting:
- every governed positive evidence item maps to exactly one occurrence;
- every occurrence maps to at least one governed positive evidence item;
- no orphan occurrence exists;
- unresolved conflict, non-reconstructible occurrence or incomplete lineage yields `occurrence_ledger_complete = false`;
- clean closed set yields true;
- each occurrence carries `documentary_label_state = NOT_EVALUATED`, `structural_identity_state = NOT_EVALUATED`, `canonical_geometry_state = NOT_AUTHORIZED` and false canonical/G2C/G3 flags;
- closure authority remains false for support/text/family/section/fixed-line/structural identity, canonical write, G2C, G3 and merge.

- [ ] **Step 3: Acquire RED**

Run the focused test module. Expected: stable-ID/closure tests fail because the APIs do not exist.

- [ ] **Step 4: Implement deterministic ledger/reconciliation/closure builders**

Payload schemas:
- ledger `schema_id = "CEW_COL03A_GOVERNED_COLUMN_OCCURRENCE_LEDGER"`, `schema_version = 1`;
- reconciliation `schema_id = "CEW_COL03A_COLUMN_OCCURRENCE_RECONCILIATION"`, `schema_version = 1`;
- closure `schema_id = "CEW_COL03A_COLUMN_OCCURRENCE_LEDGER_CLOSURE"`, `schema_version = 1`.

The reconciliation payload records input counts by evidence class, source-item→occurrence mappings, occurrence→source-item mappings, conflicts, final cardinality and digests. The closure may become true only after all spec invariants pass.

- [ ] **Step 5: Verify GREEN**

Run: `python -m unittest discover -s tests/cew_col03a -p 'test_*.py' -v`

Expected: PASS.

- [ ] **Step 6: Commit**

Commit message: `feat: build deterministic COL-03A occurrence ledger`.

### Task 5: Exact-source writer and deterministic replay

**Files:**
- Create: `experiments/cew_col03a/exact_source.py`
- Create: `tests/cew_col03a/test_exact_source_writer.py`

**Interfaces:**
- Reuse for exact-source reconstruction: `experiments.cew_col02.axis_aware_whole_symbol_exact_source._regenerate_source_analysis_and_proposals() -> tuple[image, analysis, proposals_payload]`.
- Produce: `build_col03a_from_payloads(...) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]` for testable in-memory orchestration.
- Produce: `write_col03a_artifacts(*, ...paths..., output_root: Path) -> dict[str, Any]` returning a summary containing ledger/reconciliation/closure digests.
- CLI module writes:
  - `evidence/cew-col03a/column-occurrence-ledger.json`
  - `evidence/cew-col03a/column-occurrence-reconciliation.json`
  - `evidence/cew-col03a/column-occurrence-ledger-closure.json`

- [ ] **Step 1: Write failing writer tests using temporary JSON inputs**

Pin that the writer:
- writes all three files with sorted-key canonical formatting and trailing newline;
- does not modify input files;
- emits a closure digest tied to ledger + reconciliation digests;
- emits `occurrence_ledger_complete = false` when an ambiguity conflict is present rather than silently resolving it;
- emits true only with all authority fields closed;
- produces byte-identical artifacts when normalized evidence input order is reversed.

- [ ] **Step 2: Acquire RED**

Run: `python -m unittest tests.cew_col03a.test_exact_source_writer -v`

Expected: FAIL because exact-source writer does not exist.

- [ ] **Step 3: Implement writer and CLI**

The real CLI must:
1. load committed governance receipts;
2. load fresh COL-02 generated evidence listed above;
3. assert the COL-02 closure is complete and qualified lineage values/digests match;
4. replay the frozen 611-proposal producer through the existing COL-02 helper only to rebuild the geometry lookup;
5. build COL-03A twice from the same frozen inputs, with a deliberately different evidence-item ordering on the second pass;
6. require canonical ledger/reconciliation/closure bytes to match;
7. write the three artifacts;
8. print a compact `CEW_COL03A_OCCURRENCE_LEDGER=...` summary.

- [ ] **Step 4: Verify writer GREEN**

Run: `python -m unittest discover -s tests/cew_col03a -p 'test_*.py' -v`

Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: emit COL-03A exact-source occurrence ledger`.

### Task 6: Isolated COL-03A qualification workflow

**Files:**
- Create: `.github/workflows/validate-cew-col03a-governed-occurrence-ledger.yml`
- Modify only if required for trigger coverage: this plan/spec documentation paths; do not modify the COL-02 workflow to make COL-03A part of COL-02 semantics.

**Interfaces:**
- Consumes: current candidate SHA whose ancestry includes `0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4`, committed governance receipts and frozen source commit `78c20a52db4f391ce0d13b9705b9f04737e218c9`.
- Produces: exact-SHA unit result, fresh COL-02 prerequisite evidence, fresh COL-03A artifacts and uploaded artifact `cew-col03a-governed-occurrence-ledger`.

- [ ] **Step 1: Add workflow with separate unit and exact-source jobs**

Unit job:
- checkout exact candidate head;
- Python 3.12.15;
- run `python -m unittest discover -s tests/cew_col03a -p 'test_*.py' -v`;
- run existing `python -m unittest discover -s tests/cew_col02 -p 'test_*.py' -v` as regression.

Exact-source job:
- checkout exact candidate head;
- verify `git merge-base --is-ancestor 0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4 HEAD`;
- install the same frozen Tesseract/B01 toolchain as current COL-02 exact-source qualification;
- fetch archival source commit `78c20a52db4f391ce0d13b9705b9f04737e218c9`;
- regenerate the COL-02 prerequisites in order: exact-source audit → prototype-guided search → occurrence sweep → residual reconciliation → whole-symbol repair → occurrence-coverage closure;
- run `python -m experiments.cew_col03a.exact_source`.

- [ ] **Step 2: Add exact-source assertions**

The workflow must assert from emitted JSON:
- `occurrence_ledger_complete is True`;
- final ledger cardinality is 24 on this frozen base;
- input evidence-class counts are 2 prototype + 15 prototype-guided + 2 direct residual + 5 repaired successor;
- 24/24 occurrences are `exact_source_reconstructible` and `lineage_complete`;
- 0 conflicts, 0 orphan occurrences, 0 missing closed-set items;
- occurrence IDs are 24 unique contiguous `COL-OCC-*` values;
- no occurrence contains an assigned documentary label, support identity, family, section, fixed line, vertical chain or canonical node identity;
- all professional/canonical authority flags remain false;
- upstream COL-02 proposal count is still 611 and `COL02-FP-*` IDs appear only as lineage/source geometry references.

- [ ] **Step 3: Upload only COL-03A output as successor artifact**

Upload `evidence/cew-col03a/` with `if-no-files-found: error`; do not rewrite or commit generated evidence.

- [ ] **Step 4: Acquire fresh exact-SHA GREEN**

Expected:
- COL-03A unit PASS;
- COL-02 regression PASS;
- fresh exact-source prerequisite replay PASS;
- COL-03A exact-source gate PASS;
- uploaded artifact contains exactly the three governed JSON outputs plus any explicit diagnostic manifest added by the implementation plan, but no canonical CAD/model writes.

- [ ] **Step 5: Commit**

Commit message: `ci: qualify COL-03A occurrence ledger on exact source`.

### Task 7: Governed checkpoint and handoff to COL-03B

**Files:**
- No product file changes unless qualification exposes a defect.
- PR metadata/checkpoint only after a fresh exact-head run.

**Interfaces:**
- Consumes: exact candidate SHA, COL-03A workflow run, artifact ID/digest and the three JSON digests.
- Produces: auditable checkpoint stating whether COL-03A closed mechanically or requires bounded Human Review for a conflict.

- [ ] **Step 1: Verify exact candidate state**

Confirm branch/PR is open, Draft, non-merged; expected head is unchanged during qualification; review threads are clear or explicitly accounted for.

- [ ] **Step 2: Independently inspect the fresh artifact**

Confirm closure true, 24 occurrences, 0 conflicts, bidirectional mapping complete, deterministic digests, source SHA exact and all authority closed. If any conflict exists, do not patch by inference: keep closure false and produce only the conflict set for bounded Human Review.

- [ ] **Step 3: Record checkpoint**

Update the successor PR description/comment with exact SHA, workflow run, artifact ID/digest, ledger digest, reconciliation digest, closure digest, cardinality and authority boundary.

- [ ] **Step 4: Stop at the approved boundary**

Do not start COL-03B, support identity, TAV.7 matching, 57-node mapping, section/fixed-line work, merge or deploy as an automatic consequence of COL-03A PASS.

## Self-review result

- **Spec coverage:** all sections 1–22 are mapped to Tasks 1–7. No spec requirement requires a new detector, OCR pass or structural matching.
- **Design call made in the plan:** v1 performs **no geometry-only auto-merge**. Geometry overlap is diagnostic only; >=90% overlap of the smaller bbox across distinct candidate IDs is an `AMBIGUOUS_DUPLICATE` conflict. This is the safest implementation of the spec's permissive geometry-only clause and avoids creating identity by proximity.
- **Type/interface consistency:** Task 1 emits evidence items; Task 2 enriches them; Task 3 groups them; Task 4 assigns IDs/builds payloads; Task 5 only orchestrates/writes; Task 6 qualifies the same interfaces.
- **Review Focus coverage:** mobile undo, repair precedence, strong-lineage dedup vs geometry ambiguity, deterministic IDs, and authority/source drift each have explicit tests.
- **Scope:** COL-03A remains one bounded subsystem. COL-03B is explicitly excluded.

**Plan state:** READY FOR EXECUTION / SPEC APPROVED / NO PRODUCT CODE WRITTEN YET / NO MERGE / NO DEPLOY.
