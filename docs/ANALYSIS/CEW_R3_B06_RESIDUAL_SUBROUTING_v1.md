# CEW R3 — B06 Residual Subrouting v1

Status: PROJECT ANALYSIS — CURRENT ROUTING BASIS  
Date: 2026-08-25  
Project: N12  
Work item: CEW-R3-SYNCHRONIZED-EVIDENCE-MAP-V0

## Purpose

Refine B06 from a single generic `SEARCHABLE_DOCUMENTARY_RESIDUAL` into explicit subroutes supported by the canonical M1A ledgers. The objective is to prevent repeated blind source searches while preserving useful source localization where it actually exists.

## Canonical basis

The M1A gate preserves three G4 transcription watches and seven column/storey residuals without analogy completion. The detailed ledgers provide the routing evidence:

- `M1A_TAV05A_BEAM_GROUP_INDEX_v1.csv` — group-to-G4-member scope and source locators;
- `M1A_TAV05A_GROUP_REINFORCEMENT_v1.csv` — row-level reinforcement transcription and unreadable/partial fields;
- `M1A_COLUMN_REINFORCEMENT_RESIDUALS_CURRENT_v1.csv` — seven column residuals, source-search state and reopen rules;
- `M1A_TAV06A_ROOF_GROUP_INDEX_v1.csv` — existing G5-B017 semantic-locator candidate.

No new engineering value is created by this analysis.

## G4 residuals — localization is productive, but only at group scope

### 1. Unknown bar label, L=1040

- source row: `T5A-G01-R06`;
- source: `TAV-05A`;
- locator: `P02`;
- known: straight bar, `L=1040`;
- unknown: quantity and diameter;
- G4 group member scope: `G4-B003, G4-B002, G4-B001, G4-B005, G4-B006, G4-B007`.

The source row is localized, but the canonical ledger does not provide a row-to-single-member station projection. Therefore CEW may navigate to the group context but must not bind the unreadable label to one member by assumption.

### 2. Partial sagomato

- source row: `T5A-G05-R04`;
- source: `TAV-05A`;
- locator: `P07-P08`;
- known: bent bar `2phi12` and explicitly written segments;
- unresolved: intermediate fall/continuation dimension;
- G4 group member scope: `G4-B022, G4-B008`.

The HiRes review may attempt to recover the missing written dimension. If it is not explicitly readable, the partial state remains canonical.

### 3. Unknown bar label, L=865

- source row: `T5A-G07-R07`;
- source: `TAV-05A`;
- locator: `P10`;
- known: straight bar, `L=865`;
- unknown: quantity and diameter;
- G4 group member scope: `G4-B030, G4-B039, G4-B044`.

The ledger explicitly says that quantity/diameter are not present in the current crop. This makes P10 a legitimate HiRes review target, not permission to transfer a neighbouring label.

### Routing decision for G4

The three G4 residuals are classified `LOCATOR_AVAILABLE_GROUP_SCOPE_ONLY`.

Permitted action:
- open the exact source locator in the Evidence Region Review workflow;
- preserve group/member scope in the UI;
- create a reviewed EvidenceSnippet only after an actual region is inspected.

Prohibited action:
- infer quantity/diameter from adjacent details;
- choose a single G4 member merely from drawing order or geometric proximity;
- complete the partial sagomato from graphical appearance without a source dimension.

## Seven column residuals — primary source search is already closed

The canonical column residual ledger marks all seven rows `CURRENT_PRIMARY_SOURCE_SEARCH_CLOSED`.

### G1 support 3

Section is 60x40, while TAV-07 I ordine has no 60x40 reinforcement family. The 50x40 family must not be forced.

Route: additional direct primary evidence or a newly verified I-order 60x40 family.

### G1 supports a, b, c, d

These are later terrace-added 30x30 supports. `T7-I-04` is a historical 30x30 family, but section compatibility does not establish the as-built reinforcement of later additions.

Route: direct as-built detail, reliable survey or primary documentation explicitly binding each added support.

### G3 supports 9 and 16

TAV-04S gives 40x40 sections. TAV-07 III ordine has two different 40x40 reinforcement families (`T7-III-01`, `T7-III-02`) and omits supports 9 and 16 from both numeric lists. Continuity across other orders does not uniquely discriminate the family.

Route: new direct member numbering/detail, clearer original-source evidence or independent primary evidence uniquely discriminating the family.

### Routing decision for columns

These seven residuals are not ordinary `SEARCHABLE_DOCUMENTARY_RESIDUAL` items anymore. They are `CURRENT_PRIMARY_SOURCE_SEARCH_CLOSED` and must not trigger repeated TAV-07 rereading unless a new evidence hypothesis appears.

## B06 aggregate state

B06 remains open and local-blocking for affected member checks, but its internal state is now mixed:

- 1 G5 semantic-locator candidate: `TAV06A P07 → G5-B017`;
- 3 G4 source-localized group-scope review targets;
- 7 column residuals with primary source search closed.

Therefore the B06 issue-level routing class becomes `MIXED_RESIDUAL_ROUTING`.

## Product implication

The Universal Residual Workspace must route at the residual/subclaim level, not only at issue level. A single engineering blocker can simultaneously contain:

- a reviewable source locator;
- a confirmed documentary gap;
- an as-built information gap requiring survey;
- a source-family conflict requiring discriminating evidence.

This is the mature behaviour CEW should preserve in future projects.
