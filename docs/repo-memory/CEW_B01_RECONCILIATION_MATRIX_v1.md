# CEW-B01 Reconciliation Matrix v1

**Date:** 2026-10-28  
**Scope:** Step 4 drawing-grammar / candidate-recall revision  
**Status:** ACTIVE RECONCILIATION  
**Authority effect:** NONE  

## Decision summary

The CEW-B01 V3 work must be reframed from **new drawing-grammar engine** to **integration and source-bound qualification of existing CEW capabilities**.

Selected architecture:

```text
Immutable TAV.5 / governed Step-3 raster
  -> CEW-B01 source-bound extraction adapter
  -> reusable technical-drawing interpretation rules
  -> reusable primitive/prototype-learning layer
  -> reusable deterministic similarity / find-similar
  -> B01-specific candidate-channel union + provenance binding
  -> deterministic review package
  -> human accept / reject / uncertain
  -> downstream promotion gates only after human decision
```

The current `cew_b01/drawing_grammar.py` is therefore not accepted as a new canonical grammar/similarity subsystem. Its reusable parts may survive only as a bounded B01-specific proposal channel or feature extractor after reconciliation.

---

## Reconciliation matrix

| Capability | Existing source | Existing maturity | Canonical responsibility | Decision for B01 | New work still justified |
|---|---|---|---|---|---|
| Source/provenance chain | CEW Master + B01 Steps 1–3 | CANONICAL / active B01 baseline | Immutable source, page/raster identity, coordinate/provenance binding | **REUSE** | Bind every imported/reused capability to current B01 source/raster contracts |
| Technical-drawing interpretation rules | PR #143 `work/n12-engineering-drawing-grammar-v1@098f98d...` | QUALIFIED_NONCANONICAL; held-out N12 gate PASS | Rules such as rectangle != column, target binding, topology before proximity, OCR confidence != engineering confidence | **REFERENCE + PORT bounded contract/rules** | Adapter from B01 graphic observations into rule vocabulary; no second rule system |
| Technical-drawing method provenance | PR #143 | QUALIFIED_NONCANONICAL | Explicit knowledge provenance: `PROJECT_LEARNED`, `VERIFIED_REFERENCE`, `METHOD_RULE`, `HUMAN_TAUGHT_PROJECT_RULE` | **PORT / ALIGN** | Add method/version/hash references to B01 review evidence |
| Neutral graphic primitive discovery | PR #137 `work/cew-new-project-preacquisition-v1@320755e...` | QUALIFIED_NONCANONICAL implementation foundation | Source/page/bbox-bound `GraphicPrimitiveCandidate` discovery with no semantic authority | **ADAPT / PORT** | B01 adapter for exact Step-3 raster and any TAV.5-specific primitive features not represented upstream |
| Non-semantic clustering | PR #137 | QUALIFIED_NONCANONICAL | Opaque recurring graphic-group discovery before project semantics | **REUSE / ADAPT** | Map B01 motif descriptors into existing clustering/learning inputs; explicit UNKNOWN residuals |
| Structured graphic descriptor | PR #137 | QUALIFIED_NONCANONICAL | Deterministic explainable descriptor (`CEW_STRUCTURED_GRAPHIC_DESCRIPTOR_V1`) | **REUSE** | Extend only through a versioned B01 feature channel when genuinely missing signals are demonstrated |
| Project-local prototype memory | PR #137 | QUALIFIED_NONCANONICAL | Positive/negative/ambiguous examples, replayable project-local concept memory | **REUSE / PORT** | Bind receipts to current B01 SourceVersion/Page/EvidenceRegion/candidate fingerprints |
| Counterexample memory | PR #137 | QUALIFIED_NONCANONICAL | Preserve rejected examples and penalize future retrieval | **REUSE** | Ensure B01 human rejects feed the same memory rather than being discarded |
| Learning receipts | PR #137 | QUALIFIED_NONCANONICAL | Append-only `POSITIVE`, `NEGATIVE`, `AMBIGUOUS` human teaching evidence | **REUSE / PORT** | B01 receipt adapter; no separate B01 teaching schema unless incompatibility is proven |
| Deterministic `Find Similar` | PR #116 `work/cew-oa3-deterministic-similarity-v1@a7020be...` | QUALIFIED_NONCANONICAL foundation | Versioned explainable similarity from a human-taught noncanonical prototype | **REUSE / ADAPT** | Define B01 mapping from motif/primitive features to OA-3 signal contract |
| Similarity signals | PR #116 | QUALIFIED_NONCANONICAL | geometry kind, dimension ratio, orientation, topology hint, spatial context, associated text | **REUSE as baseline** | Add B01-specific signal only if an uncovered omission is demonstrated and versioned; do not tune weights merely to satisfy one regression |
| Multi-channel visual similarity | PR #137 | QUALIFIED_NONCANONICAL | Structured descriptor plus optional frozen visual embedding, with component scores inspectable | **REFERENCE / optional later reuse** | Not required to close current Step 4 unless deterministic channels demonstrably fail; DINOv3 remains optional |
| Human teaching workflow | PR #137 + OA-2/OA-3 lineage | QUALIFIED_NONCANONICAL | `TEACH_THIS_IS`, `NOT_THIS`, `UNCERTAIN`, `FIND_SIMILAR` | **REUSE concept/contracts** | Connect current B01 review surface to reusable teaching receipts without changing promotion authority |
| Human group review | OA-3 -> OA-4 lineage / PR #137 workbench | Existing noncanonical workflow | Human precision gate after candidate retrieval | **REUSE concept; integrate later in B01 review surface** | B01-specific overview/contact-sheet presentation and exact source locators |
| Engineering semantic interpretation | PR #143 | QUALIFIED_NONCANONICAL | Convert graphic/technical relations only into `STRUCTURAL_HYPOTHESIS_CANDIDATE` | **REUSE boundary, not automatic execution for Step 4** | Step 4 remains geometric/object proposal; semantic interpretation stays downstream and non-promoting |
| B01 V2 compound-cell detector | Current CEW-B01 parent line | Existing Step-4 qualified channel | Strong source-specific high-precision proposal channel | **REUSE unchanged as one channel** | Union it with additional proposal channels; do not replace it |
| Closed-frame + internal-mark proposal | PR #165 current `cew_b01/drawing_grammar.py` | EXPERIMENTAL; focused tests partially/iteratively developed | Detect a class of source-like motifs omitted by V2 | **KEEP only as B01 proposal/feature channel** | Rename/reframe so it does not own clustering, prototype memory or generic similarity |
| `motif_similarity()` in PR #165 | PR #165 | EXPERIMENTAL / overlapping | Currently computes aspect + ink + component + context weighted score | **SUPERSEDE / REMOVE as canonical similarity** | Replace with adapter into existing OA-3 / visual-learning similarity; retain only feature calculation if useful |
| `DrawingMotif` model in PR #165 | PR #165 | EXPERIMENTAL / overlapping | Local rectangle + internal/context metrics | **ADAPT** | Map to existing `GraphicPrimitiveCandidate` / descriptor contract or define a thin B01 observation type, not a second learning ontology |
| Local family discovery planned in #165 | PR #165 plan | NOT YET JUSTIFIED as new subsystem | Planned clustering and UNKNOWN handling | **DO NOT REIMPLEMENT** | Use #137 clustering/prototype memory; add only adapter/tests needed for B01 |
| Candidate union / dedup | CEW-B01 Step 4 | B01-specific | Combine V2 and additional proposal channels while preserving provenance and deterministic IDs | **BUILD / KEEP IN B01** | This is genuinely task-local and belongs in B01 |
| Exact-raster replay / exact-SHA qualification | CEW-B01 workflows | Active qualified pattern | Reproducibility and source identity assurance | **REUSE and EXTEND** | Qualify reused components on exact TAV.5 Step-3 raster twice; emit diagnostics/artifacts |
| Human review package for TAV.5 | CEW-B01 Step 5 | Existing B01-specific review boundary | Whole-sheet overview, source context, decision surface | **REUSE and EXTEND** | Add channel/family/prototype/UNKNOWN explanations; verify omission class represented by 19/22 without using numbers as oracle |

