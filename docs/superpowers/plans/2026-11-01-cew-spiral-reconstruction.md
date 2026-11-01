# CEW-SPIRAL-01 — Spiral Reconstruction Implementation Plan

**Date:** 2026-11-01  
**Status:** `QUEUED_SUCCESSOR / CONDITIONAL_ACTIVATION`  
**Activation:** only after `CEW-COL-03F` reaches `TERMINAL_UNRESOLVED` on a fresh exact-SHA qualification and the single CEW WIP slot is released  
**Current branch role:** successor documentation and terminal handoff only; no second active WIP  
**Authority effect:** `NONE`

## Goal

Implement a reuse-first convergence loop from governed evidence to a progressively materialized N12 model without duplicating CEW grammar, prototype learning or similarity capabilities and without bypassing current human/authority gates.

## Frozen reuse inputs

- Engineering drawing grammar — PR `#143`, `098f98d2724c0a16b9293adc366a585f356bc9fc`.
- Deterministic similarity — PR `#116`, `a7020bef3934156c917f5bfe975d888c6ba9e684`.
- Project-local visual learning / zero-prior discovery — PR `#137`, `320755e66a7263f1842f73dc14fb9a0ea8ccd7f8`.
- Current B01 proposal channels and exact-source machinery from the active repository lineage.
- Recovered historical package `archive/historical_packages/v25/` as noncanonical reference material.
- BIMCraft Stage A adapter/receipt/reconciliation implementation already present in `cew_bimcraft/`.

## Guardrails

Throughout Tasks 0–11:

- `canonical_write_authorized=false` unless a later dedicated gate changes it;
- `structural_identity_authorized=false` unless a later dedicated gate changes it;
- `m0g_authorized=false` until a model-specific gate exists;
- similarity/prototypes/grammar remain proposal-only;
- historical DXF cannot satisfy the COL-03F primary-source identity gate;
- a terminally unresolved COL-03F is a valid bounded phase outcome, not an identity resolution;
- the unresolved primary-identity residual remains open and can re-enter the spiral when new primary/manual evidence becomes available;
- no new generic family-discovery, learning-receipt or similarity subsystem may be created.

---

## Task 0 — Activation gate and exact baseline

**Files:** governance/state documentation only.

1. Verify the commit containing `governance/cew-col03f/COL03F_TERMINAL_HANDOFF_v1.json` has fresh exact-SHA PASS for the COL-03F unit and exact-source jobs.
2. Verify the semantic validator reports: `candidate_count=0`, `any_identity_resolved=false`, all authority flags closed, and `next_required_action=ACQUIRE_EXTERNAL_OR_MANUAL_PRIMARY_IDENTITY_EVIDENCE`.
3. Record COL-03F as `TERMINAL_UNRESOLVED`; this closes the bounded acquisition phase without asserting structural identity.
4. Release the single CEW WIP slot from COL-03F.
5. Freeze the exact successor base SHA and current authority flags.
6. Record the frozen reuse refs listed above and verify they remain retrievable.
7. Create the implementation branch only after steps 1–6 pass.

**Acceptance:** CEW-SPIRAL-01 activates only after fresh exact-SHA evidence proves the COL-03F terminal fail-closed outcome. No successor may reinterpret historical DXF as the missing primary bridge evidence.

---

## Task 1 — CEW-DXF-01 contract: RED first

**Create:**

- `experiments/cew_dxf01/__init__.py`
- `tests/cew_dxf01/test_contract.py`
- `tests/cew_dxf01/test_inventory.py`
- `tests/cew_dxf01/test_fail_closed.py`
- `governance/cew-dxf01/CEW_DXF01_TOOLCHAIN_v1.json`
- `requirements/cew-dxf01.lock.txt`

Write failing tests requiring:

- exact input SHA/package lineage;
- explicit direct pin `ezdxf==1.4.5` in the dedicated CEW-DXF-01 lock file;
- qualification of that direct pin inside CEW-DXF-01 rather than inheritance of authority from a transitive dependency;
- read-only operation;
- stable entity/layer/text/block/dimension inventory;
- deterministic normalized digest;
- `authority_effect=NONE`;
- rejection of mutation/promotion fields.

