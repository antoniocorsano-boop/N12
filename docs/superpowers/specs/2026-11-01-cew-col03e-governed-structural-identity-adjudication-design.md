# CEW-COL-03E — Governed Structural Identity Adjudication Design

**Status:** DESIGN AUTHORIZED BY CONTINUATION / IMPLEMENTATION AUTHORIZED / NO IDENTITY PROMOTION / NO MERGE / NO DEPLOY

## 1. Intent

COL-03E is the governed successor to qualified COL-03D-BIN-01 exact head:

`df4a0a38d00d18dace597e9ca1cf449edfefca03`

Its purpose is to convert the now-replayable evidence surface into a deterministic, occurrence-by-occurrence adjudication dossier for the 22 governed column occurrences `COL-OCC-0001` … `COL-OCC-0022`.

COL-03E answers only:

> What evidence, ambiguity, contradiction, semantic blocker or explicit gap is available for deciding the structural identity of each governed occurrence, and which cases are sufficiently prepared for later human adjudication?

COL-03E does **not** answer:

> What is the final structural identity of this occurrence?

That decision belongs to a later gate consuming an explicit human receipt.

## 2. Frozen predecessor and authority boundary

Implementation MUST descend from exact qualified predecessor:

`df4a0a38d00d18dace597e9ca1cf449edfefca03`

It MUST preserve:

- exactly 22 governed occurrence identities;
- exact COL-03D historical package replayability;
- exact 8/8 required historical-member replayability;
- TAV.7 primary-source authority distinct from historical derived evidence;
- historical evidence states and notes without semantic promotion;
- `all_occurrences_cross_document_resolved = false` until a later receipt-driven gate changes it.

Throughout COL-03E the following remain false:

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

## 3. Approaches considered

### A. Automatic promotion from multi-channel support

Reject. COL-03B/C can identify documentary/cross-document candidates, but their contracts explicitly keep promotion false. Recovered historical rows also contain explicit non-demonstration notes. Agreement between derived channels is not sufficient to create structural truth.

### B. Direct manual review of raw PDFs/DXFs/CSVs for every occurrence

Safe but inefficient. It would force the human reviewer to rediscover provenance, gaps and conflicts repeatedly and would not exploit the deterministic evidence already recovered.

### C. Machine-prepared adjudication dossiers followed by explicit human receipts

Chosen. COL-03E prepares deterministic dossiers, classifies readiness, and exposes exactly what supports or blocks a decision. A later phase may record human decisions. This minimizes manual searching while preserving the authority boundary.

## 4. Evidence inputs

The dossier builder may consume only governed, replayable evidence already established by predecessor phases:

1. COL-03B documentary-label hypotheses and their supporting evidence IDs;
2. COL-03C cross-document TAV.7 hypotheses, match state, conflict state and provenance refs;
3. TAV.7 primary-source observations;
4. COL-03D recovered historical CSV evidence, including:
   - `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv`;
   - `MATRICE_PILASTRI_27x5_v22.csv`;
   - `ABACO_TOPOLOGICO_TAV5_v11.csv`;
5. COL-03D historical semantic audit;
6. exact predecessor and source digests.

No new OCR, geometric inference, nearest-neighbour matching, label invention or coordinate snapping is part of COL-03E.

## 5. Critical historical constraint

The recovered `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv` contains 27 historical rows, but the relevant identity fields are not established as individual-column bindings. In the recovered source, rows carry the note:

`armatura di tipo documentata in TAV7; associazione al singolo pilastro non ancora dimostrata`

and fields such as `sigla_TAV5`, `ordine_TAV7` and `sezione_DOC` are blank in those rows.

Therefore:

- `id_predoc = N###` is historical derived identity, not a current `COL-OCC-*` identity;
- matching coordinates or historical status `VER` cannot bridge `COL-OCC-*` to `N###`;
- the 27×5 matrix cannot be joined to a governed occurrence unless an already-governed bridge exists;
- `VER` must remain a historical state, not a current truth assertion.

## 6. Dossier model

COL-03E produces exactly one dossier per governed occurrence.

Each dossier contains:

- `occurrence_id`;
- predecessor lineage and exact SHA;
- source/evidence references grouped by channel;
- candidate documentary labels already present in predecessor evidence;
- cross-document TAV.7 candidate state;
- ambiguity and contradiction state;
- historical evidence references only when an explicit governed bridge exists;
- unbound historical evidence summary when no bridge exists;
- semantic blockers;
- missing-evidence/gap reasons;
- review-readiness state;
- deterministic dossier digest;
- all authority flags false.

