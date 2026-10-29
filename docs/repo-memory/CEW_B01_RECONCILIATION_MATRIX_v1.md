# CEW-B01 Reconciliation Matrix v1

**Date:** 2026-10-29  
**Scope:** TAV.5 grammar-first reconciliation after Step-4/Step-5 Human Recall inspection  
**Status:** ACTIVE RECONCILIATION — GRAMMAR-FIRST  
**Authority effect:** NONE  

## Decision summary

The 2026-10-28 reconciliation correctly prevented CEW-B01 from rebuilding similarity, clustering and prototype-learning subsystems already present in #116/#137/#143. The subsequent exact-TAV.5 recall work exposed a second architectural issue: even a materially improved proposal set does not demonstrate that the drawing language itself has been inventoried or understood.

B01 is therefore reframed again, this time from **detector-first recall repair** to **grammar-first document understanding**.

Selected architecture:

```text
Immutable TAV.5 / governed Step-3 raster
  -> G0 document zoning
  -> G1 neutral graphic census
  -> G2 recurring motif catalog + visual atlas
  -> G3 line/topology graph
  -> G4 human functional classification
  -> G5 technical relation grammar
  -> G6 text/dimension binding
  -> G7 grammar exhaustiveness audit
  -> G8 specialist proposal channels
  -> G9 held-out drawing transfer
  -> downstream human-reviewed structural interpretation only
```

The governing design is:

`docs/superpowers/specs/2026-10-29-cew-b01-tav5-grammar-first-design.md`

The immediate implementation scope is:

`docs/superpowers/plans/2026-10-29-cew-b01-tav5-grammar-foundation-g0-g2.md`

---

## Reconciliation matrix

| Capability / responsibility | Existing source | Decision for grammar-first B01 | New work boundary |
|---|---|---|---|
| SourceVersion / exact page / Step-3 raster | current CEW-B01 Steps 1–3 | **REUSE unchanged** | Bind every derived zone/primitive/motif to exact source/raster identity |
| Repository Memory | current B01 repo-memory foundation | **REUSE / UPDATE** | Persist grammar-first lessons and prevent detector-first restart |
| Neutral primitive discovery | PR #137 `320755e...` | **ADAPT / PORT bounded** | Add raster-specific neutral primitive observations required by TAV.5; no semantics |
| Non-semantic clustering | PR #137 | **REUSE / ADAPT** | Build G2 recurring motif catalog; preserve UNKNOWN clusters |
| Structured graphic descriptor | PR #137 | **REUSE** | Extend only if observed TAV.5 motifs cannot be represented by the existing neutral vocabulary |
| Project-local human teaching / receipts | PR #137 / OA lineage | **REUSE later** | G4 functional classification should emit reusable positive/negative/ambiguous evidence where compatible |
| Deterministic Find Similar | PR #116 `a7020be...` | **REUSE later** | Not required for initial G0–G2 census; use after human-taught motifs/prototypes exist |
| Technical-drawing interpretation invariants | PR #143 `098f98d...` | **REUSE / PORT bounded rules** | Govern G4–G6; `rectangle != column`, relation binding and topology precedence remain mandatory |
| Document zoning / title-block exclusion | no adequate current B01 capability | **BUILD bounded G0 capability** | Source-bound document-function masks + human confirmation; no structural authority |
| Structural workarea | new grammar-first concept built from G0 | **BUILD** | Structural proposal generation must consume confirmed workarea masks only |
| Neutral raster primitive census | #137 concept + current raster infrastructure | **BUILD adapter/extractor** | G1 inventory of lines, intersections, open/closed rectilinear forms, text-like groups, hatch/fill, UNKNOWN |
| Recurring motif visual atlas | existing B01 review-package patterns + #137 clustering | **BUILD B01 review artifact** | Group examples by neutral motif family and expose occurrence counts/source locators/UNKNOWN |
| Line/topology graph | technical method known in #143, no current B01 implementation adequate | **DEFER TO G3** | Design only after G0–G2 inventory is reviewed |
| Functional symbol dictionary | human project-local knowledge | **DEFER TO G4** | Classify motif families, not individual shapes blindly |
| Text/dimension binding | #143 relation rules + current OCR infrastructure | **DEFER TO G6** | OCR remains contextual evidence; no numeric/semantic authority from proximity alone |
| B01 V2 compound-cell detector | current B01 parent line | **RETAIN / MOVE CONCEPTUALLY TO G8** | Specialist high-precision proposal channel after grammar foundation |
| Closed-frame/internal-mark channel | PR #165 `drawing_grammar.py` | **RETAIN / MOVE CONCEPTUALLY TO G8** | Specialist motif proposal only; not grammar foundation |
| Current Step-4 union/dedup | PR #165 | **RETAIN AS G8/REGRESSION INFRASTRUCTURE** | Must not drive G0–G2 or serve as completeness oracle |
| Current exact Step-4/Step-5 qualification | PR #165 | **RETAIN AS REGRESSION EVIDENCE** | Useful proof that existing proposal channels are reproducible; not proof of grammar exhaustiveness |
| Historical witnesses 19/22 and counts | review evidence only | **REFERENCE ONLY** | Never production detector input or grammar-completeness oracle |

