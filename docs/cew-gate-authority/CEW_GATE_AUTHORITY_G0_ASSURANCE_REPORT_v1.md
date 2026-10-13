# CEW Gate Authority G0 — Bootstrap Assurance Report v1

Status: **CANDIDATE_ASSURANCE_PASS — FRESH INDEPENDENT REVIEW REQUIRED**

This report records bootstrap assurance evidence only. It does **not** promote G0/A0 and it does not activate the production qualification control plane.

## Exact candidate under assurance

- Repository: `antoniocorsano-boop/N12`
- PR: `#148`
- Exact assurance head before this report-only commit: `54f55156b9d5cd2c8a3c9d01c0193c0f0926d8c5`
- Base: `main`
- Operational Authority O: `d806dcca72779b5a186defe557a7a9b739575a90`
- Bootstrap workflow run: `38442451686`
- Bootstrap workflow conclusion: `success`

The exact final review head is the commit containing this report. It must be freshly recertified before a new independent review is accepted.

## G0 / A0 identities

- Gate Core version: `G0`
- G0 source-bundle SHA-256: `1103c1755db135c9a3b6ea59ec41cd573c98d5bee3e32866083783c68abba027`
- G0 manifest Git blob SHA: `5c04c75ab35c391af3c693b322f9e01dc94cb94d`
- A0 authority ID: `N12_CEW_CONTRACT_01_A0`
- A0 Git blob SHA: `42fc0e1c764d080427b5f60469d466031a2a4717`
- Qualification Receipt schema Git blob SHA: `cf7a7809dd67338a47e2fa57ce365479cc67960e`
- G0 manifest promotion state: `CANDIDATE`
- Commit binding: `HUMAN_PROMOTION_RECORD_REQUIRED`

The G0 manifest binds exactly 13 source/authority/schema blobs. The candidate workflow is not part of the Gate Core source bundle and cannot self-promote G0.

## Trusted document-contract layer

A0 defines the complete structured candidate surface before invariant evaluation:

- five JSON contracts: `qualification.json`, `evidence-index.json`, `registration-uncertainty.json`, `model-generation.json`, `model-generation-receipt.json`;
- two CSV contracts: `conformance-matrix.csv`, `structural-type-minimality.csv`.

For every JSON contract A0 freezes the exact root field set and supported schema identity/version. For every CSV contract A0 freezes the exact header. A0 also freezes the source repository, canonical `C01-T01..C01-T11 → evidence path` bindings and all five authority-boundary flags as explicit `false`.

G0 validates the document-contract layer before evaluating I01–I17. JSON decoding is also strict: duplicate object keys are rejected before document-contract or invariant evaluation, including nested objects and duplicates whose final value would otherwise look valid.

## Independent-review remediation evidence

### First independent review

The review on `7aaf74f6491679d3d4aadac49607cdd1f7964e89` found two valid P1 semantic blockers: unsupported qualification schema identity/version and untrusted test-to-evidence binding. Those findings were remediated and recertified on `0dfb957218813eb404516afda46400220eae72f9`.

### Second independent review

The fresh review on `0dfb957218813eb404516afda46400220eae72f9` found three valid semantic-contract blockers: incomplete global authority-boundary rejection, incomplete model-generation receipt provenance binding, and unsupported/future schema identities for remaining structured JSON documents. Remediation generalized the trusted contract layer across every structured candidate document and froze CSV headers.

TDD evidence:

- RED `3e90d844167edf5d3f288d2df6831d46400ab2d3`, run `38438044820`: 10 targeted document-contract regressions failed with prior tests green;
- GREEN `32e98d7d2524de67630c6daf024b93855c1c9f3c`, run `38438719235`: complete success;
- final reviewed head `b1fcbd1ba5672130762a5b52f84735a78882f9fe`, run `38438968600`: complete success.

### Third independent review — JSON ambiguity

The fresh review on exact head `b1fcbd1ba5672130762a5b52f84735a78882f9fe` found one valid P1: Python `json.loads()` accepted duplicate object keys, so a candidate could state a non-authorized value first and a permitted value second; the first claim disappeared before I16/document-contract evaluation.

This was remediated as a JSON-decoding rule rather than a field-specific patch. G0 now uses a strict `object_pairs_hook` for every candidate JSON object and raises `CANDIDATE_JSON_DUPLICATE_KEY` on any duplicate key before semantic interpretation.

TDD evidence:

- RED exact head: `b92a37fd47272869c7fcc7bc5c6259f95bc47a5e`
- RED run: `38442107706`
- Tasks 2–7 preceding full discovery remained PASS; full suite ran **107 tests** and failed exactly **4 duplicate-key regressions**.
- GREEN decoder head: `f3aeb911fc0abdcfd277e7e0284df71c0aa0e10e`; Task 7 correctly detected the stale G0 manifest after the Gate Core blob changed.
- GREEN manifest-bound head: `54f55156b9d5cd2c8a3c9d01c0193c0f0926d8c5`
- GREEN run: `38442451686` = success.

The four new regressions prove fail-closed behavior for:

- authority-boundary duplicate `true` followed by `false`;
- duplicate schema version whose final value is supported;
- duplicate provenance whose final value is trusted;
- a semantically innocuous duplicate key with identical values.

Therefore duplicate-key rejection is a generic JSON-language constraint, not a special-case authority check.

## Test and replay evidence

Run `38442451686` on exact head `54f55156b9d5cd2c8a3c9d01c0193c0f0926d8c5`:

- Task 2 identity/A0 tests: PASS
- Task 3 CandidateReader/path/object/resource tests: PASS
- Task 4 Operational Authority replay tests: PASS
- Task 5 I01–I17 qualification tests: PASS
- Task 6 event identity + no-exec end-to-end tests: PASS
- Task 7 G0 manifest/toolchain identity tests: PASS
- Python compileall: PASS
- full `tests/cew_gate_authority` discovery suite: **107/107 PASS**
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

- GitHub hosted runner: `ubuntu-24.04`
- Python: `3.12`
- `actions/checkout@11d5960a326750d5838078e36cf38b85af677262`
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`
- `github/codeql-action@24c54180a607b1449ed407dd24f251e4e9147c8d`
- actionlint `1.7.12`, SHA-256 `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8`
- zizmor `1.30.1`, SHA-256 `e65324f4430c2717591937edcec90ccbefaf14c174f8ec9415e03ca875b46e1a`

The two zizmor checks suppressed by `--offline` remain `NON_BLOCKING_BOOTSTRAP_LIMITATION`; they are not represented as executed.

## Threat-model coverage reached

Fresh bootstrap evidence demonstrates exact H binding, branch-move resistance, regular-blob-only candidate inputs, resource/path/symlink/gitlink protections, no candidate execution, B/G/A/H/O receipt binding, closed structured-document contracts, strict duplicate-key JSON decoding, exact evidence binding, receipt provenance binding, recursive authority-boundary protection, deterministic O-only replay, I01–I17 positive/negative coverage, and immutable bootstrap tool identities.

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
