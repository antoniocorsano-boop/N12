# FRAME_WELL_FORMEDNESS_GATE

**Scope:** ETW-2 / structural eTwin reconstruction  
**Purpose:** prevent image-derived geometry from producing a non-well-formed framed structural model.

## Core invariant

A structural claim may be promoted from document-level evidence to a persistent framed-structure entity only through the chain:

`SOURCE -> OBSERVATION -> CLAIM -> POSITION/CHAIN -> STRUCTURAL ENTITY -> PROPERTY`

Image similarity, raster proximity or section-symbol resemblance alone MUST NOT establish persistent structural identity.

The building is not required to be vertically prismatic. A well-formed framed model may contain documented terraces, setbacks, roof frames, ridge/eaves beams, deliberate column terminations and local framed extensions. These are modeled explicitly as structural topology, never repaired automatically into a fictitious regular frame.

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

A chain is NOT required to reach every upper level. A documented or otherwise evidence-supported termination is valid when represented by:
- `verticalEnd`;
- `presentAtLevels[]`;
- `terminationReason`;
- `evidenceRefs`;
- epistemic status.

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

### WF-08 ROOF_FRAME_TOPOLOGY
The roof is part of the framed structural system and must be modeled explicitly, not approximated as a flat terminal floor.
Required entities/checks:
- ridge beams (`TRAVE_DI_COLMO`) with resolved end/support nodes;
- eaves beams (`TRAVE_DI_GRONDA`) with resolved end/support nodes;
- roof-pitch/frame members connected consistently to ridge/eaves nodes;
- three roof ridges/wings preserved as distinct geometry until documentary correspondence is closed;
- no automatic extrusion of the ordinary-floor frame into the roof.

Current building-specific ridge/eaves requirement is `RIF` pending source-by-source binding.

### WF-09 FIRST_LEVEL_TERRACE_LOCAL_FRAME_EXTENSION
There is one terrace in this lower-level scope and it is located at the **first level**. It must be modeled as a local extension of the framed system, not as a detached terrace slab or as a ground-floor terrace.

Current user-reported configuration (`RIF`, documentary binding pending):
- added columns were introduced to support the terrace extension;
- added beams were introduced with the terrace frame;
- those added beams are connected/embedded into the corresponding pre-existing structural node;
- anchorage stubs/monconi at the node are reported as part of the connection detail.

Current partial source binding (`ETW_FIRST_LEVEL_TERRACE_RECEIVER_BINDING_v1.csv`):
- TAV-02S/G1 documents a local return/projection of 150 cm in the terrace candidate zone;
- the homologous TAV-03S/G2 geometry reduces to 70 cm, confirming a level-specific G1 geometry change;
- registered localization maps the zone near support `P15`, whose G1 section is DOC `40x50`;
- verified TAV-05S topology identifies `P23-P15` as the leading original receiving beam-line candidate;
- the visible 150 cm return joins the horizontal structural line before the visible support, so the exact insertion point MUST remain a separate anonymous/local node until pointwise evidence closes it;
- `P15` is therefore a support reference, not yet the exact terrace insertion node.

Well-formedness requirements:
1. every added terrace column must resolve to a support/base condition and to the terrace-frame node above;
2. every added terrace beam must resolve to explicit endpoints;
3. the connection to the original frame must resolve to the corresponding pre-existing node/member, never merely to a nearby raster location;
4. the original-frame node/member and the added-frame node must be represented as one structural connection or as explicitly related connection entities, depending on documentary evidence;
5. anchorage/monconi are connection/reinforcement properties, not independent frame members;
6. added members must remain distinct from the ordinary original-frame genealogy, while participating in the same well-formed global graph;
7. exact added member IDs, exact insertion node ID, sections, anchorage lengths/counts and construction chronology remain `ND`/`RIF` until source-bound;
8. nearest-support identity is forbidden: `local terrace insertion node = P15` is not allowed solely from registration distance;
9. current admissible partial model is `original receiving member candidate P23-P15 -> local/anonymous terrace insertion node -> added terrace beam(s)` with P15 retained as the nearest verified support reference.

The terrace extension therefore follows:

`existing frame member/node -> documented anchorage/interface -> added beam(s) -> added terrace node(s) -> added column(s)/supports`.

It MUST NOT be represented as:

`terrace outline -> invented beams/columns by geometric closure`.

### WF-10 SUBROOF_REDUCED_PLAN_AND_COLUMN_TERMINATION
The sub-roof / upper residential level is a reduced-plan floor with three apartments and terraces (`RIF`, pending documentary binding).
Consequently, absence of upper columns may be structurally correct.

Current user-reported constraints:
- three column positions are absent/terminate for each wing at the reduced upper/sub-roof configuration;
- TAV-06S/carpenteria di copertura represents the columns that actually continue up to the roof level;
- therefore, for a G4 support whose persistent position is resolved, absence of the homologous main-frame column in TAV-06S is positive evidence for termination below roof, subject to source registration and topology checks;
- TAV-06S may also contain one or more **local/additional stair-tower columns** that do not belong to the ordinary 27-chain main-frame genealogy.

