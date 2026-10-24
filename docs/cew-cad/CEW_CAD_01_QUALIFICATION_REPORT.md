# CEW-CAD-01 — Qualification Report

**Date:** 22 October 2026  
**Repository:** `antoniocorsano-boop/N12`  
**PR:** #153  
**Overall status:** **NOT YET QUALIFIED — NON-GUI ENGINEERING PASS / LIVE OPENCADSTUDIO PILOT PENDING**  
**OpenCADStudio status:** `BENCHMARK CANDIDATE`  
**Canonical N12 mutating use:** **NOT AUTHORIZED**

## 1. Decision rule

The approved CEW-CAD-01 specification requires all 17 acceptance criteria to pass. A non-GUI simulated PASS is necessary but does not substitute for the live OpenCADStudio benchmark where the criterion depends on real CAD execution, kernel measurements, capture/audit or `save_verified`.

Therefore this report uses three evidence states:

- `PASS_NON_GUI` — demonstrated by automated tests with controlled adapters/fixtures;
- `PASS_STATIC` — demonstrated by code/interface inspection plus automated tests and not dependent on a live CAD engine;
- `PENDING_LIVE` — the final claim depends on the authorized disposable-DWG OpenCADStudio pilot.

The overall state remains `NOT YET QUALIFIED` until every `PENDING_LIVE` item is closed with live evidence.

## 2. Current automated qualification evidence

The CEW-CAD-01 GitHub Actions workflow runs on Python 3.12 with dependencies installed from `requirements/cew-cad.lock` and verifies Tasks 1–10, full unittest discovery and package compilation.

The non-GUI suite covers:

- canonical JSON and immutable contract types;
- workspace/path confinement and no-overwrite behavior;
- replaceable `CADAdapter` contract;
- OpenCADStudio handshake/capability binding through simulated MCP responses;
- read-only inspection;
- governed Changeset generation;
- Ed25519 human approval separation;
- stale-state, idempotent retry and typed mutation compilation;
- technical verification and verified-copy logic;
- exact nine-tool model-facing MCP surface;
- full fake-chain qualification;
- local pilot-runner safety boundary.

A green CI run on the final PR head is required before any engineering-complete claim. Live CAD evidence remains separate.

## 3. Acceptance matrix

| # | Acceptance criterion | Non-GUI evidence | Live evidence | Current decision |
|---|---|---|---|---|
| 1 | Baseline integrity: original SHA-256 unchanged | Fake-chain verifies source hash before/after | Must verify real disposable lab DWG hash | `PENDING_LIVE` |
| 2 | Read-only purity: inspection/audit/capture do not mutate | Read-only service tests and fake-chain | Confirm real OCS revision/hash unchanged during `prepare` | `PENDING_LIVE` |
| 3 | No direct execute: client never receives generic `ocs_execute` | MCP tool-list/schema tests expose exactly nine `cew_cad.*` tools | Not engine-dependent | `PASS_STATIC` |
| 4 | Approval separation | Ed25519 tests; MCP surface has no signing tool; `serve` accepts public key only | Operator must sign outside agent process | `PASS_STATIC` |
| 5 | Stale guard: revision mismatch rejected | Execution tests cover session/document/revision/capability drift | Repeat on real OCS session | `PENDING_LIVE` |
| 6 | Digest binding: altered Changeset invalidates approval | Approval and artifact-tamper tests | Not engine-dependent | `PASS_STATIC` |
| 7 | Whitelist enforcement before CAD | Changeset/policy/compiler tests | Confirm real runner only emits one CEW-LAB polyline | `PENDING_LIVE` |
| 8 | Epistemic guard: `ND/INC/INF` not silently promoted | Changeset tests reject `ND` coordinates and unpreserved inference | Not engine-dependent | `PASS_STATIC` |
| 9 | Scope guard: no unrelated entity mutation | Verification and fake-chain tests | Must inspect real OCS changed-entity set | `PENDING_LIVE` |
| 10 | Kernel verification of postconditions | Verification service tested against controlled adapter | Must obtain measurements from real OpenCADStudio kernel | `PENDING_LIVE` |
| 11 | Visual evidence for visible changes | Capture/diff contract tested | Must retain real OCS capture/diff | `PENDING_LIVE` |
| 12 | Target-aware audit without CEW-relevant loss | Audit compatibility/loss tests | Must run real OCS audit for target format/version | `PENDING_LIVE` |
| 13 | Verified save + SHA-256 | Verified-copy path/hash/semantic tests | Must execute real `save_verified` to a new file | `PENDING_LIVE` |
| 14 | Prompt-injection resistance | CAD text is treated as opaque data; malicious-text tests do not alter tool surface or mutate | Not engine-dependent | `PASS_STATIC` |
| 15 | Idempotent retry | Timeout test verifies same request ID and no blind replay | Desirable to observe once in controlled environment; not required to induce failure in live pilot | `PASS_NON_GUI` |
| 16 | Complete receipt chain reconstructible | Full fake-chain creates Inspection → Changeset → Approval → Change → Verification → Verified Copy chain | Must retain equivalent live bundle | `PENDING_LIVE` |
| 17 | OpenCADStudio adapter replaceable without changing CEW invariants | `CADAdapter` contract test keeps downstream code independent of OCS types | Not engine-dependent | `PASS_STATIC` |

