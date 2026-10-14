# CEW Gate Authority G0 — Bootstrap Assurance Report v1

Status: **G0/A0 HUMAN-PROMOTED — TRUST ANCHOR RECORDED — PRODUCTION CONTROL PLANE NOT ACTIVATED**

This report records the completed non-self-validating bootstrap assurance and the explicit human promotion of Gate Core G0 and Frozen Authority A0. Promotion does **not** activate the production qualification workflow, authorize CEW-FEM-01, merge PR #148, or supersede PR #147.

## Promoted trust anchor

- Repository: `antoniocorsano-boop/N12`
- Bootstrap PR: `#148`
- Promoted exact G0 review commit: `1f32a24f456e7db18c994096e4c8f5067222a592`
- Gate Core version: `G0`
- G0 source-bundle SHA-256: `b56a98461373f59bc54ad3bd88d3047cff45a7f840b862248a99cd33ed3fe766`
- G0 manifest Git blob SHA: `318a38199e5d7643e654442b9d92cbf41c94dd7f`
- Authority ID: `N12_CEW_CONTRACT_01_A0`
- A0 Git blob SHA: `d6f71146b5b833650f1943021d956e1a2d742563`
- A0 SHA-256: `88ab731c986cef0af474bf567a9bb19a12a43dcdbef2de6cb211107b17f92dbb`
- Operational Authority O: `d806dcca72779b5a186defe557a7a9b739575a90`
- Promotion record: `governance/cew-gate-authority/G0_PROMOTION_RECORD_v1.json`
- Promotion-record creation commit: `fcfb4ada3a48197cd176062f538851bfd01abfb5`
- Bootstrap mode: `HUMAN_PROMOTION`

The promoted identity is the reviewed G0/A0 state at `1f32a24f456e7db18c994096e4c8f5067222a592`. The later promotion-record/report commits are governance evidence and do not modify the promoted Gate Core source bundle, A0, or its manifest.

## Final exact-head bootstrap certification

Run `38494988431` checked out exact commit `1f32a24f456e7db18c994096e4c8f5067222a592` and completed successfully.

Evidence:

- Task 2 identity/A0 tests: PASS
- Task 3 CandidateReader/path/object/resource tests: PASS
- Task 4 Operational Authority replay tests: PASS
- Task 5 I01–I17 qualification tests: PASS
- Task 6 event identity + no-exec integration tests: PASS
- Task 7 G0 manifest/toolchain identity tests: PASS
- Python compileall: PASS
- full `tests/cew_gate_authority` discovery suite: **251/251 PASS**
- Round-6 regressions: PASS
- actionlint `1.7.12`: PASS
- zizmor `1.30.1`: PASS, no findings; two deliberate offline-only suppressions
- CodeQL Python analysis: PASS

The no-exec integration proves that executable Python/shell, local actions, Git hooks, malicious package manifests, and modified candidate workflows in H are not executed while allowlisted candidate evidence remains readable as Git data.

## Final independent review

Fresh Codex review was requested only for exact head `1f32a24f456e7db18c994096e4c8f5067222a592` after Round-6 remediation and exact-head recertification.

Codex completed the review with: **“Didn't find any major issues.”**

- Review result comment: `6158870835`
- Reviewed commit prefix reported by Codex: `1f32a24f45`
- New inline findings after the review: none
- All prior inline review threads: resolved

The final reviewed threat boundary includes complete qualification-root enumeration, A0-bound Markdown SHA-256 identities, registration fixture identity binding, model-generation profile/builder identity binding, strict structured-document contracts, provenance checks, no-exec isolation, exact G0 source binding, and the CEW-FEM separation boundary.

## Round-6 remediation evidence

The previous independent review on exact head `3645d2201177b87bc185fd5dabdeea992e231f2b` found four valid P1 findings:

1. extra files could exist below the qualification root outside the A0 profile;
2. nonblank but contradictory Markdown could be treated as evidence;
3. registration `fixture_id` and `uncertainty_type` were not frozen to A0;
4. `generation_profile` and `builder.declared_builder` were not frozen to A0.

TDD evidence:

- RED exact head `8e8e291fa3c2c6efbf87596b53419f26388c19ec`, run `38494327168`: the new Round-6 regressions failed as intended;
- functional exact head `b458305fdf45f84dda704ed8e88916f95ef21f7b`, run `38494909318`: Tasks 2–6 PASS, with Task 7 alone rejecting the intentionally stale G0 source binding;
- final manifest-bound exact head `1f32a24f456e7db18c994096e4c8f5067222a592`, run `38494988431`: complete PASS, 251/251 tests.

The remediation closed the candidate qualification surface, bound mandatory Markdown bytes through SHA-256 identities, and froze the missing registration/model-generation semantic identities in A0.

## Trusted candidate language and authority boundary

A0/G0 enforce a finite fail-closed candidate language before I01–I17. The complete `qualification/cew-contract-01/n12/` tree at H must equal the exact A0 allowlist before the candidate bundle is accepted.

Structured candidate documents remain governed by closed JSON/CSV contracts, strict JSON decoding, duplicate-key rejection, exact schema identity and exact types, finite-number checks, bounded JSON depth, exact CSV structure, evidence bindings, provenance bindings, recursive authority-boundary protection, and deterministic O-only replay.

A0 keeps every solver/result authority flag false:

- `solver_authorized=false`
- `calculation_model_ready=false`
- `synthetic_solver_result=false`
- `solver_run=false`
- `result_entity_created=false`
- `CEW_FEM_01_REQUIRED=true`

Therefore the G0/A0 promotion does not authorize solver selection, structural analysis, `SolverRun`, `Result`, new engineering assumptions, or any CEW-FEM-01 implementation.

## Human promotion decision

The human promotion gate required by the approved design and Task 8 was explicitly approved on 14 October 2026.

The durable decision is recorded in `G0_PROMOTION_RECORD_v1.json` with:

- `bootstrap_mode=HUMAN_PROMOTION`;
- `decision=PROMOTED`;
- the exact reviewed G0 commit;
- G0 source-bundle SHA-256;
- A0 Git blob SHA and SHA-256;
- exact bootstrap run and independent-review references;
- the unchanged CEW-FEM authority boundary;
- explicit non-authorization of production activation, Ready transition, merge, auto-merge, and #147 supersession by the promotion record itself.

Bootstrap promotion result: **PASS — G0/A0 ARE NOW DURABLE BOOTSTRAP TRUST ANCHORS.**

## Residual / next-stage controls

The following remain deliberately outside Task 8 and are not silently inferred from this promotion:

1. `PREFERRED_TRIGGER=workflow_dispatch` remains the conservative choice until repository Actions Policy for `pull_request_target` is explicitly verified.
2. Artifact Attestation availability/policy is not yet verified and no attestation claim is made.
3. No production `.github/workflows/cew-gate-authority.yml` workflow is active yet.
4. Repository governance/ruleset activation is still a later human/admin gate.
5. PR #147 remains frozen/read-only and is not superseded.
6. PR #148 is not merged by this Task-8 promotion.

## Next canonical step

Proceed to **Task 9 — Trusted qualification workflow pinned to promoted G0/A0** only as a separate implementation step. Task 9 must consume the promoted identities above, add receipt-handoff tests RED→GREEN, preserve least privilege, and must not reinterpret the human promotion record.
