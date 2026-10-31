# CEW-COL-03C — Governed Cross-Document Source Materialization — Implementation Plan

> **Spec:** `docs/superpowers/specs/2026-10-31-cew-col03c-governed-cross-document-materialization-design.md`

## Goal

Build a deterministic, fail-closed COL-03C gate that reconstructs the exact TAV.7 documentary source, classifies historical derived artifacts by real materialization state, audits recoverable derived references, and emits cross-document evidence state for exactly the 22 qualified `COL-OCC-*` subjects without promoting structural identity.

## Exact bases

- qualified COL-03B predecessor: `cfd9382b703d0a974daf63c23dc2b6d3d81eadad`
- frozen archive source commit: `78c20a52db4f391ce0d13b9705b9f04737e218c9`
- historical registration commit: `643dc8934ec0c8ac37613ec2880cf9e02f5a9df2`
- TAV.7 path: `archive/documentazione_originaria/tavola7.pdf`
- TAV.7 SHA-256: `38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b`
- TAV.7 repository blob: `bf92501e723843fd912976b1b711285a61c548d3`
- TAV.7 repository size: `798816` bytes

## Global constraints

1. Work only on a successor branch whose merge-base is exact COL-03B head `cfd9382b…`.
2. TDD is mandatory: every production behavior begins with a causal RED.
3. The 22 `COL-OCC-*` subjects are immutable.
4. No new column detector, no re-opening COL-02 graphical coverage, no mutation of COL-03A/COL-03B governed evidence.
5. TAV.7 PDF is primary source authority; derivative rasters/text are evidence only.
6. Historical DXF/CSV inventory entries are not usable row-level evidence until exact bytes/provenance are recovered.
7. Canonical/derived CSVs from the frozen archive commit are reference evidence only.
8. A source not materialized is never represented as inspected `NO_EVIDENCE`.
9. No support number, family, section, fixed line, vertical chain, canonical node or structural identity assignment.
10. No G2C/G3 promotion, EdiLus export, merge or deploy.

## Planned package

```text
experiments/cew_col03c/
  __init__.py
  predecessor.py
  historical_inventory.py
  source_materialization.py
  derived_reference_quality.py
  tav07_observations.py
  cross_document.py
  exact_source.py

tests/cew_col03c/
  test_predecessor.py
  test_historical_inventory.py
  test_source_materialization.py
  test_derived_reference_quality.py
  test_tav07_observations.py
  test_cross_document.py
  test_exact_source_writer.py

.github/workflows/
  validate-cew-col03c-governed-cross-document-materialization.yml
```

## Planned evidence surface

Only:

`evidence/cew-col03c/`

with exactly:

1. `source-materialization-manifest.json`
2. `derived-reference-quality.json`
3. `cross-document-evidence-ledger.json`
4. `cross-document-reconciliation.json`
5. `cross-document-evidence-closure.json`

---

## Task 1 — Freeze predecessor and historical inventory semantics

### Files

Create:

- `experiments/cew_col03c/__init__.py`
- `experiments/cew_col03c/predecessor.py`
- `experiments/cew_col03c/historical_inventory.py`
- `tests/cew_col03c/test_predecessor.py`
- `tests/cew_col03c/test_historical_inventory.py`

### RED

Write tests first for:

1. exact predecessor SHA must equal `cfd9382b…`;
2. predecessor ledger must contain exactly `COL-OCC-0001` … `COL-OCC-0022`;
3. COL-03B must remain identity-unresolved and all authority closed;
4. predecessor must preserve the historical materialization gap semantics introduced by COL-03B;
5. historical registration snapshot can establish that an artifact is known but cannot establish that its bytes are available;
6. inventory entries without exact bytes resolve to `KNOWN_INVENTORY_NOT_MATERIALIZED`;
7. row-level use of an inventory-only artifact raises/fails closed.

Run the focused tests and acquire causal failures because the modules/functions do not yet exist.

### GREEN interfaces

