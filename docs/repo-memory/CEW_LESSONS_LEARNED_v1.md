# CEW Lessons Learned v1

**Status:** ACTIVE  
**Date:** 2026-10-30  
**Purpose:** preserve architectural/process lessons that should change future CEW behavior.

## LL-001 — Open/draft work is still project knowledge

**Observation**  
A capability may be implemented, tested and even qualified on a historical branch while remaining absent from `main`.

**Failure mode**  
A later task searches only the active branch/default branch, concludes that the capability does not exist and rebuilds it.

**Rule**  
Before new design, search Repository Memory plus relevant open/closed PRs and branches.

**Current example**  
The CEW-B01 drawing-grammar revision began to recreate similarity, clustering and prototype-learning responsibilities already present in #116/#137/#143.

---

## LL-002 — `BUILD LAST — REUSE FIRST` applies to internal CEW history too

**Observation**  
The Master principle was originally framed around external/open-source tools, but the same waste occurs when CEW rebuilds its own previously developed components.

**Rule**  
Reuse check order:

1. canonical CEW capability;
2. qualified noncanonical CEW capability;
3. suitable external/open-source capability;
4. new code only for the residual gap.

---

## LL-003 — A causal TDD RED proves the test path, not the architecture

**Observation**  
The first drawing-grammar RED correctly proved that the new interface did not exist. Later tests exercised the implementation as intended.

**Failure mode**  
Green/red discipline can still validate a duplicated or wrongly scoped subsystem.

**Rule**  
Before Task 1 RED for a new subsystem, perform a capability reconciliation lookup. TDD begins after ownership of the responsibility is established.

---

## LL-004 — Do not tune a duplicate similarity model to one regression witness

**Observation**  
The experimental `motif_similarity()` produced `0.70` where a synthetic test expected `>= 0.80`.

**Failure mode**  
Changing weights or thresholds at this point could overfit the witness while deepening duplication with OA-3 and visual-learning similarity.

**Rule**  
When a score model overlaps an existing reusable capability, reconcile ownership before tuning.

---

## LL-005 — Separate four different kinds of “drawing intelligence”

Future designs must explicitly distinguish:

1. **technical-drawing method knowledge** — general rules/advice about how drawings are read;
2. **source-specific graphic grammar** — measurable recurrence/relations in one sheet;
3. **project-local learned prototypes** — human-taught positive/negative/ambiguous examples;
4. **structural identity/engineering interpretation** — downstream hypothesis and human-reviewed promotion.

Conflating these layers causes hidden authority escalation and duplicate implementations.

---

## LL-006 — Similarity is retrieval, not identity

**Observation**  
OA-3 already encodes the rule that similarity ranks candidates but creates neither type, family membership nor structural identity.

**Rule**  
Every future similarity/embedding subsystem must expose this boundary explicitly. A visual or geometric match is a review proposal only.

---

## LL-007 — Human corrections are durable training evidence

**Observation**  
The visual-learning architecture already retains positive, negative and ambiguous examples as append-only learning receipts.

**Failure mode**  
A task-local review UI that merely accepts/rejects candidates without feeding reusable learning memory wastes human effort.

**Rule**  
Where compatible, human review should emit reusable project-local learning evidence rather than disposable UI state.

---

## LL-008 — Preserve WIP=1 by porting bounded capability slices

**Observation**  
Historical reusable work often lives in stacked branches with old dependencies.

**Failure mode**  
Reactivating or merging whole historical stacks creates parallel work fronts and imports stale assumptions.

**Rule**  
Port/adapt the smallest coherent interface + implementation + tests needed by the active macro-task. Record the source PR/ref and dependency review.

---

## LL-009 — Names should reveal authority and scope

**Observation**  
A module named `drawing_grammar.py` can appear to own generic drawing interpretation even when it only detects closed frames/internal marks on one B01 raster.

**Rule**  
Prefer names that expose bounded responsibility. Generic names require genuinely generic, reconciled ownership.

