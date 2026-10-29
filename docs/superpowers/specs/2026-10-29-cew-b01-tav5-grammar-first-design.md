# CEW-B01 TAV.5 Grammar-First Design

**Status:** HUMAN-APPROVED DESIGN — ACTIVE REFERENCE  
**Date:** 2026-10-29  
**Scope:** CEW-B01 / N12 / TAV.5 pilot  
**Authority effect:** NONE  

## 1. Intent

CEW-B01 must stop treating TAV.5 primarily as a rectangle-recall problem. TAV.5 is the pilot for learning how a structural drawing encodes information through zones, graphic primitives, recurring motifs, topology, spatial relations, annotations and only later structural meaning.

The objective is to construct an inspectable and sufficiently exhaustive **source-specific graphic grammar** of TAV.5 before specialist object detectors are allowed to drive the workflow.

The original governed SourceVersion remains evidentiary authority. Every derived zone, primitive, motif, relation or hypothesis must map reproducibly back to source coordinates.

## 2. Why the previous detector-first approach is insufficient

PR #165 improved recall materially by combining the existing V2 compound-cell detector with a closed-frame/internal-mark proposal channel. This is useful evidence, but inspection of the exact TAV.5 review package exposed a structural limitation:

- the same rectangular shape can mean different things depending on context;
- some beam-column nodes do not form isolated closed contours because beam linework is connected to the node;
- a rectangle located along a beam may represent a beam section rather than a column;
- beam/slab section symbols use L/T/double-line patterns that are not reducible to closed rectangles;
- title-block, notes and administrative graphics create many irrelevant proposals;
- improving one proposal channel does not demonstrate that the drawing language is understood or exhaustively covered.

Therefore candidate count and rectangle recall are diagnostics, not the architecture.

## 3. Selected approach

Three approaches were considered.

### A. Continue object-first detector tuning

Add more thresholds/channels for columns, beam intersections, beam sections and slabs.

**Rejected as primary architecture** because it creates local fixes before the symbol vocabulary and relation grammar are known. It is prone to overfitting one sheet and confusing similar geometry with different meaning.

### B. End-to-end semantic vision model

Train/use a model to segment or classify structural objects directly.

**Deferred** because CEW currently needs explainable provenance, small-data operation, inspectable failure modes and explicit epistemic boundaries. Such a model may later become an auxiliary proposal channel, not source authority.

### C. Grammar-first decomposition

First divide the document, inventory neutral graphics, discover recurring motifs, reconstruct topology, classify functions with human guidance, bind text/dimensions and audit coverage; only then run specialist detectors.

**Selected.** This aligns with CEW's existing Repository Memory and with the engineering-drawing grammar rule that topology and contextual binding outrank visual proximity or raw shape.

## 4. Reuse-first architecture

The design reuses existing CEW capabilities instead of creating a parallel intelligence stack:

- **Source/provenance and exact raster** — current B01 Steps 1–3.
- **Neutral primitive discovery / clustering / structured descriptors** — bounded reuse/adaptation from PR #137 (`320755e66a7263f1842f73dc14fb9a0ea8ccd7f8`).
- **Technical drawing interpretation invariants** — bounded reuse from PR #143 (`098f98d2724c0a16b9293adc366a585f356bc9fc`).
- **Deterministic similarity / find-similar** — bounded reuse from PR #116 (`a7020bef3934156c917f5bfe975d888c6ba9e684`).
- **Human teaching / positive-negative-ambiguous memory** — reuse from #137/OA lineage.
- **Current V2 detector and closed-frame/internal-mark channel** — retained as later specialist proposal channels, not as the grammar foundation.

No generic similarity, clustering, prototype memory or engineering rule system may be reimplemented inside B01.

## 5. Canonical analysis sequence

```text
Immutable SourceVersion
  -> governed Step-3 raster
  -> G0 Document Zoning
  -> G1 Neutral Graphic Census
  -> G2 Recurring Motif Catalog
  -> G3 Structural Line/Topology Graph
  -> G4 Human Functional Classification
  -> G5 Technical Relation Grammar
  -> G6 Text / Dimension Binding
  -> G7 TAV.5 Grammar Exhaustiveness Audit
  -> G8 Specialist Object Detectors
  -> G9 Held-out Drawing Transfer
  -> downstream human-reviewed structural interpretation only
```

G0–G7 define and test the language of the sheet. G8 consumes that grammar. G9 tests whether the grammar generalizes beyond the pilot.

## 6. G0 — Document zoning

Before structural extraction, divide the page into explicit source-bound regions.

Initial zone vocabulary:

