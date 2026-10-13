# CEW Gate Authority G0 — Bootstrap Assurance Report v1

Status: **CANDIDATE_ASSURANCE_PASS — FRESH INDEPENDENT REVIEW REQUIRED**

This report records bootstrap assurance evidence only. It does **not** promote G0/A0 and it does not activate the production qualification control plane.

## Exact candidate under assurance

- Repository: `antoniocorsano-boop/N12`
- PR: `#148`
- Exact assurance head before this report-only commit: `53f36da7e17bc8f6aa9d52e1e932e5e04c4cf6bd`
- Base: `main`
- Operational Authority O: `d806dcca72779b5a186defe557a7a9b739575a90`
- Bootstrap workflow run: `38431888985`
- Bootstrap workflow conclusion: `success`

The exact final review head is the commit containing this report. It must be freshly recertified before a new independent review is accepted.

## G0 / A0 identities

- Gate Core version: `G0`
- G0 source-bundle SHA-256: `20f393a1985f895b76bd803524f11e21d40b61d0c0b1cb01940f7ee24c3d94bd`
- G0 manifest Git blob SHA: `77d7bf0562bdeb048584118ff8a57e252de98b56`
- A0 authority ID: `N12_CEW_CONTRACT_01_A0`
- A0 Git blob SHA: `a80944e3726ca82ac881e9583542db66e36c32e9`
- Qualification Receipt schema Git blob SHA: `cf7a7809dd67338a47e2fa57ce365479cc67960e`
- G0 manifest promotion state: `CANDIDATE`
- Commit binding: `HUMAN_PROMOTION_RECORD_REQUIRED`

A0 now also freezes two semantic contracts required by the independent review:

- supported qualification schema: `CEW_CONTRACT_01_QUALIFICATION` version `1`;
- canonical `C01-T01..C01-T11 → evidence path` bindings.

The G0 manifest binds exactly 13 source/authority/schema blobs. The candidate workflow is not part of the Gate Core source bundle and cannot self-promote G0.

## Trusted toolchain evidence

Runner and runtime:

- GitHub hosted runner: `ubuntu-24.04`
- Python: `3.12`

Pinned GitHub Actions:

- `actions/checkout@11d5960a326750d5838078e36cf38b85af677262`
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`
- `github/codeql-action@24c54180a607b1449ed407dd24f251e4e9147c8d`

External analyzers:

- actionlint `1.7.12`, SHA-256 `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8`
- zizmor `1.30.1`, SHA-256 `e65324f4430c2717591937edcec90ccbefaf14c174f8ec9415e03ca875b46e1a`
- CodeQL action commit `24c54180a607b1449ed407dd24f251e4e9147c8d`

## Independent-review remediation evidence

The first independent review on `7aaf74f6491679d3d4aadac49607cdd1f7964e89` found two valid P1 semantic blockers:

1. unsupported `qualification.json` schema ID/version could still be interpreted under v1 semantics;
2. I15 accepted arbitrary non-empty allowlisted paths rather than a trusted test-to-evidence mapping.

TDD remediation:

- RED exact head: `dcbbb55d4cb8e0ecf9309e97c7d303f025f12307`
- RED run: `38431404909`; Tasks 2–7 remained PASS and the full discovery suite failed on the new semantic regressions.
- GREEN exact code/authority head: `53f36da7e17bc8f6aa9d52e1e932e5e04c4cf6bd`
- GREEN run: `38431888985` = success.

New regressions prove fail-closed behavior for:

- unapproved qualification schema ID;
- future qualification schema version;
- an allowlisted but incorrect evidence path;
- reuse of a single valid evidence file for all eleven tests.

## Test and replay evidence

Run `38431888985` on exact head `53f36da7e17bc8f6aa9d52e1e932e5e04c4cf6bd`:

- Task 2 identity/A0 tests: PASS
- Task 3 CandidateReader/path/object/resource tests: PASS
- Task 4 Operational Authority replay tests: PASS
- Task 5 I01–I17 qualification tests: PASS
- Task 6 event identity + no-exec end-to-end tests: PASS
- Task 7 G0 manifest/toolchain identity tests: PASS
- Python compileall: PASS
- full `tests/cew_gate_authority` discovery suite: **93/93 PASS**
- four independent-review semantic regressions: PASS

The no-exec integration suite includes executable Python/shell, local action, Git hook, malicious package manifest and modified candidate workflow tripwires; none are executed while allowlisted candidate evidence remains readable as Git data.

The replay remains bound exclusively to O and reproduces the historical output:

- identity: `N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json`
- SHA-256: `4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`
- size: `1068121` bytes
- `generated_at`: `2026-08-26T09:54:00.472520+00:00`

## Analyzer evidence

- actionlint `1.7.12`: **PASS**.
- zizmor `1.30.1`: **PASS**, no findings; two audits remain deliberately suppressed by `--offline`.
- CodeQL Python analysis: **PASS** on the same GREEN code/authority head.

### zizmor offline-mode classification

The two suppressed checks are `NON_BLOCKING_BOOTSTRAP_LIMITATION`, not silently treated as executed. The bootstrap intentionally does not grant zizmor an online token. Supply-chain identity remains constrained by full GitHub Action commit SHAs and verified release-asset digests, with CodeQL independent.

## Threat-model coverage reached

Fresh bootstrap evidence demonstrates:

- exact candidate SHA binding;
- branch-move/force-push resistance after H capture;
- regular-blob-only candidate inputs;
- fail-closed handling of path confusion, Unicode collision, symlink, gitlink and resource abuse;
- no candidate checkout/import/execution in Gate Core;
- B/G/A/H/O Receipt binding;
- exact A0-approved qualification schema identity/version;
- exact A0-approved test-to-evidence bindings;
- A0 authority boundary with all solver/result flags false;
- deterministic replay independent of candidate copies of operational paths;
- I01–I17 positive/negative coverage;
- immutable bootstrap action/tool identities.

## Residual / human-controlled items

The following remain mandatory before operational activation:

1. `PREFERRED_TRIGGER=workflow_dispatch` remains the conservative deployment choice until repository Actions Policy for `pull_request_target` is explicitly verified in Settings.
2. Artifact Attestation availability and repository policy remain deployment-time checks; no attestation claim is made by this bootstrap report.
3. G0/A0 are not trusted anchors until a fresh independent review of the final exact head and explicit human promotion.
4. No production `cew-gate-authority.yml` workflow is activated yet.
5. PR #147 remains frozen/read-only and is not superseded yet.

## Promotion readiness decision

Bootstrap assurance result: **READY_FOR_FRESH_INDEPENDENT_REVIEW_AFTER_FINAL_HEAD_RECERTIFICATION**.

Promotion result: **NOT YET AUTHORIZED**.

Any code or authority change invalidates the current review/evidence head and requires fresh Task 7 evidence. A documentation-only assurance update still changes the PR exact head and therefore requires the final head to be recertified before review.