---

## LL-010 — Regression witnesses must never become production oracles

**Observation**  
Objects visually represented by identifiers such as 19 and 22 are useful to detect omission classes.

**Rule**  
Literal identifiers, historical counts and coordinates may appear in test/review evidence but must not become production detection inputs.

---

## LL-011 — Exact-source qualification remains mandatory after reuse

**Observation**  
A reused component may have passed its own historical gates under another branch/toolchain/context.

**Rule**  
Reuse does not inherit qualification automatically. The active task must qualify the reused capability against the current exact source, current dependency lock and current authority contract.

---

## LL-012 — Repository Memory must be updated by failures, not only successes

**Observation**  
Failed approaches contain information about what not to build and why.

**Rule**  
A material REWORK, false assumption, duplicated subsystem, incompatible dependency or human-review finding should create/update a lesson or capability entry.

This avoids repeating expensive dead ends after conversational context disappears.

---

## LL-013 — Conversation memory is not repository governance

**Observation**  
Chat context can contain correct architectural decisions but is transient and difficult for another agent or contributor to discover.

**Rule**  
Any decision expected to affect future implementation must be materialized in the repo as a spec, capability registry entry, decision record or lesson learned.

---

## LL-014 — The smallest new code is usually an adapter

When CEW already has provenance, learning, similarity or external-tool capabilities, the preferred new implementation is normally:

`current exact input -> adapter -> reusable capability -> current exact output/assurance`

not another end-to-end subsystem.

---

## LL-015 — Detector recall is not drawing-grammar completeness

**Observation**  
PR #165 improved the exact-TAV.5 proposal set substantially and recovered previously omitted compatible symbols. Human inspection still showed that the sheet contains multiple graphic languages: beam-column nodes, beam-section symbols, beam/slab section motifs, dimensions, annotations, title-block graphics and other recurring forms.

**Failure mode**  
Treating a higher candidate count or recovery of known witnesses as “drawing understood” encourages endless threshold/channel tuning and can hide entire symbol families that the detector was never designed to represent.

**Rule**  
Before specialist object detection becomes the main extraction path, build and review a source-specific neutral graphic inventory plus recurring-motif catalog. Completeness is measured against accounted-for graphic language, not historical object count.

**Affected task:** CEW-B01 / TAV.5 grammar-first redesign, 2026-10-29.

---

## LL-016 — Zone the document before structural extraction

**Observation**  
The TAV.5 title block and administrative/annotation regions generate many geometrically plausible proposals while carrying a different document function from the structural workarea.

**Failure mode**  
Running structural proposal channels over the whole page inflates false positives, increases Human Review cost and makes candidate-count metrics difficult to interpret.

**Rule**  
Create source-bound document-function zones first. Structural extractors operate only on confirmed `STRUCTURAL_WORKAREA`; `TITLE_BLOCK`, notes, stamps and other exclusions remain preserved in the SourceVersion and visible through governed masks.

**Authority constraint:** document zoning grants no structural identity.

---

## LL-017 — Topology and relations must precede object identity when shapes are ambiguous

**Observation**  
On TAV.5, similar rectangles can occur at beam-network nodes, along beams, or in non-structural document regions. Some valid beam-column-node symbols are fused with beam linework and do not form independent closed contours.

**Failure mode**  
A shape-first rule such as “rectangle -> column candidate” confuses function and fails on connected/broken symbols. Adding more geometric thresholds does not solve the ambiguity systematically.

**Rule**  
Use the sequence:

`neutral primitive -> recurring motif -> topology/spatial relation -> functional hypothesis -> human review`.

The existing engineering invariant `TOPOLOGY_OUTRANKS_VISUAL_PROXIMITY_FOR_IDENTITY` must govern downstream interpretation. Specialist detectors belong after grammar/topology foundations, not before them.

---

## LL-018 — Column recognition must be multi-cue; symmetry axes are optional evidence

