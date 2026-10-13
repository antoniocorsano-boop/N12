# CEW Gate Authority G0 — Bootstrap Assurance Report v1

Status: **CANDIDATE_ASSURANCE_PASS — HUMAN_PROMOTION_REQUIRED**

This report records bootstrap assurance evidence only. It does **not** promote G0/A0 and it does not activate the production qualification control plane.

## Exact candidate under assurance

- Repository: `antoniocorsano-boop/N12`
- PR: `#148`
- Exact assurance head: `b4b80287612a50f97a8ac7961d18473d7fc22796`
- Base: `main`
- Operational Authority O: `d806dcca72779b5a186defe557a7a9b739575a90`
- Bootstrap workflow run: `38428548280`
- Bootstrap workflow conclusion: `success`

## G0 / A0 identities

- Gate Core version: `G0`
- G0 source-bundle SHA-256: `6838d751310cc90555b11867a898b541c789597cd70c692e10bdc640ae39dee3`
- G0 manifest Git blob SHA: `f3dcaedfbfefbd7db52405ca1413dacc9c7ebbae`
- A0 authority ID: `N12_CEW_CONTRACT_01_A0`
- A0 Git blob SHA: `413202117ada754b25f5d700953e79e0b46b0d33`
- Qualification Receipt schema Git blob SHA: `cf7a7809dd67338a47e2fa57ce365479cc67960e`
- G0 manifest promotion state: `CANDIDATE`
- Commit binding: `HUMAN_PROMOTION_RECORD_REQUIRED`

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

- actionlint `1.7.12`
  - asset: `actionlint_1.7.12_linux_amd64.tar.gz`
  - SHA-256: `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8`
  - release/digest independently verified before bootstrap execution
- zizmor `1.30.1`
  - asset: `zizmor-x86_64-unknown-linux-gnu.tar.gz`
  - SHA-256: `e65324f4430c2717591937edcec90ccbefaf14c174f8ec9415e03ca875b46e1a`
  - immutable GitHub release/digest independently verified before bootstrap execution
- CodeQL action commit `24c54180a607b1449ed407dd24f251e4e9147c8d`
  - GitHub commit signature verified by GitHub

## Test and replay evidence

Run `38428548280` on exact head `b4b80287612a50f97a8ac7961d18473d7fc22796`:

- Task 2 identity/A0 tests: PASS
- Task 3 CandidateReader/path/object/resource tests: PASS
- Task 4 Operational Authority replay tests: PASS
- Task 5 I01–I17 qualification tests: PASS
- Task 6 event identity + no-exec end-to-end tests: PASS
- Task 7 G0 manifest/toolchain identity tests: PASS
- Python compileall: PASS
- full `tests/cew_gate_authority` discovery suite: **47/47 PASS**

The no-exec integration suite includes executable Python/shell, local action, Git hook, malicious package manifest and modified candidate workflow tripwires; none are executed while allowlisted candidate evidence remains readable as Git data.

The replay remains bound exclusively to O and reproduces the historical output:

- identity: `N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json`
- SHA-256: `4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`
- size: `1068121` bytes
- `generated_at`: `2026-08-26T09:54:00.472520+00:00`

## Analyzer evidence

- actionlint `1.7.12`: **PASS**, no reported finding on the bootstrap workflow.
- zizmor `1.30.1`: **PASS**, `No findings to report. Good job!`; two audits were suppressed by deliberate `--offline` execution.
- CodeQL Python analysis: **PASS** on the same exact head.

### zizmor offline-mode classification

The two suppressed checks are recorded as `NON_BLOCKING_BOOTSTRAP_LIMITATION`, not silently treated as executed. The bootstrap intentionally does not grant zizmor an online token. Supply-chain identity is instead independently constrained by full GitHub Action commit SHAs and verified release-asset digests, and CodeQL runs independently. Independent review must still examine supply-chain pins explicitly.

## Threat-model coverage reached

Fresh bootstrap evidence demonstrates:

- exact candidate SHA binding;
- branch-move/force-push resistance after H capture;
- regular-blob-only candidate inputs;
- fail-closed handling of path confusion, Unicode collision, symlink, gitlink and resource abuse;
- no candidate checkout/import/execution in Gate Core;
- B/G/A/H/O Receipt binding;
- A0 authority boundary with all solver/result flags false;
- deterministic replay independent of candidate copies of operational paths;
- I01–I17 positive/negative coverage;
- immutable bootstrap action/tool identities.

## Residual / human-controlled items

The following are **not** defects in G0 but remain mandatory before operational activation:

1. `PREFERRED_TRIGGER=workflow_dispatch` remains the conservative deployment choice until repository Actions Policy for `pull_request_target` is explicitly verified in Settings.
2. Artifact Attestation availability and repository policy remain deployment-time checks; no attestation claim is made by this bootstrap report.
3. G0/A0 are not trusted anchors until fresh independent review and explicit human promotion.
4. No production `cew-gate-authority.yml` workflow is activated yet.
5. PR #147 remains frozen/read-only and is not superseded yet.

## Promotion readiness decision

Bootstrap assurance result: **READY_FOR_INDEPENDENT_REVIEW**.

Promotion result: **NOT YET AUTHORIZED**.

The next canonical step is Task 8: fresh independent review on the final exact G0/A0 candidate head. Any code change after review begins invalidates the review/evidence head and requires fresh Task 7 evidence.