Historical rows must never be attached to an occurrence merely because coordinates, order, shape, section or expected structural behavior look compatible.

## 7. Review-readiness states

Each dossier ends in exactly one of:

### `READY_FOR_HUMAN_REVIEW`

Allowed only when:

- the occurrence has a single non-ambiguous cross-document candidate;
- every cited evidence reference is replayable and provenance-complete;
- no contradictory evidence exists;
- no historical semantic blocker is being used as if it were positive proof;
- the dossier clearly states that human approval is still required;
- no downstream authority flag is true.

### `AMBIGUOUS`

Used when more than one candidate or duplicate primary observation remains plausible.

### `CONTRADICTED`

Used when explicit evidence channels disagree materially.

### `BLOCKED_BY_HISTORICAL_SEMANTICS`

Used when a proposed identity depends on a historical row whose own note says the association is not demonstrated, or whose state is insufficient for identity use.

### `INSUFFICIENT_EVIDENCE`

Used when there is no unique candidate, no governed bridge, missing provenance, or only geometry/morphology-based compatibility.

Precedence is fail-closed:

`CONTRADICTED` > `AMBIGUOUS` > `BLOCKED_BY_HISTORICAL_SEMANTICS` > `INSUFFICIENT_EVIDENCE` > `READY_FOR_HUMAN_REVIEW`.

## 8. Explicit bridge rule

A historical row can enter an occurrence-specific evidence list only when a bridge is already represented by a governed predecessor evidence reference. COL-03E does not create bridge identities.

Without such a bridge, historical material may appear only under an `unbound_historical_context` summary and may not contribute to readiness.

This rule prevents accidental promotion of `N###`, 27×5 chain IDs or recovered TAV.5/TAV.7 associations into current occurrence identity.

## 9. Human review contract

COL-03E prepares, but does not execute, human adjudication.

A later gate must require a receipt containing at minimum:

- occurrence ID;
- exact dossier digest;
- explicit decision (`CONFIRM`, `REJECT`, `KEEP_UNRESOLVED`);
- selected candidate when confirming;
- reviewer identity or governed reviewer reference;
- decision timestamp;
- rationale or evidence references;
- exact source/predecessor SHA.

No receipt schema is activated for promotion in COL-03E; the above is a downstream interface constraint only.

## 10. Outputs

Derived evidence only, under:

`evidence/cew-col03e/`

Required outputs:

1. `identity-adjudication-dossiers.json`
2. `identity-adjudication-readiness.json`
3. `identity-adjudication-closure.json`

No COL-03B/C/D evidence artifact is rewritten.

## 11. Determinism

Outputs MUST be invariant to:

- input list ordering;
- historical CSV row enumeration where identity is not governed by row order;
- repeated exact-source replay;
- dictionary serialization order.

Dossier IDs/digests derive only from canonical serialized governed inputs.

## 12. Qualification conditions

COL-03E may qualify only when:

- the exact predecessor SHA is verified;
- exactly 22 dossiers exist with exact occurrence IDs;
- each dossier has one allowed readiness state;
- every occurrence-specific evidence reference has provenance;
- unbound historical rows remain unbound;
- historical semantic blockers are preserved;
- no `N###` identity is silently promoted to `COL-OCC-*`;
- no dossier has any downstream authority flag true;
- COL-03D and COL-03C regression suites remain green;
- outputs are deterministic across repeated builds.

Qualification means only `adjudication_dossiers_complete = true`.

It does **not** mean `structural_identity_authorized = true`.

## 13. Human workload objective

The output should let a reviewer open one occurrence and immediately see:

- what the system believes the candidate is, if any;
- which primary/documentary evidence supports it;
- what contradicts it;
- what historical material exists but remains unbound;
- why the case is or is not ready for a decision;
- exactly what remains to inspect manually.

The reviewer should not need to search the complete ZIP or reconstruct prior chat context.

## 14. Stop conditions

COL-03E stops after deterministic dossier/readiness production.

It MUST NOT continue into:

- receipt acceptance;
- support/structural identity promotion;
- vertical-chain assignment;
- family/section assignment;
- fixed-line/analytical-axis assignment;
- M0-S;
- M0-G;
- canonical CAD/BIM write;
- G2C/G3;
- EdiLus export;
- merge/deploy.

## 15. Success condition

COL-03E succeeds only when the system can say, reproducibly and auditably:

> Every governed column occurrence has a deterministic adjudication dossier that distinguishes primary evidence, derived historical context, ambiguity, contradiction, semantic blockers and explicit gaps; cases suitable for human review are identified without silently converting historical inference into structural identity, and all structural/canonical authority remains closed.
