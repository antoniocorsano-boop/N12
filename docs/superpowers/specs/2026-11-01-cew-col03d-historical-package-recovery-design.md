# CEW-COL-03D — Historical Package Recovery Gate

**Status:** DESIGN APPROVED BY CONTINUATION / IMPLEMENTATION AUTHORIZED / NO IDENTITY PROMOTION / NO MERGE / NO DEPLOY

## 1. Purpose

COL-03D is the governed successor to qualified COL-03C exact head:

`a9daa18ddfb56eaf1834ad17f329e2f2db0af72e`

Its purpose is to recover the historical structural package that COL-03C could only represent as inventoried-but-not-materialized evidence, preserve its byte-level provenance, qualify the required package members, and expose their real row-level content for later evidence reconciliation **without promoting any support, chain, family, section, fixed line, canonical node or canonical geometry**.

COL-03D answers only:

> Can the historical v25 package and its required members be reconstructed from the previously acquired original bytes, verified immutably, parsed deterministically, and classified for evidentiary use without treating historical associations as structural truth?

## 2. Frozen predecessor and authority boundary

Implementation MUST descend from exact qualified COL-03C head:

`a9daa18ddfb56eaf1834ad17f329e2f2db0af72e`

COL-03D MUST preserve:

- exactly 22 governed `COL-OCC-0001` … `COL-OCC-0022` subjects;
- `all_occurrences_cross_document_resolved = false`;
- all downstream authority flags false;
- TAV.7 primary PDF authority distinct from historical derived artifacts;
- topology reference `DATA_QUALITY_BLOCKED` until its internal identifier universe is genuinely reconciled.

The following MUST remain false throughout COL-03D:

- `support_identity_authorized`;
- `text_identity_binding_authorized`;
- `family_assignment_authorized`;
- `section_assignment_authorized`;
- `fixed_line_assignment_authorized`;
- `vertical_chain_assignment_authorized`;
- `structural_identity_authorized`;
- `canonical_node_assignment_authorized`;
- `canonical_geometry_authorized`;
- `canonical_write_authorized`;
- `g2c_promotion_authorized`;
- `g3_authorized`;
- `merge_authorized`.

## 3. Recovered package source

A persistent user-library copy of the historical package was recovered on 2026-11-01 from the prior 2026-08-20 acquisition:

- logical package name: `Ariano_Irpino_DXF_strutturale_v25.zip`;
- recovered library filename: `Ariano_Irpino_DXF_strutturale_v25(1).zip`;
- recovered size: `5,345,286` bytes;
- SHA-256: `10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d`;
- ZIP member count: `91`.

This exact digest is the package identity for COL-03D. A package with the same name but a different digest is `PROVENANCE_MISMATCH`.

The package is historical derived evidence. It does not supersede the original PDF drawing archive.

## 4. Required recovery set

COL-03D MUST recover and verify at least the eight members explicitly registered by `archive/ARTEFATTI_STORICI.md` for the structural v25 package:

| Member | Size bytes | SHA-256 | Qualified role |
|---|---:|---|---|
| `TAV5_CARPENTERIA.dxf` | 717875 | `f8daddb352ac52399f83d34995dada371ab8940d4866baa9d5acaa913b67e3ec` | derived graphical reference |
| `TAV6_TRAVI.dxf` | 379309 | `770eda8e5cf37f386427229aba68e414a3da3b6bda81f6cd557cf11cea1d14c1` | derived graphical reference |
| `TAV7_PILASTRI.dxf` | 454309 | `6ab095fee72db4f5163dac6cc85e04b8b47e6b54a9f4d8090a9c515512bec47d` | derived graphical reference |
| `ABACO_TOPOLOGICO_TAV5_v11.csv` | 2852 | `186345c8227945003e8ed57cdc6bc9d93a4f2c22ecfbbfe0af0e3e415cd1b442` | historical topology reference |
| `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv` | 4564 | `3226fd19cc6a9fc7ff52d5c95d28f16f72b7b173e3b9d3a7403d5dbbb74107a6` | candidate cross-document association evidence |
| `MATRICE_PILASTRI_27x5_v22.csv` | 6349 | `a77de6b5f1310b8e0662f35f5381b656a134f36ffd92c24b8bbaf74b9cc89ce1` | historical vertical-matrix evidence |
| `ABACO_TRAVI_TAV6_v23.csv` | 8240 | `48d48e014718b3d951fd1c4c5669f149203e684306ebf7933c3e2a16c95182bb` | beam documentary reference |
| `ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv` | 7279 | `18ac263085b1da832346f8280d9788ad30708bb76cff99d19ee127858a38ee1e` | beam candidate-association evidence |

