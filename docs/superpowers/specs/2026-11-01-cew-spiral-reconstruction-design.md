# CEW-SPIRAL-01 — Spiral Reconstruction Design

**Date:** 2026-11-01  
**Status:** `QUEUED_SUCCESSOR / NOT_ACTIVE`  
**Activation gate:** closure of `CEW-COL-03F` and release of the single CEW WIP slot  
**WIP effect:** `NONE`  
**Authority effect:** `NONE`  
**canonical_write_authorized:** `false`  
**structural_identity_authorized:** `false`  
**m0g_authorized:** `false`

## 1. Purpose

CEW-SPIRAL-01 reorganizes already qualified CEW capabilities around progressive convergence toward a technically traceable model of the existing structure.

The program does not introduce a second drawing-understanding stack. It coordinates existing evidence acquisition, technical grammar, project-local prototype learning, deterministic similarity and BIM/IFC projection behind the current CEW authority boundary.

The target cycle is:

`current model state -> unresolved residual -> best admissible evidence channel -> governed interpretation proposal -> human/governance decision -> accepted model delta -> projection/read-back -> next residual`

The model is therefore an evolving reconstruction state, not a substitute evidentiary source.

## 2. Current boundary

`CEW-COL-03F Primary Identity Bridge Evidence` remains the only active WIP. Its current gate cannot be satisfied by historical derived material, similarity, OCR confidence, prototype matching or BIM output. CEW-SPIRAL-01 is queued only and must not modify the COL-03F closure semantics.

In particular:

- historical package `v25` is comparator/reference material only until separately qualified for a bounded use;
- recovered DXF cannot replace independent primary-source identity bridge evidence required by COL-03F;
- BIMCraft output is a regenerable projection, never evidentiary authority;
- no queued successor artifact grants structural identity or canonical write authority.

## 3. Reuse-first capability map

CEW-SPIRAL-01 SHALL reuse or adapt the following frozen capabilities instead of reimplementing them.

### 3.1 Engineering drawing grammar

Source: PR `#143`, ref `098f98d2724c0a16b9293adc366a585f356bc9fc`.

Contract pipeline:

`SourceVersion -> Page -> EvidenceRegion -> GraphicPrimitive_or_TechnicalToken -> TechnicalRelation -> StructuralHypothesis -> HumanReview`

Required invariants include:

- `RECTANGLE_DOES_NOT_IMPLY_COLUMN`;
- `DIMENSION_REQUIRES_RELATION`;
- `TOPOLOGY_OUTRANKS_VISUAL_PROXIMITY_FOR_IDENTITY`;
- `OCR_CONFIDENCE_IS_NOT_ENGINEERING_CONFIDENCE`;
- `SOURCE_REMAINS_EVIDENTIARY_AUTHORITY`.

Disposition: `PORT_BOUNDED_RULES_AND_PROVENANCE_CONTRACT`.

### 3.2 Deterministic Find Similar

Source: PR `#116`, ref `a7020bef3934156c917f5bfe975d888c6ba9e684`.

Signals already owned by this capability:

- geometry kind;
- dimension ratio;
- orientation;
- topology hint;
- spatial context;
- associated text.

Disposition: `ADAPT`. Similarity remains proposal-only and cannot create object type, family membership, structural identity or canonical writes.

### 3.3 Project-local prototype learning

Source: PR `#137`, ref `320755e66a7263f1842f73dc14fb9a0ea8ccd7f8`.

The existing append-only learning receipts and prototype memory for `POSITIVE`, `NEGATIVE` and `AMBIGUOUS` human teaching evidence are reused. The structured graphic descriptor remains the baseline channel; optional visual-foundation embeddings remain separately qualified and non-authoritative.

Disposition: `PORT_OR_ADAPT`.

### 3.4 Zero-prior graphic discovery and B01 channels

The existing zero-prior primitive discovery, B01 compound-cell detector and closed-frame/internal-mark feature channel remain proposal channels inside a deterministic union. They do not own semantics or family learning.

### 3.5 BIM/IFC projection

BIMCraft Stage A is already qualified as a candidate projection/inspection engine behind the CEW adapter. IfcOpenShell remains the semantic IFC read-back boundary. Neither component becomes CEW authority.

## 4. New component boundary: Spiral Orchestrator

The only new architectural component authorized by this design is a deterministic routing/orchestration layer. It SHALL NOT infer structural truth.

### Inputs

- current model state;
- unresolved residual ledger;
- capability registry and frozen capability refs;
- available source/evidence refs and their quality class;
- current authority flags;
- optional human-taught project-local prototype refs.

### Output

A `SpiralRouteDecision` containing at least:

- selected residual ID;
- selection reason codes;
- selected evidence/acquisition channel;
- capability IDs to invoke;
- required human/governance gate;
- prohibited authority transitions;
- expected receipt/evidence outputs;
- stable input fingerprint.

A route decision is not an interpretation decision.

### Deterministic residual selection

Residual selection SHALL be lexicographic and explainable, not a hidden weighted semantic score:

1. unresolved blocker preventing an already identified model relation;
2. expected model impact from explicit dependency graph;
3. availability of stronger source-native evidence;
4. bounded acquisition cost class;
5. stable residual ID tie-break.

No rule may rank a residual by presumed structural identity not already present in governed evidence.

## 5. Evidence routing policy

CEW-SPIRAL-01 uses a source-native-first policy.

### Route A — vector/source-native evidence

When an immutable DXF or equivalent source-derived vector asset is available and qualified, inspect the vector structure before raster/OCR processing.

### Route B — governed raster evidence

If source-native vector evidence is absent or does not contain the needed token/relation, use the existing deterministic rendering and image-feature channels.

### Route C — OCR fallback

OCR is invoked only for text not obtainable from a qualified vector/text channel. Tesseract remains the repository baseline. Any PaddleOCR comparison is a separate benchmark and cannot silently replace the frozen baseline.

### Route D — optional native DWG experiment

If original immutable DWG sources become available, a separate non-authoritative qualification may evaluate positioned text, blocks and attributes. No DWG-derived result is admitted until its source identity, tool version, output contract and replay are frozen.

## 6. CEW-DXF-01 — first executable slice

After WIP release, the first implementation slice SHALL be `CEW-DXF-01`.

### Scope

Read/query only over a frozen historical DXF asset already present in the repository package. Initial qualification uses the repository-pinned `ezdxf==1.4.4`; any newer upstream version is a separate candidate requiring its own qualification.

### Required observations

- exact input SHA-256 and package lineage;
- DXF version and document units when available;
- layer inventory;
- entity counts by DXF type;
- `TEXT` / `MTEXT` values with insertion/placement data;
- `INSERT` instances and block names;
- block definitions and attribute presence where available;
- dimension entities and their bounded observable parameters;
- document/model extents where deterministically derivable;
- stable normalized inventory digest.

### Explicitly prohibited

- mutation of the DXF;
- automatic semantic classification;
- use of historical labels as production truth;
- promotion to StructuralObject;
- satisfying the current COL-03F primary-source identity gate;
- canonical write.

The result is `HISTORICAL_DXF_OBSERVATION_ONLY` until a later gate establishes a permitted relation to current primary evidence.

## 7. Grammar and prototype reconciliation

After CEW-DXF-01, vector observations are normalized into existing CEW `GraphicPrimitive` / `TechnicalToken` compatible inputs. The ported engineering grammar may then emit `TechnicalRelation` and `StructuralHypothesis` candidates with explicit knowledge provenance.

Where human teaching exists, the existing prototype memory and deterministic similarity capability may propose related occurrences. Their results remain separately inspectable and must preserve reason codes/component scores.

Cross-view or cross-source conflicts fail closed and become residuals for a later spiral cycle.

## 8. Model projection gate

A model delta is eligible for BIMCraft projection only when the upstream CEW gate has accepted the relevant object identity/geometry for the bounded slice.

Projection sequence:

`accepted CEW object(s) -> CEW/BIMCraft command plan -> BIMCraft -> semantic read-back -> IFC4 -> IfcOpenShell -> CEW reconciliation receipt`

Required invariants:

- no model engine-generated identity is imported as CEW identity;
- CEW object/evidence/source/state metadata are carried into the projection;
- native BIM/IFC GUID changes do not alter semantic identity;
- mismatch on read-back fails closed;
- projection failure cannot rewrite accepted evidence.

## 9. Spiral receipts

Each cycle SHALL produce an inspectable receipt chain:

1. `ResidualSelectionReceipt`;
2. acquisition/evidence receipt from the selected channel;
3. optional grammar/similarity proposal receipt;
4. human/governance decision ref when required;
5. accepted model-delta receipt, if any;
6. projection/read-back reconciliation receipt, if projected;
7. updated residual ledger fingerprint.

Replay must reconstruct the same routing decision from the same governed inputs, independent of conversation state.

## 10. Fail-closed rules

CEW-SPIRAL-01 SHALL stop without authority escalation when:

- source identity is missing or mutable;
- a historical comparator is the only support for a primary identity claim;
- OCR and vector text conflict materially;
- grammar provenance is missing;
- similarity is used as truth rather than proposal;
- human review required by an upstream contract is absent;
- projection read-back disagrees with the accepted CEW object;
- WIP slot is not released.

## 11. Activation and success criteria

Activation requires explicit evidence that COL-03F no longer owns the only CEW WIP slot.

The program is successful only when it demonstrates, in order:

1. a read-only deterministic DXF observation slice;
2. bounded reuse of grammar/prototype/similarity without duplicate subsystems;
3. deterministic residual routing with no authority escalation;
4. at least one human/governance-accepted N12 model delta;
5. BIMCraft/IFC projection and semantic read-back of that accepted delta;
6. a subsequent spiral cycle driven by the updated residual ledger.

Until item 4 occurs, CEW-SPIRAL-01 improves acquisition and convergence but does not claim M0-G progress by model materialization.
