# CEW-COL-03C — Governed Cross-Document Source Materialization

**Status:** DESIGN APPROVED BY CONTINUATION / IMPLEMENTATION AUTHORIZED / NO IDENTITY PROMOTION / NO MERGE / NO DEPLOY

## 1. Purpose

COL-03C is the governed successor to COL-03B. Its purpose is to make the cross-document evidence surface reproducible without converting documentary evidence into structural identity.

It answers only:

> Which cross-document sources relevant to the 22 governed `COL-OCC-*` occurrences can be reconstructed from immutable repository evidence, which historical derived artifacts are still only inventoried, and what source-grounded cross-document evidence can therefore be evaluated without promotion?

COL-03C does **not** answer:

- which support number belongs to a `COL-OCC-*` occurrence;
- which occurrences form the same vertical structural chain;
- which section, family or fixed line belongs to a support;
- which canonical node is authoritative;
- whether any CAD/BIM/structural write is authorized.

Those remain successor decisions.

## 2. Frozen predecessor

Implementation MUST descend from the exact qualified COL-03B candidate:

`cfd9382b703d0a974daf63c23dc2b6d3d81eadad`

COL-03B guarantees:

- exactly 22 occurrence subjects `COL-OCC-0001` … `COL-OCC-0022`;
- documentary evidence collection complete for the channels then available;
- `all_occurrences_identity_resolved = false`;
- historical derived artifacts inventoried but not materialized;
- no identity/family/section/fixed-line/canonical-write authority.

COL-03C MUST preserve those subjects and authority boundaries.

## 3. Source hierarchy

COL-03C uses an explicit three-tier source hierarchy.

### Tier A — primary documentary source

Primary cross-document authority for TAV.7 is the original archived PDF:

- repository: `antoniocorsano-boop/N12`;
- archive commit: `78c20a52db4f391ce0d13b9705b9f04737e218c9`;
- path: `archive/documentazione_originaria/tavola7.pdf`;
- catalogue id: `TAV-07A`;
- class: `particolari_strutturali`;
- state: `DOC`;
- SHA-256: `38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b`;
- repository blob: `bf92501e723843fd912976b1b711285a61c548d3`;
- repository size: `798816` bytes.

The archive commit and SHA-256 are both required. A matching filename without matching immutable provenance is not the same source.

### Tier B — inventoried historical derived artifacts

The historical inventory records, among others:

- `TAV7_PILASTRI.dxf`;
- `ABACO_TOPOLOGICO_TAV5_v11.csv`;
- `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv`;
- `MATRICE_PILASTRI_27x5_v22.csv`;
- `TABELLA_CORRISPONDENZE_TRAVI_v25.csv`.

The historical registration commit `643dc8934ec0c8ac37613ec2880cf9e02f5a9df2` records their existence and historical package lineage, but it does not contain their bytes. Therefore they MUST remain:

`KNOWN_INVENTORY_NOT_MATERIALIZED`

until exact bytes plus immutable path/version/digest are recovered.

Inventory knowledge MUST NOT be converted into row-level evidence, support identity or a 27×5 chain assignment.

### Tier C — recoverable derived reference data

The immutable archive commit also contains reference datasets such as:

- `data/canonical/tav5_topology_nodes_57.csv`;
- `data/canonical/tav5_topology_connections_v07.csv`;
- `data/canonical/telaio5_tav5_candidate_matrix_v1.csv`.

These may be materialized with exact blob/digest provenance as **derived reference evidence only**. They are not primary documentary sources and do not authorize identity promotion.

## 4. Historical inventory policy

`archive/ARTEFATTI_STORICI.md` remains the inventory authority for known historical artifacts.

Its policy is binding for COL-03C:

- historical packages/ZIPs are evidence/reference material;
- model-facing data must be extracted into governed canonical structures with explicit provenance;
- historical artifacts do not replace active documentary sources;
- an inventory row proves that an artifact was known, not that its content is currently available or qualified.

## 5. Required materialization states

Every requested source or artifact MUST end in exactly one state:

- `MATERIALIZED_VERIFIED` — bytes were reconstructed and immutable provenance/digest verified;
- `KNOWN_INVENTORY_NOT_MATERIALIZED` — known through a governed inventory, but bytes/provenance are insufficient for use;
- `NOT_FOUND` — no governed inventory/source record establishes the requested artifact;
- `PROVENANCE_MISMATCH` — bytes exist but fail immutable identity/digest checks;
- `DATA_QUALITY_BLOCKED` — bytes are verified, but internal consistency prevents the intended evidentiary use.

`NO_EVIDENCE` MUST NOT be used for a source that simply was not materialized.

