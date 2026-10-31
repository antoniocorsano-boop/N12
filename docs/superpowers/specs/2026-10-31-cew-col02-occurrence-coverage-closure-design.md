# CEW COL-02 Occurrence Coverage Closure — Design

## Intent

Close the bounded COL-02 graphical occurrence-coverage state only after proving that every successor reconciliation item has a terminal graphical outcome and that no human-added point remains unbound. This tranche does not reopen detection, geometry reconstruction, support identity, text identity, structural identity or canonical geometry.

## Frozen evidence

- Frozen neutral proposal producer: 611 proposals; original `COL02-FP-*` ID space immutable.
- Residual reconciliation replay SHA-256: `b68526f71e77a072b0849d2d3cd2fcab886b03c86a99681717d7aee5cd13bf3c`.
- Reviewed whole-symbol repair manifest file SHA-256: `e688c22753d8804edfdded8e9f89651c60b7a864a016b400a027d708329b1228`.
- Residual reconciliation review: `governance/cew-col02/COL02_RESIDUAL_RECONCILIATION_HUMAN_REVIEW_v1.json`.
- Final whole-symbol graphical review: `governance/cew-col02/COL02_AXIS_AWARE_WHOLE_SYMBOL_HUMAN_REVIEW_v2.json`.

## Closure rule

`occurrence_coverage_complete` may become `true` only in a new closure artifact when all of the following are simultaneously true:

1. the fresh exact-source residual reconciliation manifest has the frozen replay SHA-256 and `residual_candidate_review_complete = true`;
2. its successor task set is exactly R01–R06 and contains no `HUMAN_POINT_UNBOUND` item;
3. all four human-added points resolve to existing frozen proposals;
4. the residual reconciliation Human Review receipt contains exactly one terminal decision for R01–R06;
5. R02 / `COL02-FP-0106` is terminally rejected as `MISLOCALIZED_NOT_COLUMN`;
6. R01, R03, R04, R05 and R06 are the five repair-eligible fragmented symbols;
7. the fresh exact-source repair manifest is byte-identical to the reviewed repair manifest digest above, has five ready repairs and zero unresolved repairs;
8. the final graphical review v2 maps exactly those five source candidates to five `PASS` decisions;
9. all professional/canonical authority flags remain false.

Any missing item, lineage mismatch, unbound point, unresolved repair, non-PASS graphical decision, task-set drift or authority drift fails closed and keeps coverage incomplete.

## Output

Create `evidence/cew-col02/footprint-text-binding/col02-occurrence-coverage-closure.json` containing:

- schema and exact-source lineage;
- frozen replay/digest checks;
- six successor task outcomes;
- four human-point bindings;
- five final repair decisions plus the single rejected target;
- `occurrence_coverage_complete = true` only when the closure rule passes;
- all downstream authority flags explicitly false.

Historical reconciliation and repair manifests remain unchanged with their original `occurrence_coverage_complete = false` values. The closure artifact is the only authoritative statement that the bounded graphical occurrence-coverage gate is closed.

## Non-goals

- no new detector or similarity search;
- no new Human Review;
- no mutation of the 611 proposal payload;
- no support number, family, section, fixed-line or structural identity;
- no canonical geometry/write;
- no G2C/G3;
- no merge or deploy.