```python
QUALIFIED_COL03B_SHA = "cfd9382b703d0a974daf63c23dc2b6d3d81eadad"

validate_col03b_predecessor(
    *,
    ledger: dict,
    reconciliation: dict,
    closure: dict,
    expected_sha: str,
) -> list[dict]

parse_historical_inventory(text: str, *, source_ref: str) -> list[dict]

classify_historical_artifact(
    record: dict,
    *,
    materialized_path: str | None,
    sha256: str | None,
) -> dict
```

Normalized historical record fields include:

- `artifact_name`
- `inventory_source_ref`
- `historical_package_refs`
- `materialization_state`
- `bytes_available`
- `row_level_evidence_usable`
- `authority = REFERENCE_ONLY`

### Completion

Run all COL-03C Task 1 tests plus COL-03B regression tests.

Commit:

`feat: freeze COL-03C predecessor and inventory boundary`

---

## Task 2 — Exact TAV.7 source contract and deterministic materialization

### Files

Create/modify:

- `experiments/cew_col03c/source_materialization.py`
- `tests/cew_col03c/test_source_materialization.py`

### RED

Write tests requiring:

1. exact archive commit/path/SHA/size constants;
2. a materialized TAV.7 with wrong SHA fails `PROVENANCE_MISMATCH`;
3. wrong archive commit/path fails closed;
4. valid bytes become `MATERIALIZED_VERIFIED`;
5. source contract keeps primary PDF authority separate from raster/text derivatives;
6. repeated page/raster metadata are canonically identical;
7. zero-page/unreadable PDF cannot qualify.

### GREEN interfaces

```python
TAV07_SOURCE = {
    "catalogue_id": "TAV-07A",
    "archive_commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "path": "archive/documentazione_originaria/tavola7.pdf",
    "sha256": "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b",
    "repository_blob": "bf92501e723843fd912976b1b711285a61c548d3",
    "size_bytes": 798816,
    "class": "particolari_strutturali",
    "state": "DOC",
}

verify_materialized_source(path: Path, contract: dict) -> dict

build_pdf_source_metadata(path: Path, contract: dict) -> dict

canonical_source_digest(metadata: dict) -> str
```

The metadata must include page count and deterministic page geometry/raster descriptors but MUST keep the PDF as authority.

### Completion

Focused RED→GREEN, then all COL-03C tests accumulated so far.

Commit:

`feat: verify exact TAV07 documentary source`

---

## Task 3 — Materialize and audit derived reference datasets

### Files

Create/modify:

- `experiments/cew_col03c/derived_reference_quality.py`
- `tests/cew_col03c/test_derived_reference_quality.py`

### Inputs from frozen archive commit

At minimum:

- `data/canonical/tav5_topology_nodes_57.csv`
- `data/canonical/tav5_topology_connections_v07.csv`
- `data/canonical/telaio5_tav5_candidate_matrix_v1.csv`

### RED

Tests must establish:

1. exact bytes/digest provenance is required for a derived reference;
2. the node table declares exactly the IDs it actually contains;
3. connection endpoints are compared against the materialized node universe;
4. any unknown endpoint produces `DATA_QUALITY_BLOCKED` for topology identity use;
5. unknown nodes are never synthesized;
6. connection row count is reported from bytes, not copied from historical inventory prose;
7. inventory claims and derived dataset facts remain separate fields;
8. row-order perturbation yields the same canonical quality digest.

### GREEN interfaces

```python
materialize_reference_descriptor(
    *,
    path: str,
    archive_commit: str,
    bytes_sha256: str,
    rows: list[dict],
) -> dict

audit_topology_reference(
    *,
    nodes: list[dict],
    connections: list[dict],
    provenance: dict,
) -> dict

audit_candidate_matrix_reference(
    *,
    rows: list[dict],
    provenance: dict,
) -> dict
```

Required topology output includes:

- node row count;
- connection row count;
- declared node IDs;
- referenced endpoint IDs;
- unresolved endpoint IDs;
- `identity_use_state`;
- `DATA_QUALITY_BLOCKED` when unresolved endpoints exist.

### Completion

Run focused test, full COL-03C unit suite, COL-03B regression.

Commit:

`feat: audit COL-03C derived reference quality`

