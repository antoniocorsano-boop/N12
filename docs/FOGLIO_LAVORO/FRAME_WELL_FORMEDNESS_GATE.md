# FRAME_WELL_FORMEDNESS_GATE

**Scope:** ETW-2 / structural eTwin reconstruction  
**Purpose:** prevent image-derived geometry from producing a non-well-formed framed structural model.

## Core invariant

A structural claim may be promoted from document-level evidence to a persistent framed-structure entity only through the chain:

`SOURCE -> OBSERVATION -> CLAIM -> POSITION/CHAIN -> STRUCTURAL ENTITY -> PROPERTY`

Image similarity, raster proximity or section-symbol resemblance alone MUST NOT establish persistent structural identity.

## Mandatory checks

### WF-01 NODE_CONNECTIVITY
Every framed structural entity must resolve to the structural graph:
- columns resolve to one persistent vertical chain / fixed-line position;
- beams resolve to two structural endpoints or an explicitly documented termination;
- intersections are represented as nodes, not graphic crossings.

### WF-02 BEAM_ENDPOINTS
A beam promoted to persistent identity must have:
- two resolved structural endpoints, OR
- one/two explicit termination reasons supported by evidence.

No orphan raster segment may become a beam.

### WF-03 COLUMN_VERTICAL_CHAIN
A column claim spanning adjacent levels must bind to a persistent `column_chain_id`.
The canonical source is `data/canonical/column_fixed_lines.csv`, whose chains preserve the historic 27x5 vertical-chain work.
A section change may be recorded as `DOC_RASTER` before chain binding, but may not become a canonical column property until the chain is resolved.

### WF-04 LEVEL_TO_LEVEL_IDENTITY
Identity across levels requires at least:
1. same resolved vertical chain / structural position;
2. topology compatible with surrounding frame;
3. source evidence at both levels.

Proximity or homography registration alone is insufficient.

### WF-05 NO_ORPHAN_STRUCTURAL_ELEMENT
No promoted column or beam may exist outside the framed graph.
Any element without a resolvable chain/endpoints remains `CANDIDATE`, `IDENTITY_UNRESOLVED` or `ND`.

### WF-06 FIXED_LINE_IS_NOT_SECTION_CENTROID
Historic fixed-line coordinates are geometric references only.
They must not be silently reinterpreted as section centroids or local section axes.
Section offsets/rotations remain independent properties and may be `ND`.

### WF-07 FLOOR_DIFFERENCE_IS_PROPERTY_CHANGE, NOT NEW ENTITY BY DEFAULT
A level-to-level section or geometry difference on the same resolved chain/entity is modeled as a property/topology override.
It must not create a new structural entity unless documentary/topological evidence proves element addition/removal/termination.

## Gate states

- `PASS` — all mandatory checks relevant to the claim are satisfied.
- `PARTIAL` — document property is verified but persistent structural identity is not fully resolved.
- `BLOCKED_IDENTITY` — no safe persistent chain/entity binding yet exists.
- `FAIL_WELL_FORMEDNESS` — proposed promotion would create an orphan, break connectivity, or contradict the framed graph.

## Promotion rule

`DOC_RASTER + INF_CONTROLLED_REGISTRATION` may establish a differential claim, but NOT persistent framed identity.

Promotion from `VER_PARZIALE` to persistent structural identity requires `FRAME_WELL_FORMEDNESS_GATE = PASS`.

## ETW-2 G2<->G3 initial application

Current differential rows `ETW2-G23-DIFF-001..004` contain readable section changes, but `persistent_entity_id=CANDIDATE`.
Therefore their well-formedness status is initially `BLOCKED_IDENTITY`, not `PASS`.

The next operation is to bind each candidate position to one of the 27 verified vertical chains in `data/canonical/column_fixed_lines.csv` using registered document position + surrounding topology + source evidence. No binding by proximity alone is allowed.
