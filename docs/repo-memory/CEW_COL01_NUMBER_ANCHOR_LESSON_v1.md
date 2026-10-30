# CEW-COL-01 Number-Anchor Lesson v1

**Status:** ACTIVE  
**Date:** 2026-10-30  
**Lesson ID:** LL-021  
**Source:** CEW-COL-01 exact-source TAV-05S audit, PR #172, qualified implementation `46042603c6726b19a9038b518fc2899647ce4310`, workflow run `41064652715`, followed by interactive Human Review on the generated C01-C09 atlas.

## LL-021 — Numeric identifiers are optional relational evidence, not a primary detector gate

### Observation

The first exact-source CEW-COL-01 audit tested a number-first recovery strategy on immutable TAV-05S.

Measured result against the historical 34-support G4 benchmark:

- 9 support-like OCR text anchors observed in the structural workarea;
- 6/34 benchmark identifiers matched at raw OCR level (`1, 4, 7, 9, 19, 30`), coverage 17.65%;
- only 5/34 identifiers also had plausible local footprint evidence (`1, 4, 7, 19, 30`), coverage 14.71%;
- identifier `7` was observed three times;
- elongated historical witnesses `18` and `23` were not retrieved;
- elongated witness `30` was retrieved only as `P3_NUMBER_PARTIAL_FOOTPRINT`.

Visual inspection and Human Review of the review package showed that several OCR numeric anchors are **dimension/annotation numbers near structural graphics**, not necessarily the support identifier inside a column footprint.

The Human Review supplied a stronger source-local discriminant for the current panel set: **column graphics are the rectangular footprints containing a numeric identifier internally; graphics without an internal number were rejected as columns in this review set.** This observation is source-local and must not be generalized to every carpenteria until tested on additional exact sources.

### Failure mode

The rule `number -> nearby rectangle -> column candidate` is under-constrained in a structural carpenteria because the same workarea contains many dimensions, sizes and annotations. Requiring the number first causes severe recall loss when OCR misses identifiers; accepting any nearby number also creates false associations with dimensional text.

A second failure mode was exposed by the first Human Review atlas: **a crop can contain a real numbered column while the machine panel identifier refers to a different nearby dimension value**. If the target object and target OCR token are not explicitly marked, a human can correctly recognize a column in the image while the system incorrectly records the nearby OCR number as that column's identifier.

The exact-source result therefore rejects the current **number-first OCR pipeline as a sufficient mandatory primary retrieval gate**. It does not establish that support identifiers are absent from the source drawing; graphical presence and OCR detectability are distinct questions.

### Durable rule

For future column recovery use:

`footprint/prototype candidate -> topology/local geometry -> internal-or-strongly-related text evidence -> optional axis evidence -> Human Review`

not:

`any numeric token -> nearby geometry -> presumed support`.

Specific constraints:

1. symmetry axes remain optional evidence;
2. numeric identifiers remain useful, but only as relational evidence after/with a plausible object footprint;
3. **text containment inside the footprint is a high-value cue and must be represented separately from nearby dimensional text**;
4. Human Review panels must make the machine target explicit: mark the proposed footprint and OCR anchor while retaining an unmodified source-only crop as evidence;
5. a panel-level observation that a column is visible must not automatically validate the machine OCR identifier shown in the panel header;
6. historical support IDs may measure recall or select review witnesses but must never generate missing candidates;
7. OCR failure must remain visible and must not be repaired by hard-coded expected identifiers;
8. footprint/prototype retrieval should be the next primary search channel, with text and axes used to rank/explain candidates rather than to exclude them.

### Human Review evidence from the current panel set

For C01-C09, applying the human criterion to the **visible graphics** gives:

- column graphic visible with internal numeric identifier: `C01`, `C02`, `C05`, `C06`;
- not a column under the current review criterion: `C03`, `C04`, `C07`, `C08`, `C09`.

These are **panel-level visual observations**, not machine-candidate identity receipts. The existing atlas does not make the exact proposed OCR anchor/footprint target explicit enough to bind those observations safely to machine identifiers. Candidate-level Human Review therefore requires a repaired target-explicit atlas before final promotion of any candidate decision.

### Affected capabilities

- CEW-COL-01 and successor column-recovery tranche;
- TAV-05S/TAV-07 column acquisition;
- OA-2/OA-3 prototype and similarity reuse;
- future carpenteria reconstruction across TAV-03S/04S/05S/06S;
- support/text association grammar;
- Human Review artifact design and candidate-target binding.

### Authority boundary

This lesson is process/architecture memory only. It does not identify any structural object, assign a section or fixed line, authorize canonical geometry/write, or promote any OCR observation to engineering fact.