## 6. TAV.7 exact-source materialization

COL-03C MUST reconstruct TAV.7 from the frozen archive commit, not from a working branch copy.

Required checks:

1. fetch exact archive commit `78c20a52…`;
2. materialize `archive/documentazione_originaria/tavola7.pdf`;
3. verify SHA-256 `38a0cce1…`;
4. verify non-zero page count;
5. produce deterministic page/raster metadata sufficient for replay;
6. repeat the extraction/materialization and prove canonical metadata equality;
7. persist source lineage in the COL-03C manifest.

A raster/preview is derivative evidence. The PDF remains authority.

## 7. TAV.7 role in COL-03C

TAV.7 is classified as `particolari_strutturali`, not assumed to be a geometrically aligned plan of TAV.5.

Therefore COL-03C may derive from TAV.7:

- visible documentary labels and callouts;
- section/detail references;
- documentary support/column symbols where demonstrably present;
- candidate counterpart evidence;
- explicit absence/unavailability states for an evidence channel.

COL-03C MUST NOT infer cross-sheet identity from mere relative page position, nearest geometry or visual similarity alone.

## 8. Derived topology reference quality gate

The archive contains a 57-row node dataset (`N001` … `N057`) and a connection dataset whose endpoints include identifiers beyond `N057`.

COL-03C MUST not silently join these as one coherent graph.

For each materialized derived reference dataset it MUST compute and persist:

- byte SHA-256;
- row count;
- declared identifier universe;
- referenced identifier universe;
- missing/unresolved referenced identifiers;
- data-quality state.

If any connection endpoint is absent from the materialized node table, the topology reference MUST be marked `DATA_QUALITY_BLOCKED` for identity resolution. The raw rows remain inspectable evidence.

This finding is not a reason to discard the datasets and is not permission to manufacture the missing nodes.

## 9. Historical 27×5 and TAV.5↔TAV.7 associations

The remembered/registered 27×5 matrix and association abaco are valuable historical evidence, but COL-03C may use their row-level content only if their exact files are recovered with immutable provenance.

Until then:

- `historical_27x5_materialized = false`;
- `historical_tav5_tav7_association_materialized = false`;
- no `N###`, chain id or support id may be emitted from those artifacts;
- historical cardinalities may appear only as inventory metadata, never as a production oracle.

## 10. Occurrence subjects

The 22 COL-03B occurrence IDs are immutable subjects. COL-03C MUST NOT:

- create a 23rd occurrence;
- drop or reorder an occurrence semantically;
- replace `COL-OCC-*` with a historical `N###` identifier;
- mutate COL-03A geometry or COL-03B documentary observations.

Every cross-document evidence record MUST reference exactly one governed occurrence or explicitly be a source-level/global data-quality record.

## 11. Cross-document evidence model

For each `COL-OCC-*`, COL-03C emits an evidence bundle containing at least:

- `occurrence_id`;
- predecessor lineage/digest reference;
- primary TAV.7 source availability state;
- TAV.7 documentary observations relevant to the occurrence, if any;
- candidate counterpart hypotheses, if supported;
- historical derived artifact availability state;
- derived reference evidence, if actually materialized and relevant;
- conflict/ambiguity state;
- exact-source reconstructibility;
- authority closure flags.

Evidence values MUST preserve channel provenance. Evidence from TAV.7, topology CSVs and historical inventory cannot be flattened into one undifferentiated score.

## 12. Hypotheses, not assignments

Permitted hypothesis kinds:

- `TAV07_DOCUMENTARY_COUNTERPART_CANDIDATE`;
- `CROSS_DOCUMENT_LABEL_CANDIDATE`;
- `DERIVED_REFERENCE_COUNTERPART_CANDIDATE`.

Every hypothesis MUST include:

- supporting evidence ids;
- contradicting evidence ids;
- channel count;
- state;
- `promotion_authorized = false`.

No single channel can promote identity in COL-03C.

## 13. Matching constraints

Permitted candidate evidence channels include:

- explicit text/label equality grounded in exact source;
- explicit graphical callout linkage;
- documented source-reference linkage;
- reproducible topology signature, but only when the underlying topology reference passes its integrity gate;
- recovered historical association rows, but only after immutable materialization.

Forbidden auto-binding rules include:

- nearest-neighbor only;
- visual similarity only;
- same approximate page position;
- same section shape;
- same historical family;
- remembered 27×5 chain;
- any rule that promotes because there is only one convenient candidate.

## 14. Conflict states

At minimum:

- `NONE`;
- `AMBIGUOUS_CROSS_DOCUMENT_MATCH`;
- `CONTRADICTORY_CROSS_DOCUMENT_EVIDENCE`;
- `PRIMARY_SOURCE_RECONSTRUCTION_FAILED`;
- `HISTORICAL_ARTIFACT_NOT_MATERIALIZED`;
- `DERIVED_REFERENCE_DATA_QUALITY_BLOCKED`;
- `PREDECESSOR_DRIFT`;
- `AUTHORITY_DRIFT`.

A gap may be non-blocking for **available-source evaluation** while still blocking identity resolution.

## 15. Two separate completion concepts

COL-03C MUST not overload the word “complete”. It reports separately:

### 15.1 Available-source evaluation

`available_cross_document_evidence_evaluated = true` only when:

- exact COL-03B predecessor is verified;
- exact TAV.7 primary source is materialized and verified;
- every known historical derived artifact has an explicit materialization state;
- every materialized derived reference has a data-quality result;
- all 22 occurrences have an explicit cross-document evidence bundle;
- deterministic replay passes;
- no authority drift exists.

### 15.2 Historical recovery

`historical_derived_artifact_recovery_complete = true` only when all required historical derived artifacts have verified bytes and provenance.

This is expected to remain `false` if v19/v22/v25/v51 artifact bytes are not recovered.

### 15.3 Identity resolution

`all_occurrences_cross_document_resolved = true` only in a future adjudication gate. COL-03C MUST keep it `false` unless a later approved design changes authority.

## 16. Authority closure

For every occurrence and every closure artifact, the following MUST remain false:

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

## 17. Determinism

COL-03C output MUST be invariant to:

- filesystem enumeration order;
- inventory row order;
- occurrence input order;
- derived reference row order, where semantics are set-like;
- repeated exact-source reconstruction.

Canonical digests MUST be computed from deterministic serialization.

## 18. Outputs

COL-03C writes only under:

`evidence/cew-col03c/`

Required artifacts:

1. `source-materialization-manifest.json`
2. `derived-reference-quality.json`
3. `cross-document-evidence-ledger.json`
4. `cross-document-reconciliation.json`
5. `cross-document-evidence-closure.json`

No COL-02/COL-03A/COL-03B governed artifact may be rewritten.

## 19. Expected frozen-base state

On the current known repository history the expected evidence state is:

- exact TAV.7 primary source: recoverable and verifiable;
- historical inventory: present;
- historical v19/v22/v25/v51 derived file bytes: not currently materialized on the qualified branch;
- topology node reference: materializable;
- topology connection reference: materializable but internally inconsistent against the 57-node table for identity use;
- 27×5 historical matrix: inventory-known, raw file not currently materialized;
- TAV.5↔TAV.7 historical association abaco: inventory-known, raw file not currently materialized.

These are qualification witnesses, not hard-coded production conclusions. Runtime logic derives them from source and inventory evidence.

## 20. Human Review

Human Review is required only if COL-03C produces a real candidate ambiguity or documentary conflict that cannot be represented faithfully without adjudication.

A missing historical file does not require a fabricated human decision. It remains an explicit recovery gap.

No human receipt may promote structural identity in COL-03C.

## 21. Workflow qualification

The isolated COL-03C workflow MUST:

1. checkout exact candidate SHA;
2. prove ancestry from `cfd9382b…`;
3. run COL-03C unit tests;
4. run COL-03B regression tests;
5. fetch exact archive commit `78c20a52…`;
6. materialize and verify TAV.7;
7. materialize permitted derived reference datasets from the same frozen archive commit;
8. run integrity/data-quality checks;
9. build COL-03C artifacts twice with perturbed input ordering and prove canonical equality;
10. assert all authority flags remain false;
11. assert historical inventory gaps are not misreported as inspected `NO_EVIDENCE`;
12. upload only `evidence/cew-col03c/`.

A later full upstream replay may be added if needed, but COL-03C must never weaken the exact predecessor contract to make the workflow cheaper.

## 22. Stop conditions

COL-03C stops after cross-document source materialization and available-source evidence reconciliation.

It MUST NOT automatically continue into:

- support identity adjudication;
- vertical chain construction;
- 27×5 chain promotion;
- M0-S section assignment;
- M0-G fixed-line/offset assignment;
- canonical structural model write;
- G2C/G3 promotion;
- EdiLus export;
- merge/deploy.

## 23. Success condition

COL-03C succeeds when the system can say, reproducibly and auditably:

> TAV.7 and every other source actually available to this gate have been reconstructed and evaluated with explicit provenance; every known unavailable historical artifact is represented as a governed recovery gap; all 22 occurrences have cross-document evidence state; no unresolved source gap has been disguised as negative evidence; no structural identity has been promoted.

That success is an evidence-readiness milestone, not a structural-model milestone.