Version rationale: the current qualified Python 3.12.15 / Ubuntu 24.04 B01 environment resolved `ezdxf 1.4.5` transitively through `build123d==0.13.0`. This observation selects the first CEW-DXF-01 candidate baseline only. Transitive presence is not CEW qualification and grants no authority.

**RED evidence:** tests must fail because no CEW-DXF-01 reader/direct toolchain contract exists yet.

---

## Task 2 — CEW-DXF-01 reader: GREEN

**Create:**

- `experiments/cew_dxf01/reader.py`
- `experiments/cew_dxf01/normalize.py`
- `experiments/cew_dxf01/exact_source.py`

Implement the smallest reader needed to satisfy Task 1.

Required normalized observations:

- DXF/version/units metadata when observable;
- layers;
- entity counts;
- `TEXT`/`MTEXT` with placement;
- `INSERT`/block references;
- block definitions/attributes where observable;
- dimensions;
- deterministic extents;
- stable source-bound IDs derived from exact source + entity handle/normalized locator, never semantic guesses.

Run the new suite twice and assert identical normalized output digest.

**Acceptance:** `CEW_DXF01_READ_QUERY_PASS`; no writes and no semantic promotion.

---

## Task 3 — Historical DXF qualification receipt

**Create:**

- `experiments/cew_dxf01/validate_artifact.py`
- `.github/workflows/validate-cew-dxf01-read-query.yml`
- `governance/cew-dxf01/schemas/DXF_OBSERVATION_RECEIPT_v1.schema.json`

Replay from the exact historical package transport/materialized asset and emit a receipt containing source digest, tool version, normalized digest and authority flags.

Add a regression proving that a DXF observation marked historical cannot be substituted for `PRIMARY_SOURCE_IDENTITY_BRIDGE_EVIDENCE`.

**Acceptance:** exact-source replay PASS + authority-boundary PASS.

---

## Task 4 — Port the engineering grammar boundary

**Do not copy the historical subsystem wholesale.** Port only the bounded contract/rules needed by the active data model.

**Create/modify:**

- adapter under a dedicated `cew_spiral/` package;
- tests for `GraphicPrimitive/TechnicalToken -> TechnicalRelation -> StructuralHypothesis`;
- provenance mapping for `PROJECT_LEARNED`, `VERIFIED_REFERENCE`, `METHOD_RULE`, `HUMAN_TAUGHT_PROJECT_RULE`.

Mandatory tests:

- rectangle alone cannot imply column;
- dimension without target relation is insufficient;
- topology outranks visual proximity for identity proposals;
- OCR confidence cannot become engineering confidence;
- cross-source conflict fails closed.

**Acceptance:** grammar proposal output only; zero authority escalation.

---

## Task 5 — Adapt prototype memory and deterministic similarity

Reuse PR #137 learning receipts/prototype memory and PR #116 deterministic similarity through adapters.

Tests must prove:

- only human-taught project-local prototypes seed semantic search;
- negative examples penalize similarity;
- ambiguous examples do not form centroids;
- component scores/reason codes remain inspectable;
- `FIND_SIMILAR` never creates object type/family/structural identity;
- candidate scene is bound to the same governed source revision where required.

**Acceptance:** candidate proposals suitable for human cluster review, nothing more.

---

## Task 6 — Spiral Orchestrator contract: RED first

**Create:**

- `cew_spiral/contracts.py`
- `tests/cew_spiral/test_routing_contract.py`
- `tests/cew_spiral/test_authority_boundary.py`
- `tests/cew_spiral/test_determinism.py`

Specify `SpiralRouteDecision` and receipts before implementation.

Required RED tests:

- stronger qualified source-native evidence routes before OCR;
- unavailable vector evidence falls back to governed raster/OCR route;
- a historical-only identity claim remains blocked;
- same governed inputs yield same residual selection and route;
- no route can change authority flags;
- stable residual-ID tie-break is deterministic.

