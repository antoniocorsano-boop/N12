# CEW-B01 V3 Reuse-First Implementation Plan

**Status:** SUPERSEDED AS ACTIVE ARCHITECTURE — RETAINED AS G8 SPECIALIST-DETECTOR / REGRESSION REFERENCE  
**Superseded on:** 2026-10-29  
**Successor design:** `docs/superpowers/specs/2026-10-29-cew-b01-tav5-grammar-first-design.md`  
**Successor first implementation plan:** `docs/superpowers/plans/2026-10-29-cew-b01-tav5-grammar-foundation-g0-g2.md`

## Supersession reason

This plan successfully reconciled B01 with pre-existing CEW capabilities and improved the Step-4 exact-TAV.5 proposal set. The resulting Human Recall inspection exposed a broader architectural fact: closing a rectangle/motif recall omission does **not** establish an exhaustive grammar of the structural drawing.

The V2 compound-cell detector and the closed-frame/internal-mark channel therefore remain valuable, qualified proposal mechanisms, but they are now downstream **G8 specialist-detector capabilities**. They must not be treated as the foundation for G0–G7 document understanding.

No agent should continue threshold/channel tuning from this plan while grammar-first G0–G2 are incomplete, except to preserve existing regression behavior.

## Repository Memory / Reuse Assessment

The original reconciliation remains valid:

- `CEW-CAP-ENG-DRAWING-GRAMMAR-V1` → reuse bounded rules/provenance from PR #143;
- `CEW-CAP-OA3-DETERMINISTIC-SIMILARITY-V1` → reuse/adapt PR #116 rather than local similarity;
- `CEW-CAP-VISUAL-PROTOTYPE-LEARNING-V1` and zero-prior discovery → reuse/adapt PR #137;
- `CEW-CAP-B01-V2-COMPOUND-CELL-DETECTOR` → retain as G8 proposal channel;
- `CEW-CAP-B01-CLOSED-FRAME-INTERNAL-MARK-SPIKE` → retain as bounded G8 proposal feature channel;
- B01 source binding, provenance, exact-raster replay and review artifacts remain reusable infrastructure.

## Historical goal

The plan's original goal was to close a Step-4 recall omission on exact TAV.5 evidence without creating a second CEW similarity, family-discovery, prototype-memory or engineering-grammar subsystem.

That goal produced useful regression evidence, including exact-source deterministic candidate generation and the recovery of previously omitted compatible motifs. It did **not** prove that all TAV.5 symbol families, beam-column nodes, beam-section symbols, slab-section motifs, dimensions, annotations and unknown recurring graphics had been inventoried or explained.

## Historical tasks and current disposition

### Task A — bounded reuse adapter

**Disposition:** COMPLETE / REUSABLE.  
The source-bound adapter and bounded OA-3 reuse remain valid infrastructure.

### Task B — closed-frame/internal-mark channel

**Disposition:** COMPLETE AS EXPERIMENTAL/SPECIALIST PROPOSAL CHANNEL.  
It remains nonsemantic and may be consumed in G8 after grammar exhaustiveness work establishes where the channel belongs.

### Task C — candidate union/dedup and provenance

**Disposition:** REUSABLE G8/REGRESSION INFRASTRUCTURE.  
The union is not a substitute for neutral primitive census, topology or grammar coverage.

### Task D — exact TAV.5 qualification and recall review

**Disposition:** QUALIFIED REGRESSION EVIDENCE, NOT B01 COMPLETION.  
The exact-source review demonstrated improved recall but also revealed the need to separate title-block/document regions and to understand symbol classes before further detector tuning.

## Authority boundary

The original authority boundary remains unchanged:

- source document remains evidentiary authority;
- all detector output is proposal/evidence only;
- `structural_identity_authorized=false`;
- `canonical_write_authorized=false`;
- no Step 6, BIM/FEM/NTC authority;
- historical object numbers/counts/coordinates remain review witnesses only.

## Next authorized work

Follow the grammar-first sequence. Immediate implementation scope is only G0–G2:

1. document zoning and governed title-block exclusion;
2. neutral graphic primitive census in `STRUCTURAL_WORKAREA`;
3. recurring motif catalog, visual atlas and explicit UNKNOWN residuals.

Do not resume this V3 plan as the active architecture.