The three DXFs identify AutoCAD version `AC1027` in their header. Their geometry is historical derived geometry, not canonical current geometry.

## 5. Inventory-name reconciliation

COL-03D MUST correct a naming discrepancy in the COL-03C requested-artifact surface without rewriting COL-03C evidence:

- historical inventory and recovered ZIP contain `ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv`;
- COL-03C requested `TABELLA_CORRISPONDENZE_TRAVI_v25.csv`, which is not the registered package member.

COL-03D MUST derive its required set from the governed historical inventory plus explicit recovery policy, not from a synthetic absent filename.

Rules:

- an inventory-known member absent from the verified package is `INVENTORY_PACKAGE_MISMATCH`;
- a requested name absent from the inventory is `NOT_IN_GOVERNED_INVENTORY`, not `KNOWN_INVENTORY_NOT_MATERIALIZED`;
- aliases require an explicit governed alias receipt; filename similarity is insufficient.

## 6. Preservation architecture

The original ZIP MUST be treated as immutable package evidence.

Preferred repository archival target:

`archive/historical_packages/v25/Ariano_Irpino_DXF_strutturale_v25.zip`

If the exact ZIP cannot be committed byte-for-byte by the available repository transport, the implementation MUST fail closed for package-level repository qualification. It may still produce a local recovery receipt, but it MUST NOT report `historical_package_repository_materialized = true`.

Required-member exact bytes may be materialized under:

`archive/historical_packages/v25/members/`

Only byte-preserving writes are permitted. No DXF normalization, line-ending conversion, CSV reserialization, encoding conversion, recompression or field cleanup is allowed in the source archive.

Parsed/normalized data belongs only under `evidence/cew-col03d/`.

## 7. Package and member provenance

The package recovery manifest MUST persist:

- package logical/original name;
- package SHA-256;
- package byte size;
- member count;
- acquisition date/context;
- immutable repository path if materialized;
- package materialization state;
- sorted member inventory with raw member path, uncompressed size, CRC32 and SHA-256;
- required-member flag;
- governed-inventory membership.

Every required member MUST be independently hash-verified before parsing.

## 8. Parsing policy

Parsing is downstream from byte verification.

CSV parsing MUST:

- detect/validate delimiter from the verified raw bytes;
- preserve raw header names;
- retain raw row text or row-level provenance references;
- expose deterministic normalized row objects for analysis;
- never rewrite the archived source member;
- detect malformed row width, duplicate identifiers and missing required keys.

DXF parsing MUST:

- verify header/version;
- inventory entities/layers/text without mutating the file;
- preserve source handle/layer/text provenance when available;
- distinguish graphical observations from structural assignments.

## 9. Qualification witnesses from the recovered bytes

The following are current exact recovery witnesses and MUST be derived, not hard-coded as business conclusions:

- `ABACO_TOPOLOGICO_TAV5_v11.csv`: 57 data rows plus header;
- `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv`: 27 data rows plus header;
- `MATRICE_PILASTRI_27x5_v22.csv`: 135 data rows plus header;
- `ABACO_TRAVI_TAV6_v23.csv`: 46 data rows plus header;
- `ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv`: 46 data rows plus header.

These cardinalities prove recovered content only. They do not prove that every row is correct or authoritative.

## 10. Historical semantics must remain explicit

Recovered rows preserve their original evidence semantics.

Examples from the recovered package include states such as:

- `VER`;
- `RIF`;
- `ND`;
- `PROPOSTA_GEOMETRICA`.

COL-03D MUST NOT reinterpret `VER` as structural truth merely because the file is now available. File recovery validates provenance of the historical artifact; it does not retroactively validate every historical inference.

Historical notes that explicitly say an association is not demonstrated or requires documentary confirmation MUST remain machine-visible constraints.

## 11. Topology quality gate

The recovered `ABACO_TOPOLOGICO_TAV5_v11.csv` may be compared with the already materialized connection reference, but COL-03D MUST preserve the distinction between:

- recovered historical node table;
- recovered/derived connection data;
- unresolved endpoint identifiers;
- complete structural topology.

Recovery of the original 57-row abaco does not erase the COL-03C finding that other historical records reference identifiers beyond `N057`.

No missing node may be manufactured.

## 12. 27×5 matrix policy

Recovery of `MATRICE_PILASTRI_27x5_v22.csv` changes its state from inventory-only to byte-verified historical evidence.

