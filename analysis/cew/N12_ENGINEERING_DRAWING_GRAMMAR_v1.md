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

## 1. Evidence primitives

The grammar consumes only source-bound primitives with page coordinates and extractor provenance.

### Graphic primitives

- LINE / POLYLINE / CURVE / RECTANGULAR_ENVELOPE
- TEXT_RUN / TEXT_BOX
- ARROW_OR_LEADER_CANDIDATE
- DIMENSION_LINE_CANDIDATE
- EXTENSION_LINE_CANDIDATE
- HATCH_OR_FILL_CANDIDATE
- AXIS_OR_GRIDLINE_CANDIDATE
- CLOSED_SECTION_CONTOUR_CANDIDATE
- REBAR_STROKE_CANDIDATE
- STIRRUP_CONTOUR_CANDIDATE

Primitive names are descriptive, not semantic truth.

## 2. Technical tokens

Tokens are normalized without discarding the source string.

Candidate classes:

- numeric dimension: `25`, `70`, `3.20`, `970`;
- diameter/rebar: `Ø14`, `Φ14`, OCR-normalized variants;
- multiplicity: `2Ø14`, `10Φ14`;
- spacing: `Ø8/15`, `staffe Ø8 passo 15`;
- section dimensions: `25x70`, `40x40`, `80x20`;
- length: `L=970`, equivalent source notation retained;
- grid/frame labels: numeric/alphabetic/alphanumeric identifiers;
- elevation/level tokens;
- element/detail references.

Every normalized token preserves:

`raw_text, normalized_text, bbox, page_id, source_version_id, extractor, extractor_version, confidence`.

## 3. Relations

No technical meaning is assigned from token shape alone. Candidate relations are explicit objects:

- `NEAR`
- `ALIGNED_WITH`
- `BETWEEN_EXTENSION_LINES`
- `LEADER_POINTS_TO`
- `INSIDE_CONTOUR`
- `CROSSES`
- `PARALLEL_TO`
- `PERPENDICULAR_TO`
- `REPEATS_WITH`
- `BELONGS_TO_DETAIL_REGION`
- `CONTINUES_ACROSS`
- `CORRESPONDS_ACROSS_VIEWS`

Each relation records evidence and alternative interpretations.

## 4. Interpretation rules

### G-RC-001 — rectangle is not automatically a column

A rectangular closed contour alone cannot assign `COLUMN`. It may represent a column footprint, beam section, detail frame, opening, annotation box, foundation element or another object. Structural type requires contextual evidence and/or explicit human teaching.

This rule preserves a correction learned during N12 development, where superficially similar rectangles could represent beam sections rather than columns.

### G-RC-002 — dimension text requires a dimension relation

A number close to an element is not an element dimension unless the system can establish a compatible relation to dimension/extension geometry or another governed reference.

### G-RC-003 — reinforcement callout requires target binding

A token such as `2Ø14 L=970` is initially a `REBAR_CALLOUT_CANDIDATE`. Promotion to a reinforcement assertion requires a governed target relation to a bar/group/detail plus compatible local geometry.

### G-RC-004 — section size requires contextual binding

A token such as `25x70` may become `SECTION_DIMENSION_CANDIDATE`, but cannot be assigned to a beam/column until its target element/detail is resolved.

### G-RC-005 — topology outranks visual proximity for identity

Visual proximity or similarity alone cannot establish structural identity. Identity hypotheses must be checked against topology, alignment, repeated framing logic, cross-view correspondence and project evidence.

### G-RC-006 — repeated conventions can create a prototype, not truth

Repeated graphic patterns may create a project-local prototype/family candidate. They do not automatically establish semantic or structural identity.

### G-RC-007 — cross-view agreement strengthens, conflict blocks

Agreement between plan, frame/elevation, section/detail and calculation documentation strengthens a hypothesis. Material disagreement creates an explicit contradiction requiring review; the system must not silently reconcile it.

### G-RC-008 — OCR confidence is not engineering confidence

