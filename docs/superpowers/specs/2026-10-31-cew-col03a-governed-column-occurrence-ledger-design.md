# CEW COL-03A — Governed Column Occurrence Ledger

**Status:** DESIGN PROPOSED / IMPLEMENTATION NOT AUTHORIZED  
**Date:** 2026-10-31  
**Branch:** `docs/cew-col03a-governed-occurrence-ledger`  
**Exact base:** `0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4` (PR #175, COL-02 bounded graphical occurrence-coverage closure)

## 1. Intent

COL-03A converts the governed graphical evidence produced by COL-02 into a single, deduplicated and provenance-complete ledger of **documentary column occurrences**.

It answers only this question:

> Which exact graphical occurrences have already been governed as column occurrences, and can each one be reconstructed from immutable source evidence without depending on the discovery path that found it?

COL-03A does **not** answer which structural column each occurrence represents.

The governing transition is:

`COL-02 governed graphical evidence -> normalized occurrence records -> lineage reconciliation -> deduplication -> fail-closed ledger closure`

The output is an evidence/governance layer, not a professional structural model.

## 2. Why COL-03A exists

COL-02 intentionally preserves multiple evidence paths:

- human-approved graphical prototypes;
- prototype-guided review targets;
- visible-sibling residual review;
- human-added points bound back to frozen proposals;
- fragmented-symbol whole-symbol repairs;
- review-directed outer-envelope completion;
- final bounded occurrence-coverage closure.

This is correct for auditability, but these paths are not an appropriate permanent object identity.

A `COL02-FP-*` identifier is the identity of a detector proposal, not the professional identity of a column occurrence and not the structural identity of a support.

Before any documentary or structural identity work, CEW therefore needs one neutral layer in which every governed positive occurrence exists exactly once, independently of whether it entered the evidence chain as a prototype, shortlist target, visible sibling, human-added point or repaired symbol.

## 3. Goals

COL-03A must:

1. enumerate every governed positive column occurrence supported by the closed COL-02 evidence set;
2. assign each normalized occurrence a new neutral occurrence identifier;
3. preserve every historical source/proposal/review/repair identifier as lineage, never replace it;
4. reconstruct each occurrence from immutable exact-source provenance;
5. collapse only genuinely equivalent representations of the same physical drawing occurrence;
6. preserve unresolved conflicts instead of forcing a merge;
7. make discovery path irrelevant to downstream identity work;
8. publish an explicit authority boundary that keeps all professional/canonical promotion closed;
9. fail closed on lineage drift, duplicate ambiguity, contradictory governed decisions or missing exact-source reconstruction.

## 4. Non-goals

COL-03A must not:

- run a new detector, OCR pass, similarity search or whole-sheet sweep;
- change the frozen 611 COL-02 proposal payload or the original `COL02-FP-*` ID space;
- discover additional column occurrences;
- infer a support number from OCR, nearby dimensions or topology;
- assign text identity;
- assign structural support identity;
- assign family or section;
- assign fixed lines, analytical axes or offsets;
- infer vertical continuity or a 27x5 chain membership;
- identify a COL-03A occurrence with one of the historical 57 canonical node IDs;
- write canonical CAD/project geometry;
- authorize G2C, G3, EdiLus export, merge or deploy.

Any of those operations belongs to a successor gate.

## 5. Approaches considered

### A. OCR/text-first identity

Use internal or nearby text to name each detected occurrence immediately.

**Rejected.** COL-02 exists partly because nearby dimension text can be incorrectly associated with a column footprint. Exact-source evidence also shows that internal OCR coverage is sparse. Text can later contribute evidence, but it cannot define the ledger.

### B. Neutral governed occurrence ledger, then identity evidence

Normalize already-governed positive occurrences first; only afterwards collect documentary identity evidence against a stable occurrence set.

**Selected.** This preserves provenance, avoids circular reasoning and gives downstream identity work a stable subject.

### C. Direct matching to the historical 57 nodes / 27x5 matrix / TAV.7

Use the already reconstructed structural topology to name occurrences immediately.

**Rejected for COL-03A.** Those assets are valuable second-stage discriminants, but using them to create the occurrence set would make structural expectations act as discovery/identity oracles and would blur the distinction between documentary evidence and structural reconciliation.

## 6. Frozen inputs and authority

COL-03A is based on the exact qualified COL-02 head:

`0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4`

The qualified COL-02 boundary includes:

- frozen 611 neutral proposals and immutable `COL02-FP-*` proposal space;
- terminal residual reconciliation R01-R06;
- four human-added points bound to existing frozen proposals;
- five repair-eligible fragmented symbols with final graphical PASS;
- terminal rejection of `COL02-FP-0106` as `MISLOCALIZED_NOT_COLUMN`;
- `col02-occurrence-coverage-closure.json` with `occurrence_coverage_complete = true`;
- downstream authority flags false.

Historical manifests remain historical and are not rewritten by COL-03A.

## 7. Core concept: occurrence versus proposal versus structural identity

COL-03A formalizes three distinct namespaces:

### 7.1 Proposal identity

Example: `COL02-FP-0363`.

Meaning: one machine-generated proposal in the frozen COL-02 producer space.

It is immutable historical evidence.

### 7.2 Documentary occurrence identity

New namespace, proposed form:

`COL-OCC-0001`, `COL-OCC-0002`, ...

Meaning: one governed graphical occurrence of a column symbol on an immutable source page.

This is the only new identity COL-03A may create.

### 7.3 Structural identity

Examples may eventually include support number, vertical chain, canonical node, section/family or model element identity.

COL-03A does not create or confirm any structural identity.

## 8. Input evidence classes

The ledger builder must consume only governed/frozen evidence available at the exact base. At minimum it must reconcile positive occurrences from these classes where present:

1. `COLUMN_FOOTPRINT_HUMAN_REVIEW_v1` positive prototypes;
2. prototype-guided Human Review positive targets;
3. residual mobile/reconciliation positive decisions;
4. human-added point bindings that resolve to frozen proposals;
5. final whole-symbol graphical-review PASS items;
6. the occurrence-coverage closure artifact that proves the bounded set is terminal.

A later implementation plan must name the exact files and schemas used for each class before code is written.

## 9. Proposed ledger record

Each ledger row/object should minimally contain:

```text
occurrence_id
source_version_id
source_path
source_sha256
page_id
page_index
page_transform_id
source_geometry_ref
normalized_bbox
normalized_polygon_or_envelope_ref | null
primary_graphical_representation
source_proposal_ids[]
discovery_paths[]
human_review_receipts[]
repair_lineage[]
human_added_point_lineage[]
graphical_decision
graphical_decision_state
exact_source_reconstructible
lineage_complete
dedup_state
conflict_state
documentary_label_state
structural_identity_state
canonical_geometry_state
canonical_write_authorized
g2c_promotion_authorized
g3_promotion_authorized
notes
```

### Required authority defaults

For every ledger occurrence:

- `documentary_label_state = NOT_EVALUATED`
- `structural_identity_state = NOT_EVALUATED`
- `canonical_geometry_state = NOT_AUTHORIZED`
- `canonical_write_authorized = false`
- `g2c_promotion_authorized = false`
- `g3_promotion_authorized = false`

A ledger PASS must not change those values.

## 10. Neutral occurrence ID assignment

`COL-OCC-*` IDs must be deterministic for a frozen input set.

They must not depend on:

- order in which humans reviewed candidates;
- commit timestamp;
- dictionary iteration order;
- incidental filesystem ordering;
- support number or inferred structural identity.

The implementation plan should prefer a stable sort over source/page/geometry plus an explicit deterministic tie-break, then assign the sequential occurrence namespace.

The chosen ordering algorithm must be contract-tested because downstream evidence will reference these IDs.

## 11. Deduplication semantics

Deduplication is not "nearby means same".

Two evidence items may collapse into one `COL-OCC-*` only when the ledger can prove they refer to the same source drawing occurrence through governed lineage or sufficiently strong exact-source geometry equivalence.

### 11.1 Strong equivalence channels

Examples of acceptable equivalence evidence include:

- multiple governed review paths reference the same frozen `COL02-FP-*` proposal;
- a human-added point is explicitly bound to an existing frozen proposal;
- a whole-symbol repair explicitly declares its source fragmented proposal and is governed as replacement graphical representation for that same occurrence;
- a review-directed outer envelope explicitly derives from the same governed repair lineage.

### 11.2 Geometry-only equivalence

Pure geometry overlap may be used only under a deterministic, conservative contract and must not silently merge two nearby columns.

Any geometry-only rule must:

- operate in a common normalized source coordinate system;
- define explicit overlap/containment thresholds;
- include a separation check against neighboring governed positives;
- preserve the evidence that triggered the merge;
- fail to `AMBIGUOUS_DUPLICATE` when more than one target is plausible.

### 11.3 Forbidden deduplication evidence

The following are insufficient by themselves:

- same or similar OCR token;
- similar footprint size/aspect ratio;
- same inferred family;
- proximity to the same grid line;
- expected support count;
- membership in the historical 34-support benchmark;
- ability to make the 27x5 matrix "fit".

## 12. Representation precedence

A single occurrence may have multiple graphical representations along its history.

COL-03A must preserve all of them in lineage but expose one `primary_graphical_representation` for downstream review.

Proposed precedence:

1. governed final whole-symbol/outer-envelope representation when it explicitly supersedes a fragmented source representation;
2. otherwise the original governed frozen proposal geometry;
3. never a newly inferred geometry generated only for ledger convenience.

Precedence chooses the review representation, not a canonical CAD geometry.

## 13. Conflict model

COL-03A must be able to represent conflicts without resolving them by guess.

Required conflict states should include at least:

- `NONE`
- `CONTRADICTORY_GRAPHICAL_DECISIONS`
- `AMBIGUOUS_DUPLICATE`
- `MISSING_LINEAGE`
- `SOURCE_RECONSTRUCTION_FAILED`
- `UNEXPECTED_POSITIVE_NOT_IN_CLOSED_SET`
- `CLOSED_SET_ITEM_MISSING`

Any non-`NONE` conflict blocks ledger closure unless the design explicitly classifies that conflict as a terminal exclusion with governed evidence.

## 14. Closed-set invariant

COL-03A must not rediscover the sheet.

The occurrence set is derived exclusively from the governed COL-02 closed evidence.

Therefore the builder must prove both directions:

1. **completeness relative to COL-02:** every governed positive occurrence represented by the closed COL-02 evidence appears exactly once in the ledger;
2. **no unauthorized expansion:** every ledger occurrence can be traced back to at least one governed positive COL-02 lineage path.

No orphan ledger occurrence is allowed.

## 15. Exact-source reconstruction invariant

Every `COL-OCC-*` must be reconstructible from immutable source provenance.

At minimum the replay must verify:

- source path/version identity;
- source SHA-256;
- page identity/index;
- page transform identity where applicable;
- graphical representation coordinates in the correct coordinate space;
- lineage back to frozen proposal/review/repair evidence.

A crop image, screenshot or conversation reference may be supplementary evidence but cannot be the sole authority for an occurrence.

## 16. Output artifacts

Proposed outputs:

### 16.1 Main ledger

`evidence/cew-col03a/column-occurrence-ledger.json`

Contains the normalized occurrence records and exact lineage.

### 16.2 Reconciliation report

`evidence/cew-col03a/column-occurrence-reconciliation.json`

Contains:

- input evidence counts by class;
- number of unique governed positives before normalization;
- dedup groups and reasons;
- conflicts/exclusions;
- final ledger cardinality;
- bidirectional closed-set checks;
- deterministic replay digest.

### 16.3 Closure artifact

`evidence/cew-col03a/column-occurrence-ledger-closure.json`

May set:

`occurrence_ledger_complete = true`

only when all closure invariants pass.

Historical COL-02 files remain unchanged.

## 17. Closure rule

`occurrence_ledger_complete = true` only if all of the following are true:

1. exact COL-02 base lineage matches the frozen qualified base;
2. the COL-02 occurrence-coverage closure is valid and complete;
3. all governed positive input paths are accounted for;
4. every final ledger occurrence has complete source lineage;
5. every final ledger occurrence is exact-source reconstructible;
6. every positive source item maps to exactly one final occurrence;
7. every final occurrence maps back to at least one governed positive source item;
8. no unresolved duplicate ambiguity remains;
9. no contradictory governed graphical decision remains;
10. deterministic replay produces the same ledger IDs, geometry references and digest;
11. all documentary/structural/canonical authority flags remain closed.

Any failure keeps `occurrence_ledger_complete = false`.

## 18. Human Review boundary

COL-03A should not require routine re-review of every already governed occurrence.

Human Review is required only if deterministic reconciliation exposes a genuine unresolved conflict such as:

- two nearby governed positives cannot be safely distinguished;
- one historical item appears to map to two occurrence records;
- repair lineage is contradictory;
- exact-source reconstruction shows that two supposedly equivalent geometries are not the same drawing occurrence.

If no such conflict exists, COL-03A may close mechanically from already governed evidence.

No Human Review in COL-03A may assign support number, family, section or structural identity.

## 19. TDD order for the future implementation plan

Implementation is not authorized by this design document. If approved, the implementation plan should follow this dependency order:

1. RED: normalized evidence item model and authority defaults;
2. GREEN: adapters for governed positive evidence classes;
3. RED: deterministic occurrence-key/ID ordering;
4. GREEN: stable neutral `COL-OCC-*` assignment;
5. RED: lineage-equivalence deduplication;
6. GREEN: strong-lineage collapse with audit reasons;
7. RED: ambiguous geometry-only duplicate cases fail closed;
8. GREEN: conservative geometry reconciliation without structural or OCR identity;
9. RED: bidirectional closed-set accounting;
10. GREEN: completeness/no-expansion reconciliation;
11. RED: exact-source reconstruction and lineage drift tests;
12. GREEN: deterministic exact-source replay;
13. RED: authority-boundary drift tests;
14. GREEN: closure artifact writer;
15. full regression against frozen COL-02 evidence;
16. Human Review only for any unresolved reconciliation conflicts;
17. exact-SHA qualification.

## 20. Success criteria

COL-03A is successful when CEW can state, with reproducible provenance:

> We have one stable, neutral record for every governed graphical column occurrence in the closed COL-02 set; every record can be reconstructed from immutable source evidence; no occurrence is duplicated or orphaned; and no structural identity has been inferred.

This success criterion intentionally stops before documentary identity.

## 21. Successor boundary: COL-03B

Only after COL-03A closes may a successor tranche evaluate documentary identity evidence for each stable occurrence.

COL-03B may consider:

- internal text bindings;
- intersecting/nearby text as non-authoritative evidence;
- high-resolution local source reading;
- drawing labels and callouts;
- local topology;
- cross-document correspondence;
- historical 57-node / 27x5 / TAV.7 assets as independent reconciliation evidence.

COL-03B must still distinguish:

`documentary label -> support identity -> cross-document identity -> structural vertical identity -> section/fixed-line/canonical geometry`

and must not collapse these stages into one promotion.

## 22. Integration boundary

COL-03A is a successor to the qualified exact head of PR #175, but it does not authorize merging PR #175 or any successor automatically.

The implementation branch, when authorized, should be based exactly on:

`0191c1bdb0b1cd8387aa2260f31a7764cbe0f2b4`

unless a later explicit integration review establishes a different qualified base.

**Design state:** READY FOR HUMAN APPROVAL / NO IMPLEMENTATION / NO MERGE / NO DEPLOY.
