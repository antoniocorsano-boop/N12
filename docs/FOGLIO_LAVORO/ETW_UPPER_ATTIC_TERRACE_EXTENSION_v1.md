# ETW upper-attic terrace beam extension v1

## Scope

Photographed upper residential level / mansarda zone beneath the main pitched roof, distinct from the lower first-level terrace addition.

## Evidence chain

### PHOTO_OBSERVED_OVERHANG
Source: user-supplied upper-floor / stair-tower photograph (`ETW_UPPER_FLOOR_PHOTO_EVIDENCE_v1.md`).

Directly visible in the photographed wing:
- the mansarda/enclosed upper volume is set back from the outer horizontal edge below it;
- a continuous projecting horizontal edge/slab-beam band runs in front of the upper wall line and forms the terrace/open setback boundary;
- the projection is structurally/geometrically distinct from the upper wall line and from the pitched roof eaves above;
- hidden beam-column joints and reinforcement are not directly visible in the photograph.

Evidence state: `PHOTO_RIF_PRIMARY` for visible present geometry.

### DOC_ORIGINAL_UPPER_CANTILEVER
Source: original architectural/section drawing `SRC-TAV06E`, repository path `archive/documentazione_originaria/tavola6-2.pdf` / HiRes elevation-section artifact recovered by workflow `Render N12 HiRes Sources`, run `32262545586`, artifact `9368841495`.

Direct HiRes section reading shows:
- at the upper/sub-roof floor level, the horizontal structural floor/beam line extends outward beyond the outer vertical support/column line;
- this original projecting/cantilever portion is visible on both external sides of the section;
- therefore, an **original upper cantilever/projection already existed in the design**, before the later enlargement described by the user;
- the nearby vertical dimensions `20 / 200 / 20 / 220` belong to vertical section geometry and do **not** establish the horizontal cantilever length.

Evidence state: `DOC_GEOMETRY`.

### RIF_SUCCESSIVE_EXTENSION
User construction-history clarification, 2026-08-20:
- the upper projecting beams were subsequently lengthened/extended;
- the purpose of the extension was to increase the useful floor area of the mansarde.

Evidence state: `RIF`.

The later chronological extension is not promoted to `DOC` unless a subsequent drawing, survey or other documentary source is bound.

## Structural interpretation

The upper level must carry three geometries/genealogical stages separately:

1. `ORIGINAL_UPPER_SUPPORT_LINE`
   - upper columns / main vertical chains that continue to the reduced upper level and roof;
   - original beam/support nodes at the terrace-start line.

2. `ORIGINAL_PROJECTING_BEAM_SEGMENT`
   - documented by TAV-06E as a horizontal upper-floor/beam projection beyond the outer support line;
   - part of the original structural design genealogy.

3. `LATER_ATTIC_EXTENSION`
   - user-reported prolongation beyond the original projecting segment;
   - enlarged slab/floor footprint associated with the mansarda useful-area increase;
   - present terrace/mansarda perimeter may therefore lie farther outward than the original design edge.

Model genealogy:

`original upper column/node -> DOC original projecting beam segment -> RIF later beam extension/prolongation -> current enlarged floor/slab edge`

The later portion must not be silently merged into the original 1978–80 beam genealogy.

## Well-formedness requirements

- the original support/node line must remain identifiable independently of both the original cantilever edge and the present outer edge;
- the original projecting beam segment is part of the original structural genealogy and may be promoted only when its endpoints/support path are resolved;
- the later prolongation must be represented as a later intervention/property-genealogy override or connected member, not as an original ordinary-floor span;
- the present terrace/mansarda outer boundary must not be used to relocate the original upper columns;
- no beam section, reinforcement diameter, splice/anchorage length, horizontal extension length or intervention date is inferred from the photograph;
- where the extension crosses beyond a column line, the support path must remain explicit: `column/node -> original projecting beam -> later extension -> slab/perimeter`;
- the intervention is distinct from the separate first-level terrace addition already registered elsewhere in the eTwin.

## Current status

| Property | State | Basis |
|---|---|---|
| visible present upper terrace/open setback | PHOTO_RIF_PRIMARY | field photograph |
| visible present projecting horizontal edge/band | PHOTO_RIF_PRIMARY | field photograph |
| original beam/floor projection beyond upper support line | DOC_GEOMETRY | TAV-06E HiRes section |
| original projection present on both external sides of inspected section | DOC_GEOMETRY | TAV-06E HiRes section |
| later lengthening of projecting beams | RIF | user construction-history clarification |
| purpose: increase mansarda useful area | RIF | user clarification |
| exact original cantilever endpoint/length | ND / BINDING_REQUIRED | no reliable horizontal dimension yet bound |
| exact present beam endpoint | ND / BINDING_REQUIRED | current survey/geometry binding required |
| later extension length | ND | not measurable reliably from single oblique photo |
| beam section/reinforcement of later extended portion | ND | not documented by current evidence |

## Reconciliation target

Use TAV-06E as the original-section baseline, TAV-06S for roof/support plan binding, and the field photograph for current-state geometry.

Required chain for each inspected wing:

`upper column/support line -> original terrace-start node -> DOC original cantilever -> RIF later extension -> present outer perimeter`.

Do not infer the same later extension geometry for the other two wings until their current-state evidence is checked.