OCR confidence measures recognition quality only. Engineering confidence must be separately derived from source quality, geometric relation, contextual consistency, cross-view agreement and human validation state.

### G-RC-009 — drawing-era conventions are hypotheses

Historical drafting conventions may guide candidate generation but cannot be assumed universal. Project-local evidence and verified references take precedence.

### G-RC-010 — source authority is retained after technical reconstruction

A CAD/technical reconstruction remains a derived operational representation. The original governed SourceVersion/Page/EvidenceRegion remains the evidentiary authority.

## 5. Structural hypothesis object

Minimum proposal contract:

```json
{
  "hypothesis_id": "...",
  "hypothesis_type": "BEAM|COLUMN|SLAB|FOUNDATION|REBAR|GRID|DIMENSION|OTHER",
  "source_bindings": [],
  "supporting_tokens": [],
  "supporting_primitives": [],
  "relations": [],
  "cross_view_support": [],
  "contradictions": [],
  "knowledge_rules": [],
  "project_prototype_refs": [],
  "engineering_confidence": null,
  "human_review_required": true,
  "structural_identity_authorized": false,
  "canonical_write_authorized": false,
  "authority_effect": "NONE"
}
```

`engineering_confidence` must not be a renamed OCR/detector score.

## 6. Knowledge provenance

Every rule must declare one of:

- `PROJECT_LEARNED`: learned from explicit N12 evidence/correction;
- `VERIFIED_REFERENCE`: external technical/scientific source acquired and fingerprinted;
- `METHOD_RULE`: CEW governance/method rule;
- `HUMAN_TAUGHT_PROJECT_RULE`: explicit project-local teaching.

Rules without provenance may be used for exploration only and cannot participate in promotion gates.

## 7. N12 regression cases

Initial regression corpus must include at least:

1. **Rectangle ambiguity** — prevent rectangle -> column shortcut; include the known beam-section correction.
2. **G4/TAV-05S support families** — use the governed 34-support / five-family context only as expected project context, not automatic classification authority.
3. **Beam reinforcement callout** — bind diameter/multiplicity/length tokens to the correct graphical target before any reinforcement assertion.
4. **Foundation correspondence** — metric coincidence alone cannot establish identity; require an independent discriminant.
5. **Frame/topology correspondence** — prefer governed connectivity/alignment over visual proximity.

Regression cases used to author a rule are training cases. Readiness requires separate held-out N12 cases not used to create the rule.

## 8. Integration with technical-PDF benchmark

PR #131 extractor benchmark remains upstream.

Recommended pipeline:

- PyMuPDF: PDF/source/provenance baseline and first native vector/text extraction;
- pdfcadcore/ezdxf branch: vector/CAD-oriented reconstruction candidate;
- PP-OCRv6-medium: primary technical-token OCR candidate;
- eDOCr2: engineering-drawing OCR comparator;
- PaddleOCR-VL-1.6: expensive fallback/semantic comparator where justified;
- this grammar: interpretation layer consuming extractor outputs without granting them authority.

The benchmark should therefore measure not only character/token accuracy but **downstream relation recoverability**: whether extracted geometry and text are sufficient to reconstruct the correct technical relation.

## 9. Readiness gates

- `KG-G1 EVIDENCE_SEMANTICS_PASS`: all inputs source-bound and reproducible.
- `KG-G2 TECHNICAL_GRAMMAR_PASS`: token/primitive/relation rules replay deterministically.
- `KG-G3 STRUCTURAL_RELATION_PASS`: hypotheses preserve topology and contradictions.
- `KG-G4 KNOWLEDGE_PROVENANCE_PASS`: every promotion-relevant rule has governed provenance.
- `KG-G5 HELD_OUT_N12_INTERPRETATION_PASS`: unseen N12 cases interpreted correctly enough for professional review without hidden manual reconstruction.

Until KG-G5 passes, CEW remains a governed engineering interpretation assistant, not an autonomous structural interpreter.
