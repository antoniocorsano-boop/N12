# ETW upper cantilever genealogy well-formedness rule v1

## Scope
Upper mansarda / terrace cantilever genealogy only. This rule supplements `FRAME_WELL_FORMEDNESS_GATE.md`.

## WF-13 ORIGINAL_CANTILEVER_AND_LATER_PROLONGATION

The present upper terrace/mansarda projection must be represented as a chronological structural genealogy, not as one timeless beam.

Required sequence:

`original upper support/node -> original DOC cantilever segment -> original free edge -> later RIF prolongation/extension -> present outer edge`

### Evidence partition

- `TAV-06E`: documents the original upper horizontal member/slab extending beyond the outer vertical-support line to a free edge (`DOC_GEOMETRY`).
- `TAV-05E`: documents the original reduced/set-back upper floor and terrace condition (`DOC_GEOMETRY`).
- `TAV-05S` topology: may localize structural axes/support lines, but G4 beam IDs MUST NOT be silently promoted to upper cantilever member IDs.
- `TAV-06S`: provides roof-level support presence and upper roof topology; it does not by itself identify the later cantilever prolongation.
- current field photograph: documents the present projecting terrace/mansarda edge (`PHOTO_RIF_PRIMARY`).
- user construction-history statement: later lengthening of the projecting beams to increase mansarda useful area (`RIF`).

### Mandatory constraints

1. The original support line and original free edge are separate properties from the present outer edge.
2. The original cantilever segment may be `DOC_GEOMETRY` even while its exact plan member ID or horizontal length remains unresolved.
3. The later prolongation must carry a separate chronology/evidence state (`RIF`) and may not inherit original reinforcement or section automatically.
4. No current edge may be back-projected as the original 1978–80 endpoint without documentary evidence.
5. No G4 beam segment may be renamed an upper cantilever beam merely because it lies on the same projected axis.
6. WING-A and WING-B may use the resolved plan support lines as localization aids; WING-C remains a composite/irregular transition until independently closed.
7. Analytical modelling must preserve at least two states when the later extension affects stiffness/load path materially: `ORIGINAL_AS_DESIGNED` and `CURRENT_AS_BUILT/ALTERED`.
8. If the connection between original cantilever and later prolongation is not documented, connection stiffness/reinforcement remains `ND`; no monolithic continuity assumption is promoted to DOC.

### Promotion criteria

A persistent upper-cantilever beam identity requires:

`resolved upper support node + source-bound plan axis + original cantilever evidence + explicit original free-edge relation`.

A persistent later-extension identity additionally requires:

`current geometry evidence + intervention genealogy + connection model or explicit ND/uncertainty treatment`.

Until these criteria are satisfied, use `GENEALOGY_CANDIDATE` / `PARTIAL`, not a canonical structural beam ID.

## Current application

See `ETW_UPPER_CANTILEVER_BEAM_GENEALOGY_CANDIDATES_v1.csv`.

- WING-A: strong support-line localization `P28-P29-P30`; exact upper member IDs unresolved.
- WING-B: strong support-line localization `P02-P10-P18`; exact upper member IDs unresolved.
- WING-C: no forced single support line; remains `BLOCKED_IDENTITY` for member-level genealogy.
