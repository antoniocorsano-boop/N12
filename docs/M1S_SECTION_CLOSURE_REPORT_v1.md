# M1-S — Section Completion Closure Report v1

Date: 2026-08-22
Branch: `work/m0-global-model`
Gate: `M1-S / SECTION ASSIGNMENT`
Decision: `PASS_WITH_WATCH`

## Scope

Close the section-assignment front for the frozen M0-G ordinary structural skeleton without reopening geometry or topology. The M0-G inventory remains 356 ordinary structural members: 229 beams and 127 vertical column segments.

## G5 residual resolution

The M0-G handoff carried 17 G5 beam-section `ND` values. The targeted TAV-06S/TAV-06A review and qualified human reading produced the current assignment ledger `data/canonical/M1S_G5_BEAM_SECTIONS_CURRENT_v1.csv`.

Results:
- G5 ordinary beams: 36/36 usable sections;
- G5 section `ND`: 0;
- `G5-B011` 10-11 = `50x65 cm`;
- `G5-B012` 11-12 = `50x65 cm`;
- reviewed residual rectangular roof beams = `30x50 cm` according to the qualified human reading and preserved source context;
- `G5-B017` 12-19 = `30x50 cm`, structural role `IMPLUVIO`, status `SUPPORTED` rather than `DOC` because TAV-06A does not directly label the 12-19 endpoints on the corresponding reinforcement detail;
- `G5-B019` 19-20 = `30x50 cm` for the ordinary beam portion; the adjacent triangular intersection is registered separately as a rigid-zone modeling watch.

## Rejected shortcut

The written values approximately `7.15` / `7.25` visible in the inclined-beam reinforcement details were tested against the frozen G5 axis coordinates and were **not** accepted as identifiers of the 12-19 and 19-26 support-to-support spans.

Using the canonical G5 support-core coordinates:
- 12-19 axis distance is about 6.30 m;
- 19-26 axis distance is about 7.52 m.

Therefore those TAV-06A values are not used as span-binding evidence. The B017 assignment remains `SUPPORTED`, based on the combined evidence chain: TAV-06S topology + qualified identification as impluvio + TAV-06A 30x50 inclined-beam family.

## Column-section watches

All 127 vertical column segments retain usable endpoint sections. Four segments preserve pre-existing evidence watches and are not promoted from `MIS` to `DOC`:
- `COL-052`, support 18, G2-G3;
- `COL-055`, support 21, G2-G3;
- `COL-086`, support 18, G3-G4;
- `COL-089`, support 21, G3-G4.

These watches are nonblocking for dimensional model construction.

## Rigid zone

`data/canonical/M1S_G5_RIGID_ZONES_v1.csv` records `G5-RZ-001`, the triangular rigid zone associated with the 19-20 intersection. Its exact polygon remains a solver-handoff watch. M0-G node/member identities and connectivity are unchanged; no fictitious extra beam is introduced.

## Deterministic gate summary

`data/canonical/M1S_SECTION_GATE_v1.csv` records:
- G5 beams: 36/36 usable, 0 ND, 1 evidence watch (`B017` SUPPORTED);
- G1-G4 beams: 193/193 usable, 0 ND;
- vertical column segments: 127/127 usable, 0 ND, 4 evidence watches;
- overall ordinary structural members: **356/356 usable sections, 0 ND**.

Overall decision: **`PASS_WITH_WATCH`**.

## Boundary to M1-M

M1-S is closed as the current section-assignment checkpoint. M0-G remains frozen. The next authorized front is `M1-M — materials`, which must independently establish concrete and reinforcing-steel properties and preserve distinctions among original documentary values, test/measurement results, reported values and assumptions. No material class or knowledge/confidence factor is to be invented from age, construction period or neighboring projects.
