# CEW Gate Authority G0 — Bootstrap Assurance Report v1

Status: **CANDIDATE_ASSURANCE_PASS — FRESH INDEPENDENT REVIEW REQUIRED**

This report records bootstrap assurance evidence only. It does **not** promote G0/A0 and it does not activate the production qualification control plane.

## Exact candidate under assurance

- Repository: `antoniocorsano-boop/N12`
- PR: `#148`
- Exact assurance head before this report-only commit: `32e98d7d2524de67630c6daf024b93855c1c9f3c`
- Base: `main`
- Operational Authority O: `d806dcca72779b5a186defe557a7a9b739575a90`
- Bootstrap workflow run: `38438719235`
- Bootstrap workflow conclusion: `success`

The exact final review head is the commit containing this report. It must be freshly recertified before a new independent review is accepted.

## G0 / A0 identities

- Gate Core version: `G0`
- G0 source-bundle SHA-256: `6f0e1fce7eeba832d565983b3ef83ba35fdb20cb905e187c595b2015fcabc5f6`
- G0 manifest Git blob SHA: `6019e40cdd86807cc012f85ba638a4acf98a5a66`
- A0 authority ID: `N12_CEW_CONTRACT_01_A0`
- A0 Git blob SHA: `42fc0e1c764d080427b5f60469d466031a2a4717`
- Qualification Receipt schema Git blob SHA: `cf7a7809dd67338a47e2fa57ce365479cc67960e`
- G0 manifest promotion state: `CANDIDATE`
- Commit binding: `HUMAN_PROMOTION_RECORD_REQUIRED`

The G0 manifest binds exactly 13 source/authority/schema blobs. The candidate workflow is not part of the Gate Core source bundle and cannot self-promote G0.

## Trusted document-contract layer

A0 now defines the complete structured candidate surface before invariant evaluation:

- five JSON contracts:
  - `qualification.json`;
  - `evidence-index.json`;
  - `registration-uncertainty.json`;
  - `model-generation.json`;
  - `model-generation-receipt.json`;
- two CSV contracts:
  - `conformance-matrix.csv`;
  - `structural-type-minimality.csv`.

For every JSON contract A0 freezes the exact root field set and supported schema identity/version. For every CSV contract A0 freezes the exact header. The authority file itself is also treated as a closed schema by the trusted loader.

A0 additionally freezes:

- source repository: `antoniocorsano-boop/N12`;
- canonical `C01-T01..C01-T11 → evidence path` bindings;
- all five authority-boundary flags as explicit `false`.

G0 validates the document-contract layer before evaluating I01–I17. Unsupported schema/version, unexpected root fields and incompatible CSV headers therefore fail closed before semantic interpretation.

## Independent-review remediation evidence

### First independent review

The review on `7aaf74f6491679d3d4aadac49607cdd1f7964e89` found two valid P1 semantic blockers:

1. unsupported `qualification.json` schema ID/version could be interpreted under v1 semantics;
2. I15 accepted arbitrary non-empty allowlisted paths rather than a trusted test-to-evidence mapping.

Those findings were remediated and recertified on `0dfb957218813eb404516afda46400220eae72f9`.

### Second independent review

The fresh review on `0dfb957218813eb404516afda46400220eae72f9` found three additional valid P1 semantic-contract blockers:

1. authority-boundary claims could be introduced in other structured JSON locations and ignored;
2. `model-generation-receipt.json` provenance did not bind `source_repository` and `builder_path` to A0;
3. remaining JSON documents could declare unsupported/future schema versions while being interpreted with current semantics.

Rather than patching the three examples individually, remediation generalized the trusted contract layer across every structured candidate document. CSV headers were also frozen to prevent the same class of schema drift in tabular payloads.

TDD evidence for this systematic remediation:

- RED exact head: `3e90d844167edf5d3f288d2df6831d46400ab2d3`
- RED run: `38438044820`
- Tasks 2–7 remained PASS; CodeQL PASS; full discovery suite failed **10 targeted regressions** and no prior tests regressed.
- GREEN exact code/authority head: `32e98d7d2524de67630c6daf024b93855c1c9f3c`
- GREEN run: `38438719235` = success.

The new regressions prove fail-closed behavior for:

- unsupported schema versions in registration, model-generation, model-generation-receipt and evidence-index;
- unexpected root fields in structured JSON;
- receipt `source_repository` substitution;
- receipt `builder_path` substitution;
- authority-boundary `true` claims nested anywhere in the structured JSON set;
- invalid conformance-matrix CSV header;
- invalid structural-minimality CSV header.

## Test and replay evidence

Run `38438719235` on exact head `32e98d7d2524de67630c6daf024b93855c1c9f3c`:

- Task 2 identity/A0 tests: PASS
- Task 3 CandidateReader/path/object/resource tests: PASS
- Task 4 Operational Authority replay tests: PASS
- Task 5 I01–I17 qualification tests: PASS
- Task 6 event identity + no-exec end-to-end tests: PASS
- Task 7 G0 manifest/toolchain identity tests: PASS
- Python compileall: PASS
- full `tests/cew_gate_authority` discovery suite: **103/103 PASS**
- actionlint `1.7.12`: PASS
- zizmor `1.30.1`: PASS, no findings; two offline-only audits suppressed as previously classified
- CodeQL Python analysis: PASS

The no-exec integration suite includes executable Python/shell, local action, Git hook, malicious package manifest and modified candidate workflow tripwires; none are executed while allowlisted candidate evidence remains readable as Git data.

The replay remains bound exclusively to O and reproduces the historical output:

- identity: `N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json`
- SHA-256: `4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`
- size: `1068121` bytes
- `generated_at`: `2026-08-26T09:54:00.472520+00:00`

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

### zizmor offline-mode classification

The two suppressed checks remain `NON_BLOCKING_BOOTSTRAP_LIMITATION`, not silently treated as executed. The bootstrap intentionally does not grant zizmor an online token. Supply-chain identity remains constrained by full GitHub Action commit SHAs and verified release-asset digests, with CodeQL independent.

## Threat-model coverage reached

Fresh bootstrap evidence demonstrates:

- exact candidate SHA binding;
- branch-move/force-push resistance after H capture;
- regular-blob-only candidate inputs;
- fail-closed handling of path confusion, Unicode collision, symlink, gitlink and resource abuse;
- no candidate checkout/import/execution in Gate Core;
- B/G/A/H/O Receipt binding;
- exact A0-approved structured-document contracts before semantic evaluation;
- exact A0-approved test-to-evidence bindings;
- receipt provenance bound to A0 repository/builder identity;
- authority-boundary claims scanned recursively across all structured JSON inputs;
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

Any code or authority change invalidates the current review/evidence head and requires fresh bootstrap assurance. A documentation-only assurance update still changes the PR exact head and therefore requires the final head to be recertified before review.
