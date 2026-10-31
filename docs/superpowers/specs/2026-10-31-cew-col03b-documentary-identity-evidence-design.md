# CEW COL-03B — Documentary Identity Evidence

**Status:** DESIGN PROPOSED / IMPLEMENTATION NOT AUTHORIZED  
**Date:** 2026-10-31  
**Branch:** `docs/cew-col03b-documentary-identity-evidence`  
**Exact base:** `0d4a43cf02eadd2ab6f4b2641888395586c08a98` (PR #176, COL-03A qualified governed occurrence ledger)

## 1. Intent

COL-03B collects, normalizes and reconciles **documentary identity evidence** for the 22 stable `COL-OCC-*` occurrences closed by COL-03A.

It answers only this question:

> For each governed column occurrence, what documentary evidence exists that may later support a support/documentary identity, and what contradictions or gaps remain?

COL-03B does **not** promote any occurrence to structural identity, family, section, fixed line, vertical chain, canonical node, canonical geometry, G2C or G3 authority.

The governing transition is:

`COL-03A stable occurrence -> channel-separated documentary evidence -> candidate hypotheses -> cross-document reconciliation -> fail-closed evidence-collection closure`

The output is an evidence layer for later identity adjudication, not a structural model.

## 2. Why COL-03B exists

COL-03A solved a different problem: it established one neutral, exact-source-reconstructible record for each governed graphical occurrence and removed discovery-path ambiguity.

That stable subject set is now available:

- 24 governed graphical evidences in input;
- 22 neutral `COL-OCC-*` occurrences after the two human equivalence decisions;
- 0 conflicts;
- 0 missing evidences;
- 0 orphan occurrences;
- exact-source qualification PASS;
- all downstream structural/canonical authority still closed.

Identity work can therefore begin without allowing OCR, topology or historical expectations to redefine the occurrence set.

## 3. Goals

COL-03B must:

1. operate on exactly the 22 qualified `COL-OCC-*` occurrences from COL-03A;
2. collect documentary evidence independently for each occurrence;
3. keep every evidence channel explicit and provenance-complete;
4. distinguish internal text, intersecting text, nearby text, callouts, local topology and cross-document correspondence;
5. preserve high-resolution source readings as exact-source-derived evidence, not screenshots/conversation artifacts;
6. produce candidate documentary/support-label hypotheses only as non-authoritative hypotheses;
7. use historical topology/TAV.7/27x5 assets only as independent reconciliation evidence;
8. record contradictions instead of forcing a single identity;
9. permit a complete COL-03B closure even when some occurrences remain documentary-identity unresolved, provided evidence collection itself is complete and gaps are explicit;
10. leave all structural, canonical and promotion authority flags false.

## 4. Non-goals

COL-03B must not:

- add, delete or merge `COL-OCC-*` occurrences;
- rerun graphical occurrence discovery as an identity oracle;
- treat OCR text as authoritative by proximity alone;
- promote a nearby dimension, beam label or unrelated annotation to column identity;
- equate a documentary label with structural identity automatically;
- identify an occurrence directly with a historical `N###` node without independent documentary support;
- assume the historical 57 nodes are the complete geometric universe;
- promote the 27x5 matrix to authority over the source drawing;
- assign family, section, reinforcement, fixed line, analytical axis, offset or vertical chain;
- write canonical CAD/project geometry;
- authorize G2C, G3, EdiLus export, merge or deploy.

These remain successor operations.

## 5. Approaches considered

### A. Text/OCR-first identity

Read text around each occurrence and directly assign the most plausible support number.

**Rejected.** TAV.5 contains dense nearby dimensions and annotations; proximity alone is not identity evidence. This approach would recreate the text-binding failure mode that the governed occurrence pipeline was designed to avoid.

### B. Channel-separated evidence bundle per stable occurrence

For each `COL-OCC-*`, collect independent evidence channels, preserve provenance, derive zero or more non-authoritative identity hypotheses, and require independent discriminants before any later promotion.

**Selected.** This is the approach implied by the COL-03A successor boundary and by the current project decision: text, callouts, local topology and cross-document correspondence are gathered separately against a stable occurrence set.

### C. Historical topology/57-node/27x5-first identity

Map all 22 occurrences directly onto the historical topological assets and use those matches as identity.

**Rejected.** Historical artifacts are valuable reconciliation evidence, but the repository inventory explicitly warns that references beyond N057 exist and therefore the 57-node set cannot automatically define the whole geometric universe. Historical matches must be evidence, not authority.

## 6. Frozen input boundary

COL-03B is based exactly on:

`0d4a43cf02eadd2ab6f4b2641888395586c08a98`

The implementation must replay or consume the qualified COL-03A outputs and prove:

- `occurrence_count = 22`;
- occurrence IDs are exactly `COL-OCC-0001` through `COL-OCC-0022`;
- `occurrence_ledger_complete = true`;
- no COL-03A conflict remains;
- exact-source lineage for every occurrence is intact;
- the two human equivalence collapses remain unchanged;
- all structural/canonical authority is still closed.

COL-03B may not rewrite COL-03A artifacts.

## 7. Evidence channels

Each occurrence receives an evidence bundle with the following channels.

### 7.1 Internal text

Text whose geometry lies inside the governed occurrence representation.

Required fields per item:

- evidence ID;
- source page/transform;
- extraction method;
- token/raw transcription;
- normalized text bbox/polygon;
- relation to occurrence geometry;
- legibility/read state;
- exact-source reconstructibility;
- provenance digest.

Internal placement is strong locality evidence but is not by itself structural identity.

### 7.2 Intersecting text

Text geometry overlapping or touching the occurrence envelope.

It must remain distinct from internal text because fragmented OCR boxes, leaders or adjacent dimensions may intersect geometrically without naming the support.

### 7.3 Nearby text

Text within a bounded local neighborhood but not intersecting the occurrence.

Every item must record:

- normalized distance;
- direction/quadrant;
- whether a leader/callout relationship is present;
- competing nearby occurrences;
- reason it is retained as evidence.

Nearby text can propose a hypothesis but never confirm one alone.

### 7.4 High-resolution local source reading

A deterministic high-resolution read of the immutable TAV.5 source centered on the occurrence and its local annotation field.

The read must be reproducible from source SHA, page transform and normalized region. Generated crops are derivative artifacts only; authority remains the original source.

This channel may contain a human-reviewed transcription receipt when machine reading is insufficient.

### 7.5 Drawing labels and callouts

Explicit leaders, bubbles, arrows, symbols or annotation structures that graphically connect text to the occurrence.

This channel must preserve both the text and the connecting geometry. A callout without a proven graphical connection is downgraded to nearby text.

### 7.6 Local topology

Occurrence-local graphical relations visible on TAV.5, such as:

- adjacent beam/line intersections;
- relative position within a local bay;
- neighboring governed column occurrences;
- local span/order signature;
- local adjacency pattern.

This is a **local documentary signature**, not a canonical node or structural axis.

### 7.7 Cross-document correspondence

Independent evidence from other documentary/historical sources, including where available:

- `TAV7_PILASTRI.dxf`;
- `ABACO_TOPOLOGICO_TAV5_v11.csv`;
- `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv`;
- `MATRICE_PILASTRI_27x5_v22.csv`;
- other immutable historical DXF/register artifacts explicitly inventoried in the repository.

Every correspondence must state:

- source artifact and digest/version where available;
- candidate counterpart identifier;
- matching discriminants;
- conflicting discriminants;
- transformation/coordinate assumptions;
- status (`CANDIDATE`, `SUPPORTED`, `CONTRADICTED`, `NOT_APPLICABLE`).

Historical correspondence cannot promote identity by itself.

## 8. Evidence strength model

COL-03B must avoid a single opaque confidence score.

Each identity hypothesis is evaluated through explicit discriminants and channel support.

Proposed evidence classes:

- `DIRECT_GRAPHICAL_BINDING` — explicit callout/leader or unambiguous internal label bound to the occurrence;
- `INDEPENDENT_DOCUMENTARY_CORRESPONDENCE` — matching evidence from another governed document/artifact;
- `LOCAL_TOPOLOGY_MATCH` — local adjacency/span/order signature consistent with one candidate;
- `PROXIMITY_ONLY` — nearby text without binding geometry;
- `AMBIGUOUS_TEXT` — text could refer to more than one occurrence or annotation target;
- `CONTRADICTORY_EVIDENCE` — evidence channels support incompatible hypotheses;
- `NO_EVIDENCE` — channel explicitly inspected but no usable evidence found.

No evidence class in COL-03B authorizes support identity.

## 9. Documentary hypothesis model

COL-03B may create hypotheses but not identities.

A hypothesis object should contain at minimum:

```text
hypothesis_id
occurrence_id
hypothesis_kind
candidate_value
supporting_evidence_ids[]
contradicting_evidence_ids[]
independent_channel_count
independent_discriminants[]
state
promotion_authorized
notes
```

Allowed `hypothesis_kind` values should initially be narrow:

- `DOCUMENTARY_LABEL_CANDIDATE`
- `SUPPORT_NUMBER_CANDIDATE`
- `CROSS_DOCUMENT_COUNTERPART_CANDIDATE`

Required states:

- `UNSUPPORTED`
- `SINGLE_CHANNEL`
- `MULTI_CHANNEL_SUPPORTED`
- `AMBIGUOUS`
- `CONTRADICTED`

For every hypothesis:

`promotion_authorized = false`

COL-03B closure does not change that value.

## 10. Occurrence evidence-bundle record

Each of the 22 `COL-OCC-*` records should minimally contain:

```text
occurrence_id
col03a_ledger_digest
source_version_id
source_path
source_sha256
page_id
page_index
page_transform_id
primary_graphical_representation
internal_text_evidence[]
intersecting_text_evidence[]
nearby_text_evidence[]
high_resolution_read_evidence[]
callout_evidence[]
local_topology_evidence[]
cross_document_evidence[]
hypotheses[]
documentary_evidence_state
documentary_identity_resolution_state
conflict_state
missing_channels[]
exact_source_reconstructible
lineage_complete
support_identity_authorized
family_assignment_authorized
section_assignment_authorized
fixed_line_assignment_authorized
structural_identity_authorized
canonical_geometry_authorized
canonical_write_authorized
g2c_promotion_authorized
g3_authorized
notes
```

## 11. State semantics

### 11.1 Documentary evidence collection state

- `NOT_EVALUATED`
- `PARTIAL`
- `COMPLETE`

`COMPLETE` means every required channel has been evaluated and is either populated or explicitly recorded as `NO_EVIDENCE`/`NOT_APPLICABLE`.

### 11.2 Documentary identity resolution state

- `UNRESOLVED`
- `CANDIDATE_ONLY`
- `MULTIPLE_CANDIDATES`
- `CONTRADICTED`
- `READY_FOR_SUCCESSOR_ADJUDICATION`

`READY_FOR_SUCCESSOR_ADJUDICATION` means the evidence bundle is sufficiently discriminating for a later gate to adjudicate identity. It is not an identity assignment.

### 11.3 Conflict states

At minimum:

- `NONE`
- `AMBIGUOUS_TEXT_BINDING`
- `AMBIGUOUS_CROSS_DOCUMENT_MATCH`
- `CONTRADICTORY_DOCUMENTARY_EVIDENCE`
- `SOURCE_RECONSTRUCTION_FAILED`
- `COL03A_LINEAGE_DRIFT`
- `HISTORICAL_ARTIFACT_PROVENANCE_MISSING`

## 12. Text extraction rules

Text processing must be fail-closed and source-grounded.

1. OCR output is an observation, never authority.
2. Raw OCR text and normalized/transcribed text must both be preserved.
3. Character correction cannot silently change the raw observation.
4. A number token is not a support number merely because it is near a column.
5. Dimension strings, beam labels and reinforcement annotations must remain possible competing interpretations until excluded by context.
6. Human transcription receipts must reference the exact source region and preserve the prior machine observation rather than replacing it.
7. Repeated OCR/tool runs must be deterministic or record tool/version variance explicitly.

## 13. Local topology rules

Local topology is collected from the source page around each occurrence, not imported as canonical geometry.

It may describe relative/documentary facts such as:

- nearest governed occurrence to left/right/up/down;
- number and orientation of line/beam contacts;
- local bay ordering;
- relative span pattern when readable;
- boundary/interior/corner-like local context as a descriptive observation.

It must not emit:

- canonical node IDs;
- structural grid IDs;
- fixed-line assignments;
- analytical axes;
- cross-storey continuity.

## 14. Historical artifact safeguards

The historical inventory is useful but explicitly non-authoritative.

Required safeguards:

1. source artifact provenance must be recorded before use;
2. no historical file may overwrite source-derived evidence;
3. a candidate `N###` match remains a candidate unless independently discriminated;
4. the 57-node set cannot be assumed complete;
5. the 27x5 matrix is a reconciliation source, not a target the evidence must be forced to fit;
6. any transformation from historical coordinates to TAV.5 source coordinates must be explicit and testable;
7. unresolved many-to-one or one-to-many matches remain ambiguous.

## 15. Minimum independent-discriminant rule

COL-03B must not mechanically promote any hypothesis, but it should classify hypothesis maturity.

A hypothesis may reach `MULTI_CHANNEL_SUPPORTED` only when at least **two genuinely independent discriminants** support the same candidate, for example:

- explicit source callout + independent TAV.7 correspondence;
- internal label + local topology signature;
- high-resolution human transcription + independent historical cross-document match.

Two observations derived from the same OCR token or same underlying geometry do not count as independent discriminants.

This rule only classifies evidence maturity; it does not authorize identity.

## 16. Output artifacts

Proposed outputs:

### 16.1 Evidence ledger

`evidence/cew-col03b/documentary-identity-evidence-ledger.json`

Contains one evidence bundle for each of the 22 `COL-OCC-*` occurrences.

### 16.2 Hypothesis matrix

`evidence/cew-col03b/documentary-identity-hypotheses.json`

Contains all non-authoritative documentary/support/cross-document candidate hypotheses and their supporting/contradicting evidence.

### 16.3 Reconciliation report

`evidence/cew-col03b/documentary-identity-reconciliation.json`

Contains:

- occurrence count and coverage;
- evidence counts by channel/class;
- explicit no-evidence/not-applicable counts;
- hypothesis states;
- ambiguous/contradictory cases;
- historical artifact usage and provenance;
- deterministic replay digests.

### 16.4 Human review packet

`evidence/cew-col03b/documentary-identity-human-review.json`

Generated only for cases requiring human documentary interpretation. It must present exact-source local context and competing hypotheses without authorizing structural promotion.

### 16.5 Closure artifact

`evidence/cew-col03b/documentary-identity-evidence-closure.json`

May set:

`documentary_identity_evidence_collection_complete = true`

only when all collection/replay invariants pass.

It must also expose separately:

`all_occurrences_identity_resolved = false|true`

A COL-03B PASS does **not** require this second field to be true.

## 17. Closure rule

`documentary_identity_evidence_collection_complete = true` only if:

1. exact COL-03A qualified ancestry matches `0d4a43cf02eadd2ab6f4b2641888395586c08a98`;
2. all 22 `COL-OCC-*` occurrences are present exactly once;
3. no new/removed/merged occurrence exists;
4. each occurrence retains exact-source lineage and COL-03A geometry reference;
5. every required evidence channel has been evaluated per occurrence;
6. empty channels are explicit, not omitted;
7. every evidence item has provenance and reconstructible source location or explicit historical-artifact reference;
8. all hypotheses preserve supporting and contradicting evidence;
9. all ambiguities/conflicts remain visible;
10. historical artifacts are used only as independent reconciliation evidence;
11. deterministic replay reproduces evidence IDs, bundle membership and digests;
12. all support/structural/canonical/promotion authority flags remain false.

Identity resolution is not a closure invariant for COL-03B.

## 18. Human Review boundary

Human review is appropriate when exact-source reading cannot deterministically classify documentary evidence, for example:

- a token is legible to a human but unreliable to OCR;
- a leader/callout connection is graphically ambiguous;
- two nearby occurrences compete for one label;
- two cross-document candidates satisfy the same local signature;
- historical coordinate reconciliation exposes a genuine ambiguity.

Human review in COL-03B may decide only documentary evidence interpretation, such as:

- exact transcription of a token;
- whether a leader connects annotation to a specific occurrence;
- whether two documentary marks correspond;
- whether a candidate should remain ambiguous or contradicted.

It may **not** authorize family, section, vertical chain, canonical node, canonical geometry, G2C or G3.

## 19. Future implementation order

Implementation is not authorized by this design document. If approved, the plan should use RED -> GREEN in this dependency order:

1. RED: consume/replay exact COL-03A 22-occurrence ledger and freeze ancestry/authority boundary;
2. GREEN: COL-03B occurrence evidence-bundle skeleton with all authority false;
3. RED: deterministic local-region derivation around every occurrence;
4. GREEN: exact-source high-resolution local reader;
5. RED: channel classifier for internal/intersecting/nearby text;
6. GREEN: source-grounded text evidence extraction with raw/normalized separation;
7. RED: callout/leader evidence contract;
8. GREEN: deterministic callout evidence extraction without identity promotion;
9. RED: local topology evidence contract;
10. GREEN: occurrence-local topology signatures;
11. RED: historical artifact provenance and coordinate-reconciliation contract;
12. GREEN: candidate cross-document evidence from inventoried TAV.5/TAV.7/topology/27x5 assets;
13. RED: hypothesis independence and contradiction tests;
14. GREEN: non-authoritative hypothesis matrix;
15. RED: missing-channel / ambiguous / contradictory fail-closed cases;
16. GREEN: reconciliation and human-review packet generation;
17. RED: deterministic evidence-collection closure contract;
18. GREEN: closure artifact writer;
19. full COL-03A regression and exact-source replay;
20. human documentary review only where deterministic evidence remains ambiguous;
21. exact-SHA qualification.

## 20. Success criteria

COL-03B is successful when CEW can state reproducibly:

> Every qualified `COL-OCC-*` occurrence has a complete, channel-separated documentary evidence bundle; every text, callout, local-topology and cross-document observation is provenance-traced; candidate identities remain explicit hypotheses with contradictions visible; and no structural or canonical identity has been promoted.

## 21. Successor boundary

Only after COL-03B closes may a successor gate adjudicate **documentary/support identity** from the evidence bundles.

That successor must still keep distinct:

`documentary label -> support identity -> cross-document identity -> structural vertical identity -> family/section/fixed line -> canonical geometry -> G2C -> G3`

COL-03B itself stops before the first promotion.

## 22. Integration boundary

COL-03B is designed from the exact qualified head of PR #176:

`0d4a43cf02eadd2ab6f4b2641888395586c08a98`

The design branch is documentation-only. No product/experiment implementation, merge or deploy is authorized by this document.

**Design state:** READY FOR HUMAN APPROVAL / NO IMPLEMENTATION / NO MERGE / NO DEPLOY.