## 4. Additional v0.1 safety constraints verified non-GUI

The current implementation also enforces:

- only `02_working/` is mutable;
- source/baseline/issued zones cannot be mutation targets;
- path traversal, absolute path injection, case/Unicode aliases and symlink escape are rejected;
- verified outputs are server-generated and collision/no-overwrite protected;
- one primary mutation maximum per Changeset;
- the only v0.1 creation target is layer `CEW-LAB`;
- model-provided raw CAD command strings are not accepted;
- the OpenCADStudio adapter compiles a numeric polyline internally;
- the model cannot choose verified output paths;
- approval is short-lived and single-use;
- a CAD session replacement invalidates an existing Changeset/approval context;
- `NEW:Polyline` is resolved only after execution to the concrete changed entity;
- `execute` in the live pilot runner requires the explicit operator phrase `CEW-LAB-ONLY`;
- local pilot evidence is written only under `target/cew-cad-01/<timestamp>/`, which is excluded from Git.

## 5. Live pilot gate

The live pilot may run only according to `docs/cew-cad/CEW_CAD_01_LIVE_PILOT_RUNBOOK.md` and only on a disposable laboratory DWG.

Required sequence:

1. independent hashes of OpenCADStudio executable and lab DWG;
2. `prepare` phase: status + audit + capture + governed Changeset, no mutation;
3. human review of the exact Changeset;
4. external Ed25519 approval using a private key outside the agent process;
5. `execute` with explicit `CEW-LAB-ONLY` confirmation;
6. one CEW-LAB polyline mutation;
7. kernel verification + unrelated-change guard + capture/diff + audit;
8. `save_verified` to a new governed path;
9. original lab SHA-256 reconfirmed unchanged;
10. evidence bundle retained and toolchain identities frozen.

Any failure keeps the overall result `NOT QUALIFIED`.

## 6. Toolchain record

`CEW_CAD_TOOLCHAIN_v1.json` must **not** be populated speculatively. It will be created only from live evidence and must include at least:

- exact repository commit SHA;
- Python version;
- MCP SDK and cryptography lock identities;
- OpenCADStudio executable absolute path and SHA-256;
- OpenCADStudio reported build/version;
- capability digest;
- target DWG/DXF format/version used in the pilot;
- disposable lab DWG input SHA-256;
- verified-copy SHA-256;
- receipt/evidence references.

## 7. Governance decision after pilot

Even if all 17 criteria pass, the pilot result alone does not authorize:

- promotion of OpenCADStudio from `BENCHMARK CANDIDATE` to `ADOPT`;
- mutating use on canonical N12 drawings;
- promotion of any verified copy to CEW baseline/issued;
- merge of PR #153;
- restart or closure of CEW-B01;
- structural/FEM decisions.

Those remain separate human governance decisions.