- `STRUCTURAL_WORKAREA`
- `TITLE_BLOCK`
- `LOCATION_DIAGRAM`
- `APPROVAL_STAMP_SIGNATURE`
- `NOTE_OR_LEGEND_REGION`
- `MARGIN_VOID`
- `SCAN_ARTIFACT`
- `UNKNOWN_DOCUMENT_REGION`

The cartiglio/title block must be excluded from structural proposal generation but never removed from the SourceVersion.

A zone mask is a governed derived artifact. It must record source identity, page index, coordinate frame, geometry, method, version and human confirmation state.

A manually confirmed title-block mask is permitted because it classifies document function, not structural identity.

## 7. G1 — Neutral graphic census

Within `STRUCTURAL_WORKAREA`, detect and inventory neutral primitives without assigning structural meaning.

Minimum initial primitive vocabulary:

- `LINE_SEGMENT`
- `PARALLEL_LINE_PAIR`
- `INTERSECTION`
- `T_JUNCTION`
- `LINE_ENDPOINT`
- `RECTILINEAR_CLOSED_SHAPE`
- `RECTILINEAR_OPEN_SHAPE`
- `L_SHAPED_MOTIF`
- `T_SHAPED_MOTIF`
- `CROSS_MOTIF`
- `FILLED_OR_HATCHED_REGION`
- `TEXT_BLOCK`
- `DIMENSION_LINE_OR_TICK_CANDIDATE`
- `LEADER_OR_CALLOUT_CANDIDATE`
- `COMPLEX_GRAPHIC_GROUP`
- `UNKNOWN_GRAPHIC_GROUP`

The names are deliberately nonsemantic. A rectangle is not a column; an intersection is not a beam-column node.

Every primitive must preserve source/page/bbox/coordinate-frame provenance and a deterministic feature signature.

## 8. G2 — Recurring motif catalog

Group recurring configurations before assigning structural meaning.

The catalog must expose for each motif family:

- stable cluster/motif id;
- occurrence count;
- representative examples;
- source locators;
- neutral geometric descriptor;
- relation-to-nearby-lines descriptor;
- associated-text presence without semantic use;
- classification state: `UNCLASSIFIED`, `FUNCTIONALLY_CLASSIFIED`, `NON_STRUCTURAL`, `ARTIFACT`, `UNKNOWN_EXCEPTION`.

A visual atlas is a required review artifact. Human effort should be applied to motif families/groups, not to hundreds of isolated boxes.

## 9. G3 — Structural line/topology graph

Long linework must be converted into a source-bound graph before structural semantics are inferred.

Graph nodes may include:

- intersections;
- T-junctions;
- endpoints;
- line merges/splits;
- boundary turns.

Graph edges represent neutral linear runs with measurable orientation, width/separation and continuity features.

The graph is not yet a beam model. Its purpose is to provide topological context for motif interpretation.

This enables the correct search order for ambiguous nodes:

`TOPOLOGICAL_LOCATION -> LOCAL_GRAPHIC_EVIDENCE -> STRUCTURAL_HYPOTHESIS`

instead of:

`RECTANGLE -> STRUCTURAL_IDENTITY`.

## 10. G4 — Human functional classification

Human review assigns project-local functional classes to recurring motif families while preserving proposal-only authority.

Expected classes to investigate on TAV.5 include, but are not limited to:

- beam-column node section symbol;
- beam section marker placed along a beam;
- beam/slab section motif;
- slab-field motif;
- dimension motif;
- axis/reference motif;
- text/identifier annotation;
- boundary/perimeter motif;
- non-structural/document annotation;
- unknown/exception.

The list is not an oracle. G1/G2 must be capable of surfacing recurring unknown motifs not anticipated here.

Human classifications should emit reusable positive/negative/ambiguous learning receipts through the existing project-local learning capability where compatible.

## 11. G5 — Technical relation grammar

Structural hypotheses arise from relations, not shapes alone.

Illustrative relation rules:

- `RECTANGULAR_MOTIF AT TOPOLOGY_NODE` -> column-section hypothesis candidate;
- `RECTANGULAR_MOTIF ON_LINEAR_RUN AND NOT_AT_NODE` -> beam-section-marker hypothesis candidate;
- `L_OR_T_SECTION_MOTIF OFFSET_FROM_LINEAR_RUN` -> beam/slab-section hypothesis candidate;
- `TEXT_BLOCK NEAR_AND_BOUND_TO MOTIF` -> annotation relation only;
- `DIMENSION_MOTIF TARGETS GEOMETRY` -> dimension relation candidate.

These examples define the reasoning form, not fixed semantic truth. Exact rule vocabulary must reuse/align with PR #143.

## 12. G6 — Text and dimension binding

OCR/text extraction is contextual evidence only.

