# ETW upper cantilever genealogy gate v1

## Scope

Upper mansarda/terrace transition only. This gate is distinct from the later first-level terrace addition.

## Evidence hierarchy

1. **TAV-06E original section — DOC**
   - documents an original horizontal last-level member/slab projection beyond an upper vertical support line;
   - proves that an original cantilever/projection existed before the later enlargement;
   - does not by itself identify one transferable plan length for every wing.

2. **TAV-05S/TAV-06S support topology — DOC + level-presence rule**
   - resolves which column positions continue and which terminate;
   - provides candidate terrace-start/support lines in plan;
   - roof outline/overhang geometry must not be confused with terrace-floor cantilever length.

3. **Field photograph — PHOTO_RIF_PRIMARY**
   - shows the present mansarda wall set back from the present projecting terrace/edge;
   - does not expose hidden beam-column joints or reinforcement.

4. **User construction-history clarification — RIF**
   - original beams projected from the upper columns at the terrace-start line;
   - those beams were later lengthened to increase useful mansarda area.

## Mandatory genealogy

Every present upper projecting member/edge must be modeled through:

`original upper support/node -> original DOC cantilever segment -> later RIF extension -> present slab/perimeter`

Never:

`present outer edge -> assumed original beam endpoint`.

## Plan bindings currently admissible

### WING-A — high-confidence topology binding

- terminated outer positions: `P31, P32, P33`;
- continuing inner positions: `P28, P29, P30`;
- verified cross-transition edges: `P31-P28`, `P32-P29`, `P33-P30`;
- candidate original support/start line: `P28-P29-P30`;
- exact original cantilever endpoint/length: `ND`.

### WING-B — high-confidence topology binding

- terminated outer positions: `P01, P09, P17`;
- continuing inner positions: `P02, P10, P18`;
- verified cross-transition edges: `P01-P02`, `P09-P10`, `P17-P18`;
- candidate original support/start line: `P02-P10-P18`;
- exact original cantilever endpoint/length: `ND`.

### WING-C — geometry blocked

- termination set: `P08, P16, P21`;
- local topology does not reduce to one simple collinear start line;
- relevant verified edges include `P07-P08`, `P16-P08`, `P24-P16`, `P21-P13`, `P20-P21`, `P21-P22`, `P26-P21`;
- status: `BLOCKED_GEOMETRY` until setback/perimeter reconciliation closes.

## Promotion rules

An upper projecting beam may be promoted as an original persistent member only when:

- its start node/support line is resolved;
- its original endpoint is documentary or measured with controlled registration;
- its surrounding slab/frame topology is compatible;
- the later extension is kept as a separate genealogy/state.

A later extension may be represented with `RIF` geometry only when explicitly marked as later intervention; unknown section, reinforcement, splice and anchorage data remain `ND`.

## Current verdict

- existence of **original upper cantilever/projection**: `DOC`;
- WING-A and WING-B original start-line bindings: `VER_PARZIALE/HIGH`;
- WING-C single-line binding: `BLOCKED_GEOMETRY`;
- later lengthening for mansarda enlargement: `RIF`;
- exact extension lengths and reinforcement: `ND`.