---

## Task 4 — Deterministic TAV.7 documentary observation inventory

### Files

Create/modify:

- `experiments/cew_col03c/tav07_observations.py`
- `tests/cew_col03c/test_tav07_observations.py`

### Intent

COL-03C should not merely prove that TAV.7 exists. It should produce a deterministic **document-level observation inventory** that later gates can use without pretending that observations are already bound to TAV.5 occurrences.

### RED

Tests first for:

1. normalized observation IDs are deterministic;
2. observations keep page/region/source lineage;
3. empty or unreadable text is explicit, not invented;
4. duplicate OCR tokens are not silently collapsed when their regions differ;
5. input order does not affect observation IDs/digest;
6. document-level observations have `binding_state = UNBOUND` by default;
7. no support identity is emitted by the observation extractor.

### GREEN interfaces

```python
normalize_tav07_text_observations(
    raw_observations: list[dict],
    *,
    source_metadata: dict,
) -> list[dict]

build_tav07_observation_inventory(
    observations: list[dict],
    *,
    extraction_method: str,
    extraction_version: str,
) -> dict
```

The exact-source workflow may use deterministic Tesseract or an existing PDF text layer. The output schema must not depend on which extractor was convenient; it must record the actual method/version.

### Matching rule at this task

No occurrence binding is performed here.

Commit:

`feat: inventory TAV07 documentary observations`

---

## Task 5 — Build cross-document evidence bundles, hypotheses and closure

### Files

Create/modify:

- `experiments/cew_col03c/cross_document.py`
- `tests/cew_col03c/test_cross_document.py`

### RED

Tests must require:

1. exactly 22 bundles, one per predecessor occurrence;
2. TAV.7 availability is recorded independently of whether a counterpart is found;
3. inventory-only historical artifacts appear as governed recovery gaps, not `NO_EVIDENCE`;
4. blocked topology reference can be cited as data-quality evidence but cannot support identity hypotheses;
5. a TAV.7 observation may become a candidate only through an explicitly permitted matching channel;
6. exact label equality alone produces at most a non-authoritative hypothesis;
7. multiple TAV.7 occurrences of the same label produce ambiguity, never auto-selection;
8. hypotheses always have `promotion_authorized = false`;
9. all authority keys remain false;
10. occurrence input order and observation input order do not affect output digest;
11. `available_cross_document_evidence_evaluated` is separate from `historical_derived_artifact_recovery_complete` and `all_occurrences_cross_document_resolved`.

### GREEN interfaces

```python
build_cross_document_bundles(
    *,
    predecessor_occurrences: list[dict],
    tav07_source: dict,
    tav07_observations: list[dict],
    historical_artifacts: list[dict],
    derived_reference_quality: dict,
) -> list[dict]

build_cross_document_reconciliation(...) -> dict

build_cross_document_closure(...) -> dict
```

### Frozen-base expectation

The current known repository history is expected to yield:

- TAV.7 primary source `MATERIALIZED_VERIFIED`;
- historical derived v19/v22/v25/v51 artifacts still not materialized;
- topology derived reference materialized but blocked for identity use if unresolved endpoint IDs exist;
- all 22 occurrence bundles present;
- identity resolution still false;
- all authority closed.

This expectation MUST NOT be hard-coded as the production decision procedure.

Commit:

`feat: reconcile COL-03C cross-document evidence`

---

## Task 6 — Exact-source writer and isolated qualification workflow

### Files

Create/modify:

- `experiments/cew_col03c/exact_source.py`
- `tests/cew_col03c/test_exact_source_writer.py`
- `.github/workflows/validate-cew-col03c-governed-cross-document-materialization.yml`

### RED

Before implementation, add writer/workflow contract tests for:

1. exactly five output files under `evidence/cew-col03c/`;
2. no writes to prior evidence namespaces;
3. canonical outputs identical across reversed/perturbed set-like inputs;
4. TAV.7 source mismatch blocks closure;
5. historical unavailable artifacts are persisted as gaps;
6. authority drift blocks closure;
7. the exact predecessor SHA is persisted.

