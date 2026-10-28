# CEW-B01 Drawing Grammar Induction — Technical Drawing Reading Skill

**Date:** 2026-10-28  
**Parent task:** `CEW-B01`  
**Companion spec:** `docs/superpowers/specs/2026-10-28-cew-b01-detector-v3-recall-design.md`  
**Base:** `impl/cew-b01-step1-source@e20e9daba1dce08f53ddb26f06efc9c5b2745211`  
**Status:** DESIGN EXTENSION — human-approved direction, implementation planning pending

## Intent

The next CEW-B01 detector revision must not be reduced to generic shape detection or OCR-assisted rectangle finding. CEW must use a technical-drawing reading model that combines:

1. **general technical-drawing skill** — knowledge of graphical conventions;
2. **local drawing-grammar induction** — learning how the specific drafter/technician encoded objects in the current sheet;
3. **prototype/family discovery** — discovering recurring local symbol families;
4. **find-similar propagation** — searching the sheet for instances compatible with validated prototypes;
5. **human teaching and review** — a human validates, rejects or marks uncertain the proposed objects before structural identity is promoted.

The original document remains evidentiary authority. Technical-drawing skill and induced grammar are methodological aids with `authority_effect = NONE` until an explicit human decision promotes a source-bound object.

## Why this extension is required

The current V2 detector recognizes one narrow geometric motif: a compound rectangular symbol reconstructed from four source cells. Human inspection of the TAV.5 overview showed plausible numbered structural symbols that are graphically similar to accepted candidates but were not selected.

The observed failure is therefore not only a threshold problem. It exposes a missing abstraction: the system must reason about **symbol = shape + internal marks + graphical relations + local role + recurrence**.

For example, a rectangular symbol can be distinguished from an unrelated rectangular detail by the combination of:

- envelope proportions;
- internal handwritten/printed identifier;
- adjacent dimensional annotations;
- axis or beam-line relationships;
- repeated use of the same motif elsewhere in the sheet;
- consistent orientation/scale family;
- placement within the structural layout;
- similarities to already validated instances.

No single cue is sufficient in all cases.

## Two knowledge layers

### Layer A — Technical Drawing Reading Skill

This is reusable, versioned methodological knowledge. It must include at least:

- line hierarchy and line weight;
- axes and centerlines;
- dimension strings, extension lines and dimension values;
- grids and structural alignment;
- plan/section/elevation conventions;
- symbols, callouts and references;
- hatching and material conventions;
- text orientation and rotated annotations;
- title block / legend boundaries;
- structural framing conventions for beams, columns, walls, slabs and foundations;
- relationship between geometry, annotation and object identity;
- distinction between object graphics, annotation graphics and construction/reference graphics.

This skill is a **MethodAdvisory**. It proposes how to read a drawing; it does not create canonical facts.

### Layer B — Local Drawing Grammar

For each source sheet, CEW derives a local grammar from the immutable page/raster without assuming that every technician draws exactly the same way.

The local grammar consists of:

- primitive inventory: lines, closed frames, cells, text/mark regions, dimension-like strokes;
- relation graph: intersects, contains, aligns-with, continues-through, adjacent-to, dimensioned-by, repeated-near;
- motif fingerprints;
- recurrent motif clusters;
- prototype candidates;
- context signatures;
- unknown/unclustered residuals.

The local grammar is source-specific and never becomes a general truth about all technical drawings.

## Architecture

### 1. Primitive extraction

`TAV.5 immutable source -> governed raster/vector evidence -> neutral primitives`

Primitives are descriptive only. They carry page/raster coordinates and provenance.

### 2. Relation graph

Build a graph connecting primitives using measurable relationships rather than semantic labels.

Examples:

- frame contains internal mark;
- frame intersects horizontal/vertical line;
- annotation is adjacent to frame;
- two frames share similar size/aspect ratio;
- frames occur at repeated structural spacings;
- dimension text and extension strokes occur near a frame.

### 3. Motif fingerprints

Each local object-like region gets a fingerprint from:

- outer geometry;
- internal topology/mark density;
- line-entry directions;
- nearby dimension evidence;
- local orientation;
- relative scale;
- relation-graph neighborhood.

No object number is used as an oracle.

### 4. Prototype and family discovery

Cluster only sufficiently similar motif fingerprints. Do **not** force every region into a family.

Outputs:

- `PrototypeCandidate`;
- `LocalSymbolFamilyCandidate`;
- `UNKNOWN` residuals.

A family candidate means "graphically recurring motif", not "confirmed structural family".

