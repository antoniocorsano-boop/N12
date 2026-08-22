# M1-S — G5 Human Review Report v1

Date: 2026-08-22
Branch: `work/m0-global-model`
Phase: `M1-S — residual section completion`
Scope: the 17 G5 beams whose topology is already `DOC` in `STOREY_BEAMS_G5_v1.csv` but whose section was `ND` at the M0-G handoff.

## Evidence basis

Primary graphical sources:
- `TAV-06S` — roof structural carpentry, immutable high-resolution archive, 300 dpi render used for visual review.
- `TAV-06A` — roof reinforcement drawing, immutable high-resolution archive, used as cross-check for known beam families.

Human evidence:
- qualified visual reading supplied by the project engineer/user on 2026-08-22 after inspection of targeted high-resolution crops.
- evidence class for the present report: `DOC_HUMAN_READ` where a dimension/type is explicitly read/confirmed from the drawing; `HUMAN_STRUCTURAL_INTERPRETATION` where the statement concerns structural function/modeling rather than a literal dimensional label.

This report does **not** modify or reopen the frozen M0-G geometry/topology baseline. It records M1-S evidence to be promoted through the M1 section-assignment gate.

## Confirmed readings

| Beam / zone | Human reading | Result for M1-S | Evidence state | Modeling note |
|---|---|---|---|---|
| `G5-B011` = 10–11 | `50×65 cm` | section closed | `DOC_HUMAN_READ` | confirmed on targeted detail |
| `G5-B012` = 11–12 | same section as 10–11 | `50×65 cm` | `DOC_HUMAN_READ` | explicitly confirmed by human review |
| `G5-B003` = 4–5 | same section as 2–10: `h=50 cm`, `b=30 cm` | `30×50 cm` | `DOC_HUMAN_READ` | orientation recorded as width 30, height 50 |
| `G5-B008` = 5–13 | `h=50 cm`, `b=30 cm` | `30×50 cm` | `DOC_HUMAN_READ` | orientation recorded as width 30, height 50 |
| `G5-B017` = 12–19 | **impluvium** | special member; ordinary rectangular-section assignment not forced | `HUMAN_STRUCTURAL_INTERPRETATION` | retain as special roof member; section dimensions still to be established if required by calculation model |
| `G5-B019` = 19–20 and adjacent triangular intersection | triangular area formed by 19–20 and the beam intersection is a **rigid zone** | beam section follows rectangular-beam rule outside the rigid zone; rigid triangle to be modeled explicitly in M1/EdiLus-FEM handoff | `HUMAN_STRUCTURAL_INTERPRETATION` | do not create a fictitious independent ordinary beam inside the rigid triangular zone |

## General rule supplied by human review

> All the **rectangular beams** in the reviewed G5 residual set are `30×50 cm`, except the explicitly identified 10–11 and 11–12 members, which are `50×65 cm`, and special/non-ordinary roof conditions such as the impluvium and rigid intersection zone.

Operational consequence for the residual set:

- `G5-B003` → `30×50 cm`
- `G5-B008` → `30×50 cm`
- `G5-B011` → `50×65 cm`
- `G5-B012` → `50×65 cm`
- `G5-B017` → `IMPLUVIUM`, section dimensions not yet promoted
- `G5-B018` → `30×50 cm` if retained as ordinary rectangular beam with plan offset
- `G5-B019` → `30×50 cm` for the ordinary beam portion, with a separate **rigid-zone** modeling condition at the triangular intersection
- `G5-B020` → `30×50 cm`
- `G5-B023` → `30×50 cm`
- `G5-B024` → `30×50 cm`
- `G5-B025` → `30×50 cm`
- `G5-B026` → `30×50 cm`
- `G5-B027` → `30×50 cm`
- `G5-B028` → `30×50 cm`
- `G5-B031` → `30×50 cm`
- `G5-B032` → `30×50 cm`
- `G5-B033` → `30×50 cm`

The entries marked by the general rule are **M1-S promotion candidates** and are not silently rewritten into the frozen M0-G handoff.

## Effect on the 17-section residual

Before human review:
- 17 G5 beam sections = `ND`.

After human review, at evidence level:
- 2 beams explicitly closed as `50×65 cm`: `B011`, `B012`;
- 14 residual ordinary rectangular beams can be assigned `30×50 cm` under the supplied general rule, including `B019` only for its ordinary beam portion outside the rigid intersection zone;
- 1 special member remains dimensionally unresolved: `B017` (impluvium).

Therefore the dimensional residual can fall from **17 to 1**, subject to the deterministic M1-S promotion validator confirming that every member classified under the general rectangular-beam rule is not a special non-ordinary roof element.

## Structural modeling implications

### Impluvium `B017` = 12–19
The member is not to be treated automatically as an ordinary rectangular G5 beam merely because neighboring beams are 30×50. Its role as an impluvium is now explicit. The next gate must determine the actual section/representation required by the calculation model.

### Rigid triangular zone at 19–20 / beam intersection
The triangular region identified by the human review is to be represented as a **rigid zone**. This is a modeling property for M1/EdiLus-FEM preparation, not a reason to alter the frozen M0-G connectivity unless a later formal `M0G-REOPEN` is triggered by new documentary evidence requiring geometric change.

Recommended implementation strategy:
- preserve M0-G node/member identities;
- assign `30×50 cm` to the ordinary `B019` beam portion if the deterministic section gate confirms ordinary rectangular classification;
- represent the triangular intersection through rigid offsets / rigid-link or equivalent rigid-zone treatment supported by the target solver;
- avoid double-counting stiffness or creating a fictitious extra beam.

## M1-S gate status after this review

`PASS_WITH_1_SECTION_RESIDUAL`

Remaining blocking-for-section-completeness item:
- `G5-B017` impluvium — section/analytical representation to be established.

Nonblocking modeling watch:
- `G5-B019` / triangular 19–20 intersection — rigid-zone implementation to be checked during EdiLus/FEM handoff.

M0-G status remains unchanged and frozen.