### GREEN exact-source orchestration

`python -m experiments.cew_col03c.exact_source` must:

1. consume freshly rebuilt COL-03B artifacts;
2. validate exact COL-03B predecessor semantics;
3. fetch/materialize TAV.7 only from frozen archive commit;
4. verify exact SHA-256;
5. build deterministic source metadata;
6. build deterministic TAV.7 observation inventory;
7. materialize permitted derived references from the same frozen archive commit;
8. audit their integrity/data quality;
9. load historical registration inventory from exact registration commit;
10. classify historical derived artifacts by real availability;
11. build all 22 bundles twice with perturbed order;
12. require canonical equality;
13. write the five artifacts;
14. print a concise qualification summary with digests.

### Workflow

Create `CEW-COL-03C Governed Cross-Document Materialization` with two jobs.

#### `unit`

- exact candidate checkout;
- Python 3.12.15;
- COL-03C unit tests;
- COL-03B regression tests.

#### `exact-source`

- exact candidate checkout;
- prove `cfd9382b…` ancestry and exact head;
- frozen Python/toolchain;
- fetch archival source commit `78c20a52…`;
- fetch historical registration commit `643dc893…`;
- rebuild upstream COL-02 → COL-03A → COL-03B using the existing qualified sequence;
- verify frozen predecessor contract;
- run COL-03C exact-source;
- assert:
  - 22 occurrence bundles;
  - TAV.7 primary source verified;
  - `available_cross_document_evidence_evaluated = true`;
  - historical derived recovery reflects actual availability and is not fabricated;
  - blocked derived references cannot promote identity;
  - `all_occurrences_cross_document_resolved = false` at this gate;
  - all authority false;
  - no historical gap encoded as inspected negative evidence;
- upload only `evidence/cew-col03c/`.

Commit:

`ci: qualify COL-03C cross-document materialization`

---

## Task 7 — Governed checkpoint and exact-SHA review

### No product-code changes unless a proven defect is found

1. Freeze final exact SHA.
2. Verify PR remains Draft/open/unmerged.
3. Verify merge-base exactly descends from COL-03B head.
4. Verify Memory Gate.
5. Verify COL-03C unit + COL-03B regression.
6. Verify exact-source full replay and artifact upload.
7. Record artifact ID and SHA-256 digest.
8. Inspect the exact diff for authority leakage and predecessor mutation.
9. Run final whole-branch review against spec and Review Focus.
10. If review finds Critical/Important issue, perform one bounded RED→GREEN fix pass, then rerun the full exact-SHA qualification.
11. Do not mark Ready, merge or deploy.

---

## Review Focus

The final reviewer must deliberately check these failure modes:

1. **Source identity:** TAV.7 must come from exact archive commit/path/SHA, not merely from a same-named file.
2. **Inventory ≠ bytes:** a historical inventory entry must never become row-level evidence without materialization.
3. **Primary ≠ derived:** TAV.7 PDF authority must remain distinct from OCR/raster/CSV derivatives.
4. **Topology mismatch:** the 57-node table and connection endpoint universe must not be silently coerced into a coherent graph.
5. **Historical cardinality:** remembered `27×5`, `57/38/10`, package v19/v22/v25/v51 facts must not become production assignments.
6. **Weak text match:** exact label equality across sheets may create a candidate, never an assignment.
7. **Ambiguity:** duplicate TAV.7 label candidates must remain ambiguous.
8. **Gap semantics:** not-materialized sources must never be reported as inspected `NO_EVIDENCE`.
9. **Authority:** support/family/section/fixed-line/vertical-chain/canonical-node/structural identity and all write/promotion gates remain false.
10. **Scope:** no predecessor artifact mutation, no M0-S/M0-G, no G2C/G3, no EdiLus, no merge/deploy.

## Completion state

Target terminal state:

`COL-03C AVAILABLE CROSS-DOCUMENT EVIDENCE EVALUATED / HISTORICAL DERIVED RECOVERY EXPLICIT / IDENTITY PROMOTION NOT AUTHORIZED / PR DRAFT / NO MERGE / NO DEPLOY`
