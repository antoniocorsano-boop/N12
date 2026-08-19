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
- the photograph is compatible with horizontal members projecting beyond the upper vertical-support line, but hidden beam-column joints and reinforcement are not directly visible.

Evidence state: `PHOTO_RIF_PRIMARY` for visible geometry only.

### RIF_SUCCESSIVE_EXTENSION
User construction-history clarification, 2026-08-20:
- beams projected outward from the upper columns at the point where the terrace begins;
- these projecting beams were subsequently lengthened/extended to increase the useful floor area of the mansarde.

Evidence state: `RIF`.

The chronological extension is not promoted to `DOC` from the photograph alone.

## Structural interpretation

The upper level must carry two geometries separately:

1. `ORIGINAL_UPPER_FRAME`
   - upper columns / main vertical chains that continue to the reduced upper level and roof;
   - original beam/support nodes at the terrace-start line.

2. `LATER_ATTIC_EXTENSION`
   - outward beam prolongations beyond the original upper support/node line;
   - enlarged slab/floor footprint associated with the mansarda useful-area increase;
   - local perimeter/terrace geometry resulting from the extension.

Model genealogy:

`original upper column/node -> original projecting beam segment -> later beam extension/prolongation -> enlarged floor/slab edge`

The later portion must not be silently merged into the original 1978–80 beam genealogy.

## Well-formedness requirements

- the original support/node line must remain identifiable independently of the present outer edge;
- a beam extension is modeled as a property/genealogy override or connected later member, not as a new ordinary-floor span unless evidence proves that topology;
- the present terrace/mansarda outer boundary must not be used to relocate the original upper columns;
- no beam section, reinforcement diameter, splice/anchorage length or construction date is inferred from the photograph;
- where the extension crosses beyond a column line, the supporting path must remain explicit: `column/node -> original beam -> extension -> slab/perimeter`;
- the intervention is distinct from the separate first-level terrace addition already registered elsewhere in the eTwin.

## Current status

| Property | State | Basis |
|---|---|---|
| visible upper terrace/open setback | PHOTO_RIF_PRIMARY | field photograph |
| visible projecting horizontal edge/band | PHOTO_RIF_PRIMARY | field photograph |
| beams projecting from upper columns | RIF | user construction-history clarification |
| later lengthening of projecting beams | RIF | user construction-history clarification |
| purpose: increase mansarda useful area | RIF | user clarification |
| exact original beam endpoint | ND / BINDING_REQUIRED | reconcile photo + TAV-06S/architectural sources |
| exact present beam endpoint | ND / BINDING_REQUIRED | direct geometric binding required |
| extension length | ND | not measurable reliably from single oblique photo |
| beam section/reinforcement of extended portion | ND | not documented by this source |

## Reconciliation target

Use the photograph jointly with TAV-06S and architectural elevation/section sources to identify, for each photographed wing:

`upper column/support line -> terrace-start node -> original projection -> later extension -> current outer perimeter`.

Do not infer the same extension geometry for the other two wings until their evidence is checked.
