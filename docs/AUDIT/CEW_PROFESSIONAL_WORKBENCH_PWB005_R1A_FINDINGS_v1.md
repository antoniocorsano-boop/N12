# CEW Professional Workbench — PWB-005-R1A Findings v1

Status: `R1A_COMPLETE_DIAGNOSTIC_DEFECT_ISOLATED`

Verified remediation candidate: `ddfd5826893702c3fc1299cde38c81bd7530b47a`

## Target cases

- `CEW-N12-REG-G01-R06`
- `CEW-N12-REG-G07-R07`

## Root cause

Both cases resolve to:

`FLOATING_POINT_CONTAINMENT_TOLERANCE`

### `CEW-N12-REG-G01-R06`

- strict R1 containment: `false`
- edge-tolerant containment (`0.01 pt`): `true`
- intersection-area deficit: `0.0155378622 pt²`
- left/top/right/bottom edge overhang: `0 / 0 / 0 / 0 pt`

### `CEW-N12-REG-G07-R07`

- strict R1 containment: `false`
- edge-tolerant containment (`0.01 pt`): `true`
- intersection-area deficit: `0.398352060467 pt²`
- left/top/right/bottom edge overhang: `0 / 0 / 0 / 0 pt`

## Provenance conclusion

The diagnostic reproduced no SourceVersion, Page, normalized-bbox or outside-page defect.

Therefore:

- canonical Page data are unchanged;
- canonical EvidenceRegion data are unchanged;
- transform identifiers are unchanged;
- no provenance repair is authorized or required by R1A.

The defect was solely in the derived R1 containment predicate: area comparison was too sensitive to floating-point rectangle arithmetic for full-width normalized regions.

## Remediation

R1 v1.1 replaces the area-equality containment test with explicit edge containment at `0.01 pt` tolerance.

The remediated exact-SHA run classifies all four governed regions as `RASTER` and no region as `REGION_MAPPING_ERROR`.

## Authority

`R1A_DIAGNOSTIC != PROVENANCE_REPAIR`

`PROVENANCE_REPAIR_AUTHORIZED = false`

`TECHNICAL_IDENTITY_AUTHORIZED = false`

`CANONICAL_WRITE_AUTHORIZED = false`

`HVA_EXECUTION_AUTHORIZED = false`
