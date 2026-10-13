# CASE 13 — CEW core end-to-end assurance

**Contract:** CEW-CONTRACT-01  
**Qualification scope:** core logical contract only  
**Operational source authority:** `d806dcca72779b5a186defe557a7a9b739575a90` (`work/m0-global-model`, read-only for this qualification)  
**Status:** PASS  
**Solver boundary:** `solver_authorized=false`; `calculation_model_ready=false`

## Purpose

Demonstrate a real, reproducible N12 provenance chain through the CEW-CONTRACT-01 core without fabricating a `SolverRun` or `Result`:

`Source → Evidence → Observation/Claim → P05 topology candidate → P06 adjudication → P07 promoted primary geometry → FPEP release → canonical foundation model → CanonicalSnapshot/ModelGeneration → Projection → Verification → Receipt`.

The solver extension remains explicitly outside this case and is transferred to `CEW-FEM-01`:

`ModelGeneration → SolverRun → Result → Verification → Receipt`.

## 1. Primary source and evidence authority

FPEP identifies `tavola1-2.pdf` as `TAV-01S`, the foundation-carpentry geometry/topology authority. `M1F_FOUNDATION_SOURCE_ROLE_AUDIT_v1.csv` distinguishes it from `TAV-01A`, which is property/reinforcement authority and is not allowed to generate geometry.

The FPEP procedure requires immutable-source identity/hash verification, reproducible derived evidence anchors, two blind readings, metric checks and information barriers before the primary geometry gate. Before P07, legacy foundation topology, the historical 38-support/58-member checkpoint, PT/M0-G generator geometry and TAV-01A reinforcement groups are forbidden as geometry-generation inputs.

Primary evidence anchors used by the topology chain include `P001-TILE-*`, `P001-REGION-*` and the page overview/incident-sweep artifacts. They are derived evidence; the immutable TAV-01S PDF remains the source authority.

## 2. P05 topology candidate — no premature promotion

`analysis/fpep/FPEP_PRIMARY_TOPOLOGY_CANDIDATE_v1.csv` contains exactly 15 P05 continuity candidates (`P05-CAND-001` … `P05-CAND-015`). At P05:

- all candidates preserve their source observation and evidence anchor;
- no member is created (`member_created=false` for all 15);
- no candidate is directly eligible for P07;
- unresolved endpoint/chain or missing second-reader semantic continuity remains explicit;
- proximity, numbering order and legacy target counts are not used to generate connectivity.

This is a fail-closed topology-candidate stage, not a hidden geometry promotion.

## 3. P05 → P06 → P07 exact mapping

P06 performs source-local adjudication. P07 then records each P05 claim with its P06 adjudication in `upstream_evidence` and promotes only cross-validated source continuity. The mapping is one-to-one:

