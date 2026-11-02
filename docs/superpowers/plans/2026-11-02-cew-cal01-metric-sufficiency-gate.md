# CEW-CAL-01 Metric Sufficiency Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build source-local metric relation networks from qualified human interval decisions and emit a fail-closed sufficiency gate that stops indiscriminate review and identifies the next evidence requirement.

**Architecture:** Add one focused module that joins governed interval geometry to governed human values, computes source-local consistency diagnostics, ranks targeted pending reviews, and optionally evaluates primary-anchor readiness. Integrate it into the existing external-chain exact-source workflow so the generated artifact carries both the network and gate for TAV-01S/TAV-02S.

**Tech Stack:** Python 3.12.15, stdlib `json/hashlib/statistics/math/pathlib`, `unittest`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-02-cew-cal01-metric-sufficiency-gate-design.md`

## Global Constraints

- Networks are source-local by exact `source_id + source.sha256`; never merge TAV-01S and TAV-02S coordinates.
- Only `REUSED_HUMAN_RECEIPT` and `DIRECT_HUMAN_DECISION` rows with positive `validated_value_m` become metric relations.
- Pending/OCR evidence never receives inferred metric values.
- Diagnostic tolerance is 5% for per-orientation scale residual and horizontal-vs-vertical median drift.
- Relation-network diagnostic sufficiency requires >=4 relations, >=2 per orientation, >=2 sides, and >=1 fully validated chain.
- Affine candidate readiness requires >=4 eligible anchors with a non-collinear fit triple and >=1 holdout; absence of an eligible inventory yields `PRIMARY_ANCHOR_REQUIRED`.
- All structural/canonical/M0-G/write authority remains closed.
- No merge or deploy.

## Review Focus

- Manifest and packet from different source SHA must fail closed.
- A validated row with missing/non-positive metric value must fail closed rather than be ignored.
- Cross-source aggregation must never combine geometry or scale diagnostics.
- Scale outliers just above the 5% bound must prevent diagnostic sufficiency.
- Anchor inventories with 4 collinear eligible points must remain insufficient for affine candidate readiness.

---

### Task 1: Source-local metric relation network

**Files:**
- Create: `experiments/cew_cal01/metric_sufficiency.py`
- Create: `tests/cew_cal01/test_metric_sufficiency.py`

**Interfaces:**
- Consumes: `build_interval_text_review_manifest()` output plus `build_human_review_packet()` output.
- Produces: `build_metric_relation_network(manifest: dict, packet: dict) -> dict`.

- [ ] **Step 1: Write failing relation-network tests**

Tests must assert:
- exact source/digest binding;
- only validated human rows become relations;
- horizontal and vertical endpoint construction;
- `px_per_m` calculation;
- pending rows remain value-free review candidates;
- source/digest drift and non-positive validated values fail closed;
- output authority is closed and relation edges are never fit-eligible.

- [ ] **Step 2: Run contract suite and verify RED**

Run: `python -m unittest discover -s tests/cew_cal01 -p 'test_*.py' -v`
Expected: new tests fail because `experiments.cew_cal01.metric_sufficiency` does not exist.

- [ ] **Step 3: Implement `build_metric_relation_network()` minimally**

Implement deterministic edge order by `review_id`, per-chain validated/total counts, complete-chain ids, orientation/side counts, and canonical network digest.

- [ ] **Step 4: Run contract suite and verify GREEN**

Run: `python -m unittest discover -s tests/cew_cal01 -p 'test_*.py' -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

Commit message: `feat(cew-cal01): build metric relation network`

### Task 2: Consistency audit, targeted review and primary-anchor gate

**Files:**
- Modify: `experiments/cew_cal01/metric_sufficiency.py`
- Modify: `tests/cew_cal01/test_metric_sufficiency.py`

**Interfaces:**
- Consumes: Task 1 network; optional `CEW_CAL01_PRIMARY_ANCHOR_INVENTORY_v1`.
- Produces:
  - `audit_metric_relation_network(network: dict) -> dict`
  - `rank_targeted_human_review(network: dict, limit: int = 4) -> list[str]`
  - `evaluate_metric_sufficiency(network: dict, anchor_inventory: dict | None = None) -> dict`

- [ ] **Step 1: Write failing gate tests**