**Observation**  
The historical G4/TAV-05S pilot already contains five column footprint families, including elongated `30x110` supports 18 and 23 and `110x30` support 30. Human review of the drawing indicates that some elongated columns may lack drawn symmetry axes even though the support identifier is still visible or expected to be visible in/near the footprint.

**Failure mode**  
A detector that requires crossed symmetry axes before admitting a column candidate systematically loses valid elongated footprints and conflates “axis not drawn” with “column absent”. Conversely, treating a number alone as structural identity would over-promote text evidence.

**Rule**  
For column recovery, use a multi-cue sequence:

`numeric/text anchor candidate -> local footprint geometry -> aspect ratio/orientation -> optional axis evidence -> prototype/family similarity -> human review`.

Symmetry axes are supporting evidence, not a mandatory precondition. The numeric identifier is a localization cue, not structural identity.

**Hypothesis to test:** `H-COL-01` — support identifiers are present for all or nearly all column footprints on the relevant carpenterie. This must be measured on the exact sources before becoming a project fact; do not encode “always present” as a detector assumption until verified.

**Affected tasks/capabilities:** proposed `CEW-COL-01`, TAV-05S/TAV-07 column recovery, OA prototype/similarity reuse.

**Source context:** qualified PR #169 checkpoint `f0b54e14f236aadba8a8950fe3a95c91b1c1b740`; historical G4 pilot families; issues #2 and #5.

---

## LL-019 — Carpenteria recognition should emerge from typed objects and relations, not from one-shot line extraction

**Observation**  
Independent raster analysis of TAV-03S/04S/05S/06S showed that long-line detectors also recover folds, sheet borders, title-block geometry and other non-structural lines. At the same time, current CEW work has shown that bounded object families can be learned and reviewed effectively through prototypes and Human Review.

**Failure mode**  
Attempting to recognize an entire carpenteria directly from page-wide linework creates a brittle mixture of structural elements and document graphics. A single global detector also hides which object category is incomplete or ambiguous.

**Rule**  
Reconstruct the carpenteria incrementally through separate typed passes, then compose their relations:

`columns -> beams -> walls/setti -> slab edges/openings -> auxiliary axes/dimensions -> connectivity graph`.

The final carpenteria is a graph/composition of reviewed objects and relations, not a page-level image classification result. Line evidence may support geometry but never creates structural identity by itself.

**Affected tasks/capabilities:** CEW object acquisition, TAV-03S/04S/05S/06S reconstruction, future geometric model and connectivity graph.

**Source context:** PR #59 raster concordance findings; PR #169 graphical beam prototypes and Human Review.

---

## LL-020 — Human graphical review should expand reusable project-local prototypes across object categories

**Observation**  
On PR #169, two approved graphical beam prototypes were sufficient to review the frozen DOUBLE set and a first expansion set, producing durable human decisions without automatic semantic promotion. The same pattern is directly applicable to columns and other carpenteria elements.

**Failure mode**  
Starting each object category with a new standalone detector discards validated human examples and repeats expensive threshold tuning. Keeping review decisions only in chat or screenshots also loses project learning.

**Rule**  
For each new object category, prefer:

`small human-approved prototype set -> deterministic candidate retrieval -> visual Human Review -> governed reusable learning receipt -> next expansion pass`.

Positive, negative and uncertain examples should remain durable project-local evidence. Prototype match remains graphical/retrieval evidence until downstream semantic and structural gates explicitly authorize promotion.

**Affected tasks/capabilities:** proposed `CEW-COL-01`, future beam/column/setto/opening passes, OA-2/OA-3/OA-4 reuse.

**Source context:** PR #169 Human Review `T1=10, T2=1` for expansion set E01–E11; existing LL-006 and LL-007.

---

## Update discipline

Each future lesson should contain:

- stable lesson id;
- observation/evidence;
- failure mode or risk;
- durable rule;
- affected capabilities/tasks;
- date and, when available, source PR/run/review.

Lessons are architectural/process memory only. They never change source evidence or engineering facts.