### 5. High-recall candidate union

The existing V2 compound-cell detector becomes one strong channel inside a broader candidate system. Additional channels include:

- closed-frame + internal-mark candidates;
- motif-similarity candidates derived from local prototypes;
- context-supported candidates from the relation graph.

Union and deduplication are deterministic.

### 6. Human teaching

The human must be able to say, effectively:

- this is a valid example;
- this is not one;
- this is uncertain;
- find others similar to this.

A validated example may become a local prototype for `find_similar`, but the propagation produces **new candidates**, never canonical objects automatically.

### 7. Promotion boundary

Only human-accepted, source-bound candidates may proceed:

`EvidenceRegion -> ObjectCandidate -> REVIEWED -> APPROVED -> StructuralObject / CAD canonical promotion`

The document remains authority throughout.

## Relationship with Detector V3

The companion V3 high-recall design remains valid but becomes a **component**, not the full solution.

`closed frame + internal mark` is useful as a discovery channel, but it must be embedded in the richer drawing-grammar pipeline.

The revised conceptual flow is:

`immutable TAV.5 -> technical-drawing primitives -> relation graph -> local grammar induction -> recurrent motifs/prototypes -> V3 candidate channels + find-similar -> deterministic review surface -> human teaching/review -> accepted source-bound objects only`

## 19 and 22 rule

The visually observed patterns exemplified by 19 and 22 are **regression witnesses**, not hard-coded targets.

The new system passes only if their class of motif can be rediscovered from the source by one or more general mechanisms:

- closed-frame/internal-mark evidence;
- similarity to a learned local prototype;
- relation-graph/context compatibility.

Their literal numbers, coordinates and expected count must not be production inputs.

## Skill acquisition and evidence

Technical-drawing reading competence must be explicit, versioned and inspectable. It should be represented as a CEW skill/method package rather than hidden in prompts or conversation memory.

Each methodological application should record:

- skill/version/hash;
- source sheet identity;
- primitives/relations used;
- prototype/family identifiers;
- detector/matcher version;
- confidence/evidence basis;
- human decision where present.

The skill does not alter epistemic status by itself.

## Required qualification properties

1. **Source-bound:** all candidates trace back to the immutable source.
2. **Reproducible:** same source + same skill/method versions produce the same primitive/relation/fingerprint set within the deterministic boundary.
3. **High recall:** visible motifs compatible with a validated local family must be proposed or explicitly remain `UNKNOWN`, not silently disappear.
4. **No forced clustering:** unmatched graphics remain `UNKNOWN`.
5. **No semantic leakage:** family similarity does not itself assign structural identity.
6. **Human teachability:** validated examples can drive `find_similar` without manual coordinate coding.
7. **Auditability:** candidate reason includes the channels and prototype/context evidence that caused selection.

## Required tests for implementation planning

- repeated variants of one motif cluster together under translation and small drawing variation;
- rotated/annotated variants remain discoverable when their technical role and context are compatible;
- a visually similar rectangle with annotation/relationship mismatch remains separate or `UNKNOWN`;
- prototype-derived `find_similar` recovers a missed source-like instance without object-number or coordinate oracle;
- rejected human example does not silently propagate as accepted truth;
- uncertain example does not promote;
- family discovery is deterministic across replay;
- unknown residuals are emitted explicitly;
- production code contains no historical support count, object-number whitelist or manual source coordinates.

## Review surface

The next human review package should no longer show only isolated crops. It should provide:

1. whole-sheet overview with candidate overlays by discovery channel/family;
2. prototype/family panels showing repeated motifs side by side;
3. candidate cards with local context, not only tight crops;
4. explicit `UNKNOWN`/unmatched residual indicators;
5. `find similar` evidence showing why candidates were grouped;
6. human actions: accept / reject / uncertain / use as prototype / show similar.

The goal is to let the human review the **drawing logic**, not merely individual rectangles.

## Non-goals and authority limits

- no automatic professional interpretation;
- no canonical write from skill or pattern matching;
- no conversion of `INF/INC/ND` to `DOC`;
- no hidden use of historical object counts as truth;
- no replacement of original drawings with crops or learned prototypes;
- no Step 6, BIM/FEM or NTC authorization from this design alone.

## Success criterion

CEW has acquired a usable technical-drawing-reading capability when it can explain and reproduce the local graphic grammar of the source sufficiently to propose recurring object families and similar instances, while keeping ambiguous/unmatched regions explicit and reserving structural meaning and canonical promotion for human-reviewed, source-bound evidence.