Rules:
- these positions MUST NOT be generated by vertical extrusion;
- a lower-level chain may terminate below/at the sub-roof level without failing well-formedness if `terminationReason` and evidence are recorded;
- for main-frame supports, `present in TAV-06S` is treated as `CONTINUES_TO_ROOF_CANDIDATE` and `absent in TAV-06S at a resolved homologous G4 position` as `TERMINATES_BELOW_ROOF_CANDIDATE`;
- neither state becomes canonical until persistent chain identity and local topology are resolved;
- columns visible in TAV-06S that do not map to a G4/main-frame chain are NOT forced into the 27-chain system: classify them as `STAIR_TOWER_COLUMN_CANDIDATE` / `LOCAL_UPPER_COLUMN_CANDIDATE` until bound;
- the exact three-per-wing chain identities must be resolved from carpenteria/roof/sub-roof evidence before becoming canonical.

### WF-11 TOPOLOGY_VARIANT_PRECEDENCE
When ordinary-floor regularity conflicts with documentary evidence for first-level terrace extension, setback, roof or column termination, the documented local topology variant prevails.

Order of reasoning:
`persistent frame position -> level presence -> local topology override -> section/property`.

Never:
`typical floor -> vertical extrusion -> force unmatched geometry to fit`.

### WF-12 ROOF_COLUMN_POPULATION_SPLIT
TAV-06S must be resolved into two distinct structural populations:

1. `MAIN_FRAME_ROOF_CONTINUATION`
   - has a homologous resolved G4/main-frame chain;
   - represents continuation of an existing column to roof;
   - may inherit vertical genealogy, but not section/offset automatically.

2. `STAIR_TOWER_OR_LOCAL_UPPER_COLUMN`
   - has no safe homologous ordinary G4/main-frame chain, OR belongs to the stair-tower structural subsystem;
   - must receive its own local genealogy, support path and section evidence;
   - must never be merged into the 27 ordinary chains merely because it lies nearby.

Any TAV-06S support that cannot yet be placed in one of these two populations remains `IDENTITY_UNRESOLVED`.

## Gate states

- `PASS` — all mandatory checks relevant to the claim are satisfied.
- `PARTIAL` — document property is verified but persistent structural identity is not fully resolved.
- `BLOCKED_IDENTITY` — no safe persistent chain/entity binding yet exists.
- `EXPECTED_TERMINATION_CANDIDATE` — absence at an upper level is compatible with the reduced-plan/roof topology but exact chain termination is not yet document-bound.
- `CONTINUES_TO_ROOF_CANDIDATE` — homologous roof-level column is present, but persistent binding still requires topology/source validation.
- `STAIR_TOWER_COLUMN_CANDIDATE` — roof-level column is likely part of stair tower/local upper subsystem rather than an ordinary main-frame continuation.
- `FAIL_WELL_FORMEDNESS` — proposed promotion would create an orphan, break connectivity, or contradict the framed graph.

## Promotion rule

`DOC_RASTER + INF_CONTROLLED_REGISTRATION` may establish a differential claim, but NOT persistent framed identity.

Promotion from `VER_PARZIALE` to persistent structural identity requires `FRAME_WELL_FORMEDNESS_GATE = PASS`.

For upper-level absence, promotion to a canonical termination additionally requires:
`resolved chain + TAV-06S absence at homologous position + local roof/terrace topology + terminationReason`.

For roof-level continuation, promotion additionally requires:
`resolved G4 chain + homologous TAV-06S support + compatible surrounding topology`.

For stair-tower/local upper columns, promotion additionally requires:
`roof-level support evidence + stair-tower/local topology + independent genealogy/support path`.

For first-level terrace added members, promotion additionally requires:
`resolved original receiving node/member + resolved added member endpoints + support path + source evidence for connection/anchorage`.

A terrace insertion point may remain an anonymous/local structural node while its receiving original member is partially resolved. It MUST NOT inherit the nearest P-ID until pointwise node identity is independently demonstrated.

## Building-specific topology constraints currently carried forward

| Constraint | Current state | Modeling consequence |
|---|---|---|
| Roof has ridge and eaves beams | RIF / source binding pending | Explicit roof-frame beams; no flat-floor surrogate |
| Three roof ridges / three wings | RIF/DOC context, exact entity binding pending | Preserve three independent roof-frame branches |
| First-level terrace is a local frame extension | DOC local G1 geometry + MIS registration + RIF chronology / receiver partial | Receiving original beam-line candidate `P23-P15`; P15 support reference; exact insertion node remains local/ND |
| Sub-roof/upper level has three apartments with terraces | RIF | Reduced-plan `FloorVariant`; no ordinary-floor extrusion |
| Three upper columns absent/terminated per wing | RIF | exact chain IDs pending; TAV-06S presence/absence now used as direct level-presence evidence |
| TAV-06S may contain additional stair-tower columns | RIF | split roof supports into main-frame continuations vs stair-tower/local upper columns |

## ETW-2 G2<->G3 initial application

Current differential rows `ETW2-G23-DIFF-001..004` contain readable section changes, but `persistent_entity_id=CANDIDATE`.
Therefore their well-formedness status is initially `BLOCKED_IDENTITY`, not `PASS`.

The next operation is to bind each candidate position to one of the 27 verified vertical chains in `data/canonical/column_fixed_lines.csv` using registered document position + surrounding topology + source evidence. No binding by proximity alone is allowed.

The lower/first-level pass has now partially resolved the terrace receiver genealogy to `P23-P15` as the leading original receiving-member candidate with `P15` as local support reference; the exact insertion node remains unresolved and must not be collapsed onto P15. The upper-level/roof pass must classify every TAV-06S support as main-frame continuation, stair-tower/local-upper column, or unresolved, and determine which ordinary chains terminate below roof.