Text must first be localized and related to geometry. A numeric token cannot become a dimension or section size without a technical relation to a target.

Required invariant:

`OCR_CONFIDENCE != ENGINEERING_CONFIDENCE`.

Text, dimensions and callouts may raise or lower review priority but may not independently create structural identity or canonical geometry.

## 13. G7 — TAV.5 grammar exhaustiveness

TAV.5 grammar is sufficiently exhaustive only when all of the following are true:

1. the page is fully zoned; no area is silently ignored;
2. all significant ink in `STRUCTURAL_WORKAREA` is assigned to a known primitive family, explicit artifact/noise class or `UNKNOWN`;
3. every recurring motif family is functionally classified, explicitly non-structural, artifact, or named unknown;
4. no recurring `UNKNOWN` cluster remains unexplained above the agreed recurrence threshold;
5. long linear runs participate in the topology graph or have an explicit residual classification;
6. every structural hypothesis is traceable to explicit primitive/relation evidence;
7. a whole-workarea visual coverage report exposes `CLASSIFIED`, `NON_STRUCTURAL`, `ARTIFACT`, `UNKNOWN` and unaccounted regions;
8. historical object counts, identifiers or coordinates are not used as production completeness oracles.

G7 measures coverage of the graphic language, not correctness of a final structural model.

## 14. G8 — Specialist detectors

Only after G7 may object-specific proposal channels be treated as the main extraction layer.

The existing capabilities then become useful:

- V2 compound-cell detector;
- closed-frame/internal-mark channel;
- future `beam-intersection/local-rectangle` channel if justified by G3–G7 evidence;
- beam-section-symbol detector;
- slab-field detector;
- any later specialized channel proven necessary by the motif catalog.

Each detector consumes the grammar and emits proposals only.

## 15. G9 — Held-out drawing transfer

TAV.5 can prove source-specific completeness but not generality.

After G7/G8, select at least one held-out structural drawing not used to define the TAV.5 grammar. Apply the grammar without introducing new rules first.

Results must distinguish:

- grammar rule transfers unchanged;
- parameter/calibration changes;
- genuinely new motif families;
- source-specific exceptions.

A new recurring motif on the held-out sheet is evidence for grammar extension, not permission for silent fallback.

## 16. Required artifacts

The grammar-first pilot should ultimately produce:

- `TAV5_DOCUMENT_ZONE_MAP_v1`
- `TAV5_GRAPHIC_PRIMITIVE_CENSUS_v1`
- `TAV5_RECURRING_MOTIF_CATALOG_v1`
- `TAV5_MOTIF_VISUAL_ATLAS_v1`
- `TAV5_TOPOLOGY_GRAPH_v1`
- `TAV5_FUNCTIONAL_SYMBOL_DICTIONARY_v1`
- `TAV5_TECHNICAL_RELATION_GRAMMAR_v1`
- `TAV5_GRAMMAR_COVERAGE_REPORT_v1`
- `TAV5_GRAMMAR_EXHAUSTIVENESS_GATE_v1`

Exact storage format and paths are implementation decisions, but every artifact must be deterministic or carry explicit human receipts where human classification is involved.

## 17. Authority and epistemic invariants

Throughout G0–G9:

- SourceVersion remains evidentiary authority;
- derived masks and transforms never replace the original source;
- primitive/motif detection has no structural authority;
- similarity is retrieval, not identity;
- functional classification remains project-local human teaching until promoted by an authorized downstream gate;
- `INF`, `INC` and `ND` never become `DOC` implicitly;
- no historical count or object number becomes a production oracle;
- no Step 6/canonical write/BIM/FEM/NTC authority is granted by this design.

## 18. Disposition of PR #165 work

The work already completed in PR #165 is retained as valuable experimental and specialist-detector evidence.

However:

- 442 candidates are not proof of grammar completeness;
- recovery of the 19/22 omission class is not sufficient to close B01;
- `drawing_grammar.py` remains a bounded closed-frame/internal-mark proposal channel;
- V2 + closed-frame union belongs conceptually to G8;
- current exact-source qualification remains useful as regression evidence;
- no merge/promotion should be justified solely by Step-4/Step-5 recall success.

## 19. Immediate execution boundary

The next implementation work is restricted to **G0–G2**:

1. deterministic document zoning with explicit title-block exclusion;
2. neutral primitive census inside `STRUCTURAL_WORKAREA`;
3. recurring motif catalog + visual atlas + explicit UNKNOWN residuals.

No specialist detector tuning should occur while G0–G2 are incomplete, except to preserve existing regression tests.

After G0–G2 Human Review, the project decides whether the observed motif inventory is sufficient to design G3/G4 precisely.