---

## Why grammar-first is required

Human review of exact TAV.5 demonstrated that identical or similar geometric forms can have different drawing functions:

- a rectangle at a line-network node may be a column-section symbol;
- a rectangle along a linear run may be a beam-section marker;
- L/T/double-line motifs may encode beam/slab section relations;
- some beam-column nodes do not form independent closed contours because beam linework connects directly to the local symbol;
- document graphics in the title block can satisfy generic geometric detector rules while being irrelevant to structural extraction.

Therefore shape-only detector recall cannot be used as the primary representation of the drawing.

## Immediate new-work boundary

Only G0–G2 are authorized by the current plan:

### G0 — Document zoning

Build source-bound document-function masks. The title block is excluded from structural proposal generation only after explicit human confirmation. SourceVersion remains intact.

### G1 — Neutral graphic census

Inventory significant graphic content inside `STRUCTURAL_WORKAREA` without assigning structural meaning. Broken/incomplete graphics and scan artifacts must remain visible as neutral/UNKNOWN records rather than disappearing.

### G2 — Recurring motif catalog

Cluster recurring neutral configurations and produce a visual atlas with representatives, occurrence counts and source locators. Recurring unknown motifs are first-class review items.

No G3 topology implementation, G4 semantic classification or G8 detector tuning is authorized until G0–G2 have been reviewed.

## Grammar exhaustiveness target

The later G7 gate must not ask “did we find the historical expected number of objects?”. It must ask whether the **graphic language of the workarea is accounted for**:

- page fully zoned;
- significant workarea ink assigned to known primitive/artifact/UNKNOWN classes;
- every recurring motif explicitly classified or retained as UNKNOWN;
- long linework explained by topology or residual class;
- every structural hypothesis traceable to primitive + relation evidence;
- whole-workarea coverage visible to Human Review;
- no hidden unaccounted recurring class.

## Disposition of the 2026-10-28 V3 plan

`docs/superpowers/plans/2026-10-28-cew-b01-reuse-first-v3-implementation.md` is now **SUPERSEDED AS ACTIVE ARCHITECTURE**.

Its adapter/reuse work, proposal channels, deterministic union and exact-source qualification remain valuable. They are retained as G8 specialist-detector/regression assets, not deleted.

## Authority boundary

Nothing in this reconciliation grants engineering authority:

- SourceVersion remains evidentiary authority;
- zoning is document-function classification only;
- primitives/motifs are nonsemantic observations;
- clustering/similarity do not create identity;
- functional labels remain project-local human teaching until downstream promotion;
- `INF`, `INC`, `ND` never become `DOC` implicitly;
- structural identity and canonical write remain unauthorized;
- no merge is authorized by this reconciliation.
