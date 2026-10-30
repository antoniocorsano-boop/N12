# CEW Column Recognition Historical Reconciliation v1

**Status:** ACTIVE  
**Date:** 2026-10-30  
**Purpose:** prevent COL-01/COL-02 from rebuilding column-recognition concepts and capabilities already present in CEW history.

## Verified historical knowledge

### OAR/OA process ownership

PR #132 established the governed process:

`document acquisition -> object recognition -> prototypes/families -> similar search -> guided human validation -> canonical CAD object -> structural identity -> project material`

The first bounded pilot was `PILASTRI G4 / TAV-05S`. Detection/retrieval, family grouping, structural identity and canonical write were explicitly separate authority stages.

### G4 column register

The governed pilot input on PR #132 records 34 supports and five candidate families:

- `COL-G4-40X40`: 21 supports;
- `COL-G4-45X30`: 5 supports;
- `COL-G4-30X45`: 5 supports;
- `COL-G4-30X110`: supports `18`, `23`;
- `COL-G4-110X30`: support `30`.

The source is TAV-05S with SHA-256 `2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580`. Family assignment remained `SOURCE_DERIVED_CANDIDATE_GROUPING_ONLY`; human confirmation, structural identity and canonical write were false.

### Text was already a retrieval signal

PR #118/OA-3 assigned a dedicated similarity contribution to `ASSOCIATED_TEXT` while keeping similarity non-authoritative for object type, family, source position and structural identity.

### Prototype-led footprint search already existed

PR #136 established:

`support -> draw/adjust one correct example -> TEACH_THIS_IS -> FIND_SIMILAR across verified page -> inspect/review similar candidates -> resolve exceptions`

The page-wide search used footprint scale/aspect and rectangularity/envelope quality. It did not assign support identity or auto-confirm family membership.

The fallback detector also:

- suppressed long drawing axes before contouring;
- suppressed nested raw sub-contours;
- addressed a regression where a crossing axis could make an internal cell outrank the full column footprint.

This is direct historical evidence that axis-heavy/contour-local reasoning was already known to be unsafe.

### Geometry, axis and structural identity were already separated

Issue #2 requires geometric reference/fixed line, analytical axis and section footprint to remain distinct and prohibits deriving fixed-line geometry from the section barycenter alone.

Issue #5 keeps section assignment open where sigla/sezione/dettaglio are not unambiguous and explicitly prohibits assignment by analogy.

## Reconciliation decision

The current COL-01 number-first experiment must be interpreted as a bounded experiment that **failed to reuse enough historical column-acquisition knowledge**, not as the origin of the multi-cue recognition method.

The project-local invariant for the next tranche is:

`REUSE HISTORICAL OAR/OA FIRST -> FOOTPRINT/PROTOTYPE RETRIEVAL -> LOCAL TOPOLOGY -> TEXT-FOOTPRINT BINDING -> OPTIONAL AXIS EVIDENCE -> HUMAN REVIEW`

## New information contributed by COL-01

COL-01 adds two useful exact-source findings:

1. global/number-first OCR has insufficient recall for primary retrieval on the current TAV-05S pipeline;
2. the Human Review artifact can bind a nearby dimensional number to a crop containing a different numbered column, so machine OCR target and machine footprint target must be explicitly marked and reviewed as a pair.

The source-local Human Review of C01-C09 also observed that the accepted column graphics contain a numeric identifier inside the visible footprint, but this must remain a tested source-local discriminant until confirmed across additional carpenterie.

## Mandatory reuse gate before COL-02

Before any new COL-02 detector code:

1. inventory reusable OA/OAR interfaces and tests from PRs #118, #132 and #136;
2. identify the smallest reusable prototype/footprint-search slice;
3. preserve the 34-support/5-family register as benchmark evidence only;
4. implement only the residual capability: explicit `footprint <-> contained/internal text` association and target-explicit review;
5. requalify the reused slice on the current immutable TAV-05S source;
6. keep structural identity, section assignment, fixed lines and canonical write closed.

## Non-verified historical details

Some earlier conversational work may contain more specific visual observations (for example individual support labels or exact internal-number examples) that are not currently materialized in a repository artifact found by this reconciliation. Those details must not be promoted here as repository facts until their original source or durable receipt is recovered.