---

## Task 7 — Spiral Orchestrator implementation: GREEN

**Create:**

- `cew_spiral/router.py`
- `cew_spiral/residuals.py`
- `cew_spiral/receipt.py`

Implement lexicographic residual selection:

1. explicit model-relation blocker;
2. dependency-graph model impact;
3. stronger evidence availability;
4. bounded acquisition cost class;
5. stable residual ID.

The router selects work and capabilities; it never decides structural truth.

**Acceptance:** deterministic route/replay PASS, no semantic authority added.

---

## Task 8 — OCR fallback benchmark

Run only after Tasks 1–7 establish whether vector text is available.

Baseline: frozen Tesseract already used by CEW.  
Candidate: PaddleOCR only as a separate benchmark if needed.

Use a small fixed set of source-bound regions where vector text is absent. Compare:

- token correctness;
- position/bounding-box usefulness;
- rotation handling;
- deterministic/replay characteristics;
- installation/runtime cost.

Do not replace the baseline automatically. Record `ADOPT`, `ADOPT_CONDITIONAL`, `BENCHMARK_ONLY` or `REJECT` through a separate decision artifact.

---

## Task 9 — Optional native DWG qualification

Execute only if an immutable original DWG source is available.

Freeze tool/version/source digest and test only non-authoritative extraction of positioned text, blocks and attributes. Any candidate tool remains outside CEW authority and must expose replayable source-bound observations.

If no immutable DWG exists, record `NOT_APPLICABLE` and continue; this task must not block the spiral.

---

## Task 10 — First accepted N12 model delta and BIMCraft projection

Prerequisite: upstream human/governance gate has accepted a small bounded set of N12 StructuralObjects or equivalent model objects with sufficient identity/geometry.

Reuse existing `cew_bimcraft` adapter.

Execute:

`accepted CEW objects -> command plan -> BIMCraft -> read-back -> IFC4 -> IfcOpenShell -> reconciliation`

Tests/receipts must prove:

- CEW IDs and provenance survive projection;
- expected and observed semantic object counts match;
- geometry/section fields in scope reconcile;
- native GUID nondeterminism is ignored as semantic identity;
- mismatch fails closed;
- no BIM output feeds back as new evidentiary authority.

**Acceptance:** first bounded `MODEL_DELTA_PROJECTION_PASS`.

---

## Task 11 — Complete one full spiral cycle

With the first model delta materialized:

1. regenerate the residual ledger from model + governed evidence;
2. select the next residual deterministically;
3. acquire/interpret only the evidence required for that residual;
4. produce the route/evidence/proposal/human-decision receipts;
5. update the model only if the relevant gate accepts the delta;
6. replay the cycle from frozen inputs.

**Acceptance:** same inputs reproduce the same routing decision and accepted model delta; updated inputs produce the next bounded residual without conversation memory.

---

## Verification matrix

Before declaring CEW-SPIRAL-01 complete, require fresh exact-SHA evidence for:

- CEW-DXF-01 unit + exact-source replay;
- direct `ezdxf` toolchain pin and version receipt;
- grammar adapter regressions;
- prototype/similarity adapter regressions;
- spiral routing determinism;
- authority-boundary tests;
- predecessor CEW regressions materially touched by adapters;
- BIMCraft semantic reconciliation for the first accepted N12 slice;
- repository-memory validation;
- Human Review evidence for every promotion gate that requires it.

## Stop conditions

Stop and return `REWORK_REQUIRED` rather than patching around the gate if:

- COL-03F has not achieved fresh exact-SHA `TERMINAL_UNRESOLVED` qualification when implementation is about to begin;
- the recovered historical DXF is being used as primary truth or as a substitute for the missing COL-03F primary identity evidence;
- a transitive `ezdxf` installation is treated as a CEW-qualified toolchain;
- a new subsystem duplicates grammar, prototype memory or generic similarity;
- an OCR score is used as engineering confidence;
- a model engine is allowed to create CEW identity;
- replay depends on conversation state or manual unprovenanced coordinates;
- a required human review is missing.
