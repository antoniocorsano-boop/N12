# ETW-2 GATE REPORT — Floor Differential Reconstruction

**Gate:** ETW-2  
**Status:** IN PROGRESS  
**Parent gate:** ETW-1 = PASS  
**Branch:** `feat/structural-professional-workspace-r1`

## Objective

Resolve the former M0-S1B floor-difference block by applying the validated ETW-1 high-resolution document pipeline to the ordinary floor carpenterie:

- G1 → TAV-02S
- G2 → TAV-03S
- G3 → TAV-04S
- G4 → TAV-05S

No typical-floor equivalence is assumed.

## Completed in this ETW-2 increment

### Planning contract

Created `.asw/plans/etw2-floor-differential.md` with:
- evidence-first comparison model;
- explicit comparison statuses;
- residual-local blocking;
- prohibition on automatic TYPE_A/TYPE_B assignment;
- end-to-end first probe G4 ↔ G3.

### Task 1 implementation — Four DocumentMaps

Added `model/etwin/floor_differential.py`.

The module:
- loads TAV-02S..TAV-05S from the verified ETW registry;
- verifies that all required source documents are present;
- invokes the already validated ETW-1 `build_document_map()` with identical parameters for every floor;
- preserves source SHA256 and native page dimensions;
- persists one `document_map.json` per level document;
- uses 300 DPI, ~2000 px tiles and 10% deterministic overlap.

**Status:** IMPLEMENTED / EXECUTION EVIDENCE PENDING.

### Task 2 implementation — Structural registration

The same module generates `docs/FOGLIO_LAVORO/etwin_crops/ETW-2/floor_registration.json` after execution.

Registration policy:
- G4 is `coordinate_registration_only`;
- `typical_floor_assumption = false`;
- normalized PLAN-region coordinates are primary;
- native coordinates are preserved;
- source round-trip is required;
- identity from visual proximity alone is forbidden.

**Status:** IMPLEMENTED / EXECUTION EVIDENCE PENDING.

### CI execution harness

Added `.github/workflows/etw2-floor-differential.yml` to execute Task 1–2 against the repository-hosted original PDFs and validate the produced metadata.

The workflow:
- checks out the PR branch;
- installs `pypdfium2` and `Pillow`;
- executes `python -m model.etwin.floor_differential`;
- requires all four per-document `document_map.json` files;
- requires `docs/FOGLIO_LAVORO/etwin_crops/ETW-2/floor_registration.json`;
- writes an `execution_summary.json`;
- uploads metadata as a GitHub Actions artifact.

A path mismatch in the first workflow revision (`floor_differential/` vs the actual `ETW-2/` output directory) was identified before gate promotion and corrected in commit `f105aa3938e363dcdc8210db8a588b1f589d968e`.

**Execution observation:** no GitHub Actions workflow run is yet exposed for the latest PR commit through the connected Actions API. Therefore Task 1–2 remain `EXECUTION EVIDENCE PENDING`; absence of a visible run is not treated as PASS or FAIL.

## First probe

Target pair:

`G4 / TAV-05S ↔ G3 / TAV-04S`

Required chain before any differential claim can be verified:

`source PDFs → DocumentMaps → homologous region/tile → evidence crops → persistent entity/property resolution → comparison status`

A difference may only be classified as one of:
- MATCH
- SECTION_CHANGE
- GEOMETRY_CHANGE
- ELEMENT_ADDED
- ELEMENT_REMOVED
- POSITION_SHIFT
- IDENTITY_UNRESOLVED
- UNREADABLE

## Current residuals

| ID | Scope | Status | Blocking |
|---|---|---|---|
| ETW2-R01 | Execute four DocumentMaps and persist outputs | OPEN — harness ready, run not yet observed | Task 3 evidence sweep |
| ETW2-R02 | Execute normalized floor registration | OPEN — harness ready, run not yet observed | cross-level correspondence |
| ETW2-R03 | Read homologous G4/G3 structural region | OPEN | first verified floor difference |
| ETW2-R04 | Build Floor Difference Matrix | OPEN | floor signatures / TypicalFloorGroup |

## Gate status

**ETW-2 remains IN PROGRESS.**

No canonical structural data has been modified. No ND/INF evidence has been promoted. The former OCR tooling block is removed by ETW-1, and a reproducible repository-native execution harness now exists, but the floor-difference claim remains unresolved until high-resolution comparison evidence is actually produced.