Tests must assert:
- a synthetic coherent 4-edge network with 2H/2V, two sides and one complete chain is diagnostically sufficient;
- a >5% orientation residual fails diagnostic sufficiency;
- TAV-01S-like one-edge network yields `TARGETED_HUMAN_REVIEW`;
- ranking prefers a one-missing-interval chain, then underrepresented orientation/new side;
- TAV-02S-like coherent network with no anchors yields `INSUFFICIENT` + `PRIMARY_ANCHOR_REQUIRED`;
- four eligible non-collinear anchors permit `SUFFICIENT_FOR_CALIBRATION_CANDIDATE`;
- four collinear anchors remain `INSUFFICIENT`;
- authority stays closed in every state.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.cew_cal01.test_metric_sufficiency -v`
Expected: failures for missing audit/ranking/gate interfaces.

- [ ] **Step 3: Implement audit/ranking/gate minimally**

Use medians from `statistics.median`, relative deviation `abs(value-median)/median`, deterministic ranking tuples, and 2D triangle-area non-collinearity checks.

- [ ] **Step 4: Run full CAL-01 suite and verify GREEN**

Run: `python -m unittest discover -s tests/cew_cal01 -p 'test_*.py' -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

Commit message: `feat(cew-cal01): add metric sufficiency gate`

### Task 3: Exact-source workflow integration

**Files:**
- Modify: `.github/workflows/validate-cew-cal01-external-chain.yml`
- Modify: `tests/cew_cal01/test_external_chain_human_review_workflow.py`
- Modify: `experiments/cew_cal01/metric_sufficiency.py` only if a CLI/materialization wrapper is required by the failing workflow test.

**Interfaces:**
- Consumes: per-source `interval-text-review-manifest.json` and `external-chain-human-review-packet.json`.
- Produces per source:
  - `metric-relation-network.json`
  - `metric-sufficiency-gate.json`

- [ ] **Step 1: Write failing workflow contract assertions**

Require a materialization step for TAV-01S and TAV-02S and workflow assertions that:
- TAV-01S gate is `TARGETED_HUMAN_REVIEW`;
- TAV-02S has 10 relations, 8 horizontal, 2 vertical, >=1 complete chain;
- TAV-02S relation diagnostics are sufficient;
- TAV-02S gate is `INSUFFICIENT` with `PRIMARY_ANCHOR_REQUIRED`;
- both sources have zero calibration/canonical authority.

- [ ] **Step 2: Run full suite and verify RED**

Run: `python -m unittest discover -s tests/cew_cal01 -p 'test_*.py' -v`
Expected: sole new workflow-contract failures because the materialization steps/assertions are absent.

- [ ] **Step 3: Add CLI materialization and workflow integration**

Add:
`python -m experiments.cew_cal01.metric_sufficiency --review-dir <source review dir>`

The CLI writes both JSON artifacts beside the human-review packet. Do not add anchor inputs in this workflow yet; current expected result intentionally exposes `PRIMARY_ANCHOR_REQUIRED`.

- [ ] **Step 4: Run full suite and exact-source workflows**

Run local/CI contract suite, then verify on one exact SHA:
- CEW-CAL-01 Primary Metric Calibration;
- CEW-CAL-01 External Dimension Chains;
- CEW Repository Memory Gate.

Expected: all PASS on the same candidate SHA.

- [ ] **Step 5: Inspect uploaded artifact**

Verify:
- TAV-01S targeted review ids contain no metric values;
- TAV-02S network/gate counts and diagnostics match workflow assertions;
- every new artifact preserves closed authority.

- [ ] **Step 6: Commit**

Commit message: `ci(cew-cal01): materialize metric sufficiency gate`

### Task 4: Governance checkpoint

**Files:**
- Modify: `governance/cew-cal01/CEW_CAL01_EXTERNAL_CHAIN_EXECUTION_LEDGER.md`
- Update PR #187 description after qualification.

**Interfaces:**
- Consumes: exact qualified SHA, workflow run ids, artifact id/digest, source-local gate digests.
- Produces: durable checkpoint stating the next evidence action per source.

- [ ] **Step 1: Record qualified evidence only after all three workflows PASS**

Ledger must state:
- TAV-01S next action: targeted human review with selected ids;
- TAV-02S next action: primary-anchor discovery, not more indiscriminate interval reading;
- no cross-source metric graph;
- all authority remains closed.

- [ ] **Step 2: Update PR #187**

Append the qualified metric-sufficiency checkpoint without changing Draft/merge/deploy state.

- [ ] **Step 3: Re-check PR state and exact workflow status**

Expected: PR open, Draft, not merged; all cited qualification workflows PASS.
