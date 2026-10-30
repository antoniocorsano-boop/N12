# CEW-B01 — Beam-Type Approval Micro-Pilot Design

Status: `EXPERIMENT_ONLY / HUMAN_TYPE_APPROVAL_PENDING / NON_PROMOTING / G3_NOT_AUTHORIZED`

## Goal

Select and present one exact-source graphical example for each of two human-observed beam representations on TAV.5, so the human reviewer can approve the graphical types before any family induction or structural semantics are encoded.

## Human-observed distinction to validate

The reviewer distinguishes two graphical configurations:

1. **Proposed Type T1 — transverse slab-band configuration**
   - the local beam marker has a clear major axis;
   - the slab double lines are oriented **transversely / orthogonally** to that major axis;
   - proposed later semantic interpretation: *trave emergente*.

2. **Proposed Type T2 — longitudinal slab-band configuration**
   - the local beam marker has a clear major axis;
   - the slab double lines are oriented **in line / parallel** with that major axis;
   - proposed later semantic interpretation: *trave a spessore di solaio*.

The technical names above are human hypotheses for review. They are not executable classifications in this micro-pilot.

## Neutral graphical vocabulary

Until human approval, the system records only:

- `CROSS_AXIS_DOUBLE_BAND_CANDIDATE` — double-band evidence orthogonal to marker major axis;
- `LONG_AXIS_DOUBLE_BAND_CANDIDATE` — double-band evidence parallel to marker major axis;
- `NEGATIVE_CONTROL` — nearby configuration deliberately shown to prove boundary separation;
- `UNCERTAIN` — evidence insufficient or mixed.

No `BEAM`, `COLUMN`, `SLAB_SUPPORT`, `EMERGENT`, or `IN_SLAB` value is emitted as machine authority.

## Approval package

The package contains exactly four primary panels:

- **P1 — T1 candidate:** one clean exact-source example proposed as `CROSS_AXIS_DOUBLE_BAND_CANDIDATE`;
- **P2 — T2 candidate:** one clean exact-source example proposed as `LONG_AXIS_DOUBLE_BAND_CANDIDATE`;
- **P3 — negative control:** an `ALONE` or partial configuration that must not be accepted as either positive type;
- **P4 — topology control:** a support/junction or other mixed case that must not be accepted merely because it contains a rectangle and double lines.

Each positive type is shown in two views:

1. **source-only:** unmodified 300-dpi crop from the frozen TAV.5 source;
2. **review overlay:** marker/carrier/evidence overlay derived from the same exact raster.

The source-only view is the visual authority for Human Review.

## Human decisions

For P1 and P2 the permitted decisions are:

- `TYPE_APPROVED`
- `TYPE_REJECTED`
- `TYPE_UNCERTAIN`

For P3 and P4 the permitted decisions are:

- `NEGATIVE_CONTROL_CONFIRMED`
- `NEGATIVE_CONTROL_FAILED`
- `UNCERTAIN`

If either positive type is not approved, no prototype is created for that type.

## Selection policy

The micro-pilot does not tune thresholds to obtain one example per type.

Selection proceeds from the frozen exact-source evidence already produced by PR #169:

1. enumerate all current `RECT_PLUS_DOUBLE_TRANSVERSE_BAND` candidates;
2. export source-only crops for every candidate;
3. compare the orientation of visible slab-band lines with the marker major axis;
4. select the clearest one for each proposed type;
5. retain the other candidates as evidence but do not promote them.

If no clean example of one type exists in the current candidate set, the result is `TYPE_EXAMPLE_NOT_FOUND`; the system must not fabricate one.

## Provenance requirements

Every proposed example records:

- source SHA-256;
- page index;
- marker primitive ID;
- source marker geometry;
- review marker geometry;
- carrier orientation and track IDs;
- evidence source (`G1_LINE_TRACKS`, `RASTER_LOCAL_PROFILE`, or both);
- proposed neutral type;
- human decision and review state.

## Authority boundary

- graphical prototype creation: HUMAN APPROVAL REQUIRED;
- technical beam-type semantics: NOT AUTHORIZED;
- structural identity: NOT AUTHORIZED;
- canonical writes: NOT AUTHORIZED;
- G2C promotion: NOT AUTHORIZED;
- G3: NOT AUTHORIZED;
- merge: NOT AUTHORIZED.

## Success condition

The micro-pilot succeeds only when the reviewer can approve, individually and visually, one clean source example for each proposed graphical type and confirm that both controls remain outside those types.