---

## What should be removed from the current implementation plan

The following planned responsibilities must no longer be assigned to `cew_b01/drawing_grammar.py` as new generic implementations:

1. generic project-local family memory;
2. generic `find_similar` engine;
3. generic similarity weighting/threshold model;
4. learning receipt lifecycle;
5. generic positive/negative/ambiguous prototype learning;
6. semantic engineering drawing rules already represented by #143.

These are repository capabilities, not B01-local inventions.

## What may remain in `cew_b01`

A bounded B01 module may still own:

- exact Step-3 raster input binding;
- TAV.5-specific candidate proposal channels;
- extraction of measurable source-local features unavailable from the reused primitive layer;
- coordinate-frame conversion;
- deterministic candidate union and deduplication;
- mapping into the existing prototype/similarity contracts;
- B01 reason codes and qualification diagnostics;
- exact-source replay and review-package generation.

Suggested conceptual rename if the current module survives:

`drawing_grammar.py` -> `closed_frame_internal_mark_channel.py` or another name that makes its limited responsibility explicit.

No rename should occur until dependent tests/interfaces are reconciled.

## Dependency rule for historical PRs

PR #116, #137 and #143 are open/draft historical lines. B01 must not merge their entire stacks blindly.

Reuse procedure:

1. identify the exact contract/function needed;
2. inspect its dependency closure;
3. port or adapt the smallest coherent unit;
4. preserve original provenance in commit/decision records;
5. run current B01 tests plus the reused component's relevant validators;
6. do not import historical authority claims or stale runtime assumptions automatically.

This satisfies WIP=1: reuse knowledge and bounded code inside the active CEW-B01 line rather than reopening multiple macro-streams.

## Immediate disposition of the current RED

The observed `motif_similarity` regression (`0.70 < 0.80`) must **not** be repaired by arbitrary weight/threshold tuning before reconciliation.

Reason:

- the score belongs to an implementation now classified as overlapping;
- OA-3/#116 and visual-learning/#137 already define similarity responsibilities;
- tuning against the current synthetic witness risks overfitting and would deepen duplication.

The correct next RED should be an **adapter/reuse contract test**, for example:

> a B01 source-bound motif can be transformed into the selected existing similarity input without losing provenance, and two translated compatible examples rank as similar while a context-incompatible example remains distinguishable.

## New-work boundary after reconciliation

After reuse, the genuinely new CEW-B01 Step-4 work is reduced to four responsibilities:

1. **B01 source adapter** — translate exact TAV.5 raster observations into reusable primitive/learning/similarity contracts.
2. **Additional proposal channel** — closed-frame/internal-mark or equivalent high-recall extraction if existing primitive discovery does not already cover it sufficiently.
3. **Candidate union and provenance** — combine V2 + reused/reconciled channels deterministically.
4. **Real-source qualification and human review evidence** — prove the omission class is surfaced without oracle data and without authority escalation.

That is the implementation boundary to use for the revised plan.
