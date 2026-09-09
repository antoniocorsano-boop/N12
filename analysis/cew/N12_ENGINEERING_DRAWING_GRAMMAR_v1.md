# N12 Engineering Drawing Grammar v1

## Purpose

Formalize the first explicit engineering-interpretation layer above governed PDF/vector/OCR extraction. This grammar is a reasoning aid, not engineering authority.

Canonical chain:

`SourceVersion -> Page -> EvidenceRegion -> GraphicPrimitive/TechnicalToken -> TechnicalRelation -> StructuralHypothesis -> HumanReview -> later governed promotion`

Extraction output never becomes structural truth directly.

## Authority boundary

- source document remains evidentiary authority;
- OCR/vector extraction authority: observation candidate only;
- grammar output: `STRUCTURAL_HYPOTHESIS_CANDIDATE`;
- automatic structural identity: forbidden;
- automatic canonical geometry: forbidden;
- canonical write: forbidden;
- engineering authority effect: NONE;
- contradictory evidence fails closed and remains visible.

## Core interpretation rules

1. `G-RC-001`: rectangle is not automatically a column.
2. `G-RC-002`: dimension text requires a governed dimension relation.
3. `G-RC-003`: reinforcement callout requires target binding.
4. `G-RC-004`: section size requires contextual binding.
5. `G-RC-005`: topology outranks visual proximity for identity.
6. `G-RC-006`: repeated conventions may create prototypes, not truth.
7. `G-RC-007`: cross-view agreement strengthens; conflict blocks.
8. `G-RC-008`: OCR confidence is not engineering confidence.
9. `G-RC-009`: historical drafting conventions remain hypotheses until verified.
10. `G-RC-010`: original SourceVersion/Page/EvidenceRegion remains evidentiary authority after reconstruction.

## Knowledge provenance

Promotion-relevant rules must declare one of:

- `PROJECT_LEARNED`
- `VERIFIED_REFERENCE`
- `METHOD_RULE`
- `HUMAN_TAUGHT_PROJECT_RULE`

## Held-out N12 validation after source recovery

On 2026-09-09 the original calculation-report photographs were recovered from `Cew foto originali.zip` and preserved with individual SHA-256 plus redundant archive.

Recovered primary sources:

- `RC-P10` -> `1788939776899.jpg` -> SHA-256 `3dc4528d3258d39827b245bc74ccff750ede140a0b2655a60c03241910451414`
- `RC-P13` -> `1788939776582.jpg` -> SHA-256 `7e2560fea42bbd05a8d633576af2352ea079b2565362b876fbc35bd793ede911`

Governed source bindings:

- `HO-RC-001` -> `N12-CALC-RELATION-RC-P13-V7E2560FE` -> `N12-CALC-RELATION-RC-P13-PAGE-001` -> `N12-CALC-RELATION-RC-P13-25X70-CANDIDATE`
- `HO-RC-002` -> `N12-CALC-RELATION-RC-P10-V3DC4528D` -> `N12-CALC-RELATION-RC-P10-PAGE-001` -> `N12-CALC-RELATION-RC-P10-G5-TRUNCATION`
- `HO-RC-003` remains bound to immutable TAV-05S plus PP-OCRv6 token evidence.

Authoritative held-out corpus: `data/benchmark/n12_engineering_grammar_regression_v2.json`.

Executable validator: `automation/validate_n12_engineering_drawing_grammar_v2.py`.

Validated fail-closed outputs:

- `HO-RC-001` -> `SECTION_DIMENSION_CANDIDATE_NEEDS_TARGET_BINDING`
- `HO-RC-002` -> `PRESERVE_DOCUMENTED_TRUNCATION`
- `HO-RC-003` -> `TECHNICAL_TOKEN_NEEDS_CONTEXT`

GitHub Actions result:

`KG-G5_HELD_OUT_N12_INTERPRETATION_PASS = PASS`

This PASS means the grammar correctly preserves uncertainty and non-promotion semantics on the three governed held-out N12 cases. It does not authorize autonomous structural interpretation, structural identity, canonical geometry/model writes, engineering decisions or professional authority.

## Integration with technical-PDF benchmark

PR #131 remains upstream for extractor evaluation.

Recommended pipeline:

- PyMuPDF for source/provenance baseline and native PDF geometry/text;
- pdfcadcore/ezdxf-oriented reconstruction as vector/CAD candidate;
- PP-OCRv6-medium as primary technical-token OCR candidate;
- eDOCr2 as engineering-drawing OCR comparator;
- PaddleOCR-VL where a more expensive semantic fallback is justified;
- this grammar as the non-promoting interpretation layer.

The benchmark should measure not only token accuracy but downstream relation recoverability.

## Preservation rule

No transient chat attachment may become promotion-relevant evidence before:

`original bytes -> SHA-256 -> redundant persistent archive -> SourceVersion -> Page -> EvidenceRegion`

Derived text, OCR, CSVs, historical handoffs, chat summaries and generated reports cannot replace original source bytes.
