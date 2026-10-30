# CEW-COL-01 Number-Anchor Lesson v1

**Status:** ACTIVE  
**Date:** 2026-10-30  
**Lesson ID:** LL-021  
**Source:** historical OAR/OA work plus CEW-COL-01 exact-source TAV-05S audit, PR #172, qualified implementation `46042603c6726b19a9038b518fc2899647ce4310`, followed by interactive Human Review on the generated C01-C09 atlas.

## LL-021 — COL-01 confirms historical multi-cue column grammar and exposes a target-binding defect

### Historical reconciliation

COL-01 did **not** originate the project idea that columns must be recognized from multiple cues rather than from axes or text alone. Repository history already contained the relevant building blocks:

- PR #132 established the governed Object Acquisition process `document acquisition -> object recognition -> prototypes/families -> similar search -> guided human validation -> canonical CAD object -> structural identity -> project material`, with the G4/TAV-05S column pilot as the bounded first pilot;
- the governed G4 pilot contains 34 supports in five candidate families, including elongated `30x110` supports `18` and `23` and `110x30` support `30`; family membership remained candidate evidence, not structural identity;
- PR #118/OA-3 already included `ASSOCIATED_TEXT` as an explicit similarity signal while forbidding similarity from creating identity;
- PR #136 already used the human-taught footprint as the primary retrieval prototype, with page-wide `FIND_SIMILAR`; its fallback detector explicitly suppressed long drawing axes and fixed an `internal cell` versus `full column footprint` defect;
- issues #2 and #5 already required geometric reference, analytical axis and section footprint to remain distinct and prohibited section/fixed-line promotion by analogy.

Therefore the durable project lesson is also a **reuse lesson**: before creating another column detector, reconcile historical OAR/OA capabilities and port the smallest qualified slice needed by the active exact-source task.

### What COL-01 actually added

The first exact-source COL-01 audit tested a **number-first OCR pipeline** on immutable TAV-05S. Measured against the historical 34-support benchmark:

- 9 support-like OCR text anchors were observed;
- 6/34 benchmark identifiers matched at raw OCR level (`1, 4, 7, 9, 19, 30`), coverage 17.65%;
- only 5/34 also had plausible local footprint evidence (`1, 4, 7, 19, 30`), coverage 14.71%;
- elongated witnesses `18` and `23` were not retrieved;
- witness `30` was retrieved only as `P3_NUMBER_PARTIAL_FOOTPRINT`.

This rejects only the current **number-first OCR pipeline as a sufficient mandatory primary retrieval gate**. It does not establish that identifiers are absent from the drawing.

The genuinely new finding is the **target-binding defect**: a crop may contain a true numbered column while the machine panel identifier refers to a different nearby dimensional value. A human can correctly recognize the column but the system can still bind the wrong number to it.

### Human Review evidence from C01-C09

For the visible graphics in the current panel set:

- column graphic visible with a numeric identifier inside the footprint: `C01`, `C02`, `C05`, `C06`;
- not a column under this source-local criterion: `C03`, `C04`, `C07`, `C08`, `C09`.

These are panel-level graphical observations, **not machine-candidate identity receipts**. The current atlas does not explicitly mark the exact proposed OCR anchor and exact proposed footprint strongly enough to bind the human decision safely to a machine identifier.

### Durable rule

For the successor column-recovery tranche, reuse the historical prototype-led architecture and apply the sequence:

`footprint/prototype candidate -> topology/local geometry -> text contained inside or strongly bound to the footprint -> optional axis evidence -> target-explicit Human Review`

not:

`any numeric token -> nearby geometry -> presumed support`.

Specific constraints:

1. symmetry axes are optional supporting evidence;
2. text is relational evidence and must not create structural identity;
3. containment of text inside a plausible footprint is a high-value source-local cue and must be distinguished from nearby dimensions/annotations;
4. the Human Review artifact must mark separately the machine footprint target and the machine OCR target while preserving an unmodified source-only crop;
5. historical support IDs/counts/families may benchmark recall but must never generate missing candidates;
6. the 34-support/5-family register is reusable project evidence, not a production oracle;
7. fixed lines, analytical axes, section dimensions and structural identity remain downstream governed questions;
8. new code is justified only for the residual gap after OA/OAR reuse reconciliation.

### Authority boundary

This lesson is process/architecture memory only. It does not identify a structural object, assign a section or fixed line, authorize canonical geometry/write, or promote OCR observations to engineering facts.