It does **not** authorize:

- binding a `COL-OCC-*` directly to `N###`;
- assigning a vertical chain automatically;
- propagating section/armature values across levels;
- replacing present-day occurrence geometry;
- treating the 27 chains as complete current structural identity.

Each row remains historical evidence requiring independent cross-document reconciliation.

## 13. TAV.5↔TAV.7 association policy

Recovery of `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv` permits its rows to enter the evidence surface.

It does not permit automatic identity binding. In particular:

- blank `sigla_TAV5`, `ordine_TAV7` or section fields remain blank/unknown;
- a historical note stating that armature type is documented but association to the individual column is not demonstrated is a blocking semantic constraint;
- geometrical compatibility alone remains insufficient.

## 14. Evidence classes

Each recovered member ends in one of:

- `MATERIALIZED_VERIFIED`;
- `PROVENANCE_MISMATCH`;
- `INVENTORY_PACKAGE_MISMATCH`;
- `NOT_IN_GOVERNED_INVENTORY`;
- `PARSE_DATA_QUALITY_BLOCKED`.

Each parsed row additionally carries its historical evidence state and a `promotion_authorized = false` default.

## 15. Completion concepts

COL-03D reports separately:

### 15.1 Package recovery

`historical_package_recovery_complete = true` only when the package bytes match the frozen package digest and all required registered members are present with matching member digests.

### 15.2 Repository materialization

`historical_package_repository_materialized = true` only when the exact package is preserved at an immutable repository path and the workflow can reconstruct it from the exact candidate checkout.

### 15.3 Required-member materialization

`required_historical_members_materialized = true` only when every required member is byte-verifiable in the exact candidate replay.

### 15.4 Row-level recovery

`historical_row_level_evidence_recovered = true` only when all required CSV members parse deterministically and row provenance is retained.

### 15.5 Structural identity

`historical_evidence_identity_promoted = false` throughout COL-03D.

## 16. Outputs

COL-03D writes derived evidence only under:

`evidence/cew-col03d/`

Required outputs:

1. `historical-package-recovery-manifest.json`
2. `historical-member-manifest.json`
3. `historical-derived-data-quality.json`
4. `historical-recovery-reconciliation.json`
5. `historical-recovery-closure.json`

No predecessor evidence artifact may be rewritten.

## 17. Determinism

Outputs MUST be invariant to:

- ZIP central-directory order;
- filesystem extraction order;
- CSV row enumeration where semantics are set-like;
- repeated parsing of exact bytes;
- repeated exact-source workflow execution.

Canonical output digests use deterministic serialization.

## 18. Workflow qualification

The isolated COL-03D workflow MUST:

1. checkout the exact candidate SHA;
2. prove ancestry from qualified COL-03C `a9daa18d…`;
3. verify package SHA-256 and byte size from the candidate archive source;
4. verify ZIP integrity and exact member count;
5. verify all required registered members and member digests;
6. parse required CSV members twice and prove deterministic normalized results;
7. audit DXF headers/entities without mutation;
8. assert inventory/name reconciliation, including rejection of the obsolete synthetic `TABELLA_CORRISPONDENZE_TRAVI_v25.csv` name;
9. assert historical row semantics are preserved;
10. assert every downstream authority flag remains false;
11. run COL-03C regression tests;
12. upload only `evidence/cew-col03d/` as workflow evidence.

If exact package bytes are not repository-replayable, step 3 MUST fail closed and qualification stops.

## 19. Human Review

No Human Review is required merely to recover exact bytes.

Human Review becomes required only in a later gate when recovered historical rows are proposed as bindings to the 22 governed occurrences or when competing historical/documentary evidence requires adjudication.

COL-03D itself cannot promote those bindings.

## 20. Stop conditions

COL-03D stops after package/member recovery, parsing and data-quality qualification.

It MUST NOT continue into:

- support identity adjudication;
- vertical chain promotion;
- section assignment;
- family assignment;
- fixed-line or analytical-axis assignment;
- M0-S;
- M0-G;
- canonical CAD/BIM write;
- G2C/G3;
- EdiLus export;
- merge/deploy.

## 21. Success condition

COL-03D succeeds only when the system can say, reproducibly and auditably:

> The previously acquired historical v25 package has been recovered from exact bytes, its package identity and required members have been verified, its registered historical CSV/DXF content is available with explicit row/object provenance and data-quality state, inventory-name drift has been reconciled, and none of that historical evidence has been silently converted into current structural identity.