| P05 claim | P06 adjudication | P07 ledger | promoted state |
|---|---|---|---|
| `P05-CAND-001` | `P06-ADJ-001` | `P07-L-074` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-002` | `P06-ADJ-002` | `P07-L-075` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-003` | `P06-ADJ-003` | `P07-L-076` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-004` | `P06-ADJ-004` | `P07-L-077` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-005` | `P06-ADJ-005` | `P07-L-078` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-006` | `P06-ADJ-006` | `P07-L-079` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-007` | `P06-ADJ-007` | `P07-L-080` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-008` | `P06-ADJ-008` | `P07-L-081` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-009` | `P06-ADJ-009` | `P07-L-082` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-010` | `P06-ADJ-010` | `P07-L-083` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-011` | `P06-ADJ-011` | `P07-L-084` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-012` | `P06-ADJ-012` | `P07-L-085` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-013` | `P06-ADJ-013` | `P07-L-086` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-014` | `P06-ADJ-014` | `P07-L-087` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |
| `P05-CAND-015` | `P06-ADJ-015` | `P07-L-088` | `CURRENT_PRIMARY_CONTINUITY_CLAIM` |

`P07-L-089` separately closes global source-incidence coverage from `P06-ADJ-021`.

The P07 gate records:

- 15/15 topology candidates adjudicated;
- exhaustive primary-source incidence coverage complete;
- 0 blocking topology conflicts;
- 0 Cartesian coordinates created;
- 0 analytical members created at P07;
- no information-barrier violation.

Two metric-chain conflicts (`P07-W01`, `P07-W02`) and unpaired OCR (`P07-W03`) remain explicitly non-promoted and excluded from coordinate derivation. No value is force-fit to obtain a green gate.

## 4. P07 → FPEP release

`data/canonical/M1F_FPEP_RELEASE_GATE_v1.csv` releases the primary-evidence workflow as `PASS_WITH_WATCH` after P08–P11 downstream cross-checks. It records:

- P00–P07 chain complete;
- 38 support identifiers reconstructed from primary evidence;
- 55 primary foundation incidences;
- 0 fabricated Cartesian foundation coordinates;
- the old 58-member topology is not allowed as current geometry authority;
- unresolved numeric foundation Z and current geotechnical evidence remain explicit watches.

The release authorizes `M1F-FOUNDATION-MODEL` to assemble the successor foundation model from P07 authority. It does not authorize a structural analysis.

## 5. FPEP release → canonical foundation model

`data/canonical/M1F_FOUNDATION_MODEL_CURRENT_v1.csv` was introduced by commit `7dd4adc9eff432648a15d9807a53fa9e52d0a81f` with the explicit purpose `m1f: assemble successor foundation model from FPEP authority`.

The current frozen operational snapshot is source commit `d806dcca72779b5a186defe557a7a9b739575a90`. The foundation model preserves the P07 authority in its records (`FND-P07-*`, `P07_PRIMARY_IDENTIFIER` / `P07_PRIMARY_CROSS_VALIDATED`) and keeps unsupported Cartesian coordinates as `ND`; `ZF_COMMON` remains symbolic.

The frozen SHA-256 used by ModelGeneration for this input is:

`aaf3636487618b39dd70c5a363626d2a6d78845ed913c32d6244f2b17c3e1ed0`.

## 6. Canonical foundation model → ModelGeneration

`evidence/cew-contract-01/model-generation/N12_CEW_MODEL_GENERATION_v1.json` formalizes the real generation event `N12-CEW-MG-001` against canonical snapshot:

`N12-FROZEN-INPUTSET@d806dcca72779b5a186defe557a7a9b739575a90`.

It declares:

- builder `scripts/cew_structural_model_builder.py` and builder blob;
- source commit `d806dcca72779b5a186defe557a7a9b739575a90`;
- generation profile `CEW_CANONICAL_STRUCTURAL_GRAPH_v0`;
- explicit parameters/policies;
- six canonical input paths with SHA-256 digests, including `M1F_FOUNDATION_MODEL_CURRENT_v1.csv`;
- generated output identity, SHA-256 and artifact archive digest;
- workflow/run identity and successful deterministic invariant verification;
- inventory including 38 foundation supports and 55 foundation members;
- unresolved `FOUNDATION_NUMERIC_Z` as `ND`/`ZF_COMMON`;
- `solver_authorized=false`;
- `calculation_model_ready=false`;
- `synthetic_solver_result=false`.

The generated graph is a derived projection. It is not promoted back to source evidence.

## 7. Verification and Receipt

`N12_CEW_MODEL_GENERATION_RECEIPT_v1.json` binds the real transformation to:

- source repository and frozen source commit;
- builder and workflow paths;
- workflow run `32955421352` with conclusion `success`;
- artifact id `9601773275`;
- output SHA-256 `4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`;
- archive digest `sha256:5278bec007f427f6535947343b29d0f586da461f4acdac6aa4502aea73a1d5a5`;
- all six frozen input SHA-256 values.

The receipt explicitly states `engineering_result=false`, `solver_run=false`, `result_entity_created=false`. Its warning preserves `FOUNDATION_NUMERIC_Z` as unresolved rather than manufacturing a numeric 3D foundation axis.

## 8. Assurance result

**PASS — CEW-CONTRACT-01 core provenance is demonstrated end-to-end for a real N12 transformation.**

The chain is inspectable from the generated projection/receipt back through ModelGeneration and the frozen canonical foundation input, through FPEP release and the exact P05→P06→P07 claim lineage, to TAV-01S source/evidence anchors.

This PASS does **not** certify a structural-analysis result and does not authorize calculation. The remaining solver-specific chain is a separate mandatory debt:

`CEW-FEM-01: ModelGeneration → SolverRun → Result → Verification → Receipt`.
