# CEW-COL-01 Number-Anchor Lesson v1

**Status:** ACTIVE  
**Date:** 2026-10-30  
**Lesson ID:** LL-021  
**Source:** CEW-COL-01 exact-source TAV-05S audit, PR #172, qualified implementation `46042603c6726b19a9038b518fc2899647ce4310`, workflow run `41064652715`.

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

Visual inspection of the review package also shows that several OCR numeric anchors are compatible with **dimension/annotation numbers near structural graphics**, not necessarily support identifiers centered in column footprints.

### Failure mode

The rule `number -> nearby rectangle -> column candidate` is under-constrained in a structural carpenteria because the same workarea contains many dimensions, sizes and annotations. Requiring the number first causes severe recall loss when OCR misses identifiers; accepting any nearby number also creates false associations with dimensional text.

The exact-source result therefore rejects the current **number-first OCR pipeline as a sufficient mandatory primary retrieval gate**. It does not establish that support identifiers are absent from the source drawing; graphical presence and OCR detectability are distinct questions.

### Durable rule

For future column recovery use:

`footprint/prototype candidate -> topology/local geometry -> text-inside-or-strongly-related evidence -> optional axis evidence -> Human Review`

not:

`any numeric token -> nearby geometry -> presumed support`.

Specific constraints:

1. symmetry axes remain optional evidence;
2. numeric identifiers remain useful, but only as relational evidence after/with a plausible object footprint;
3. text spatial relation must distinguish **inside/attached to footprint** from dimension text merely nearby;
4. historical support IDs may measure recall or select review witnesses but must never generate missing candidates;
5. OCR failure must remain visible and must not be repaired by hard-coded expected identifiers;
6. footprint/prototype retrieval should be the next primary search channel, with text and axes used to rank/explain candidates rather than to exclude them.

### Affected capabilities

- CEW-COL-01 and successor column-recovery tranche;
- TAV-05S/TAV-07 column acquisition;
- OA-2/OA-3 prototype and similarity reuse;
- future carpenteria reconstruction across TAV-03S/04S/05S/06S;
- support/text association grammar.

### Authority boundary

This lesson is process/architecture memory only. It does not identify any structural object, assign a section or fixed line, authorize canonical geometry/write, or promote any OCR observation to engineering fact.
