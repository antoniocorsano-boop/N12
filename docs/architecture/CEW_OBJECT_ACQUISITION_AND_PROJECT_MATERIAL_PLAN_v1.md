# CEW Object Acquisition & Project Material Plan v1

Status: GOVERNING DEVELOPMENT PLAN
Program: Civil Existing Workflow (CEW)
Phase: OAR — Object Acquisition & Recognition

## 1. Process priority

The acquisition process is upstream of structural modelling and project production.

Canonical sequence:

`DOCUMENT ACQUISITION -> OBJECT-TYPE RECOGNITION -> PROTOTYPE/FAMILY LEARNING -> FIND SIMILAR OBJECTS -> GUIDED HUMAN VISUAL VALIDATION -> CANONICAL CAD OBJECT -> STRUCTURAL IDENTITY -> PROJECT MATERIAL READY`

M0-G, M0-S, M0-A, EdiLus, FEM, diagnosis, intervention design and final project outputs are downstream consumers. They SHALL NOT be used to compensate for acquisition gaps.

## 2. Authority boundary

Invariant:

`document geometry != technical candidate != structural identity`

- Original SourceVersion/Page/EvidenceRegion is the evidence authority.
- A crop or rendered image is a derivative aid, never the primary operational identity.
- A canonical CAD object is an operational representation, not evidence.
- Screen coordinates SHALL NOT become canonical geometry.
- Visual proximity SHALL NOT establish identity.
- Overlay/synchronization requires a verified registration.
- Proposal does not equal acceptance.
- Structural identity requires explicit human confirmation and sufficient provenance.

## 3. OAR core loop

`Prototype -> Detect Similar -> Human Resolve -> Promote Object`

The system learns the graphical grammar of the specific project rather than assuming a universal drawing grammar.

### 3.1 Object types

Initial controlled vocabulary:

- COLUMN
- BEAM
- BEAM_SECTION
- SLAB
- FOUNDATION_BEAM
- FOUNDATION_NODE
- LONGITUDINAL_REINFORCEMENT
- STIRRUP
- GRID_AXIS
- DIMENSION
- CALLOUT
- STRUCTURAL_NODE
- TECHNICAL_TEXT

Each acquisition pass SHALL target one primary object type and its project-specific symbol grammar.

## 4. Domain entities

### ObjectPrototype
Human-taught exemplar of a project-specific graphical/technical family.

Required concepts:
- object type
- canonical CAD geometry
- geometric signature
- topological signature
- contextual signature
- associated-text pattern
- provenance
- human validation

### ObjectFamily
Project-local grouping of equivalent or near-equivalent representations. Graphical family and structural family SHALL remain distinguishable.

### ObjectCandidate
Machine- or rule-proposed instance. A candidate has no structural authority.

### CanonicalCadObject
Human-confirmed operational CAD representation with stable `cad_object_id` and evidence link.

### StructuralObject
Downstream structural identity. It SHALL be created only after the structural-identity gate and SHALL retain its evidence and CAD lineage.

Paired identity is mandatory:
- `evidence_object_id`
- `cad_object_id`
- `structural_entity_id` only after structural validation

## 5. Candidate state machine

Allowed states:

`DETECTED -> CANDIDATE -> {AMBIGUOUS | BLOCKED | HUMAN_CONFIRMED | REJECTED}`

Only `HUMAN_CONFIRMED` may become eligible for CAD promotion, and only when provenance is complete and the current authority policy explicitly permits the requested promotion.

`AMBIGUOUS`, `BLOCKED`, `REJECTED` SHALL fail closed.

## 6. Similarity model

Similarity is multi-signal, not an opaque visual score. Deterministic signals are implemented first:

1. topology/CAD primitive structure
2. shape
3. dimension ratio
4. absolute dimension where registration permits it
5. orientation
6. associated text
7. spatial relationships
8. storey/drawing context
9. nearby family/context
10. vertical persistence / correspondence
11. visual embedding as an additional signal, never sole authority
12. provenance compatibility

Human review SHALL expose the reasons for similarity.

## 7. Human Object Workbench

Primary surface: clean CAD-oriented reconstructed view.

Secondary surface: original source/evidence, opened on demand for verification.

Required visual states:
- verified
- proposal
- ambiguous
- blocked
- unanalyzed

Required review information:
- current object type
- validated/proposed/ambiguous/blocked counts
- project families
- explicit blockers
- selected candidate provenance
- similarity reasons

Minimum actions:
- `Questo è un...`
- `Trova simili`
- `Conferma`
- `Conferma gruppo`
- `Rifiuta`
- `Sposta in altra famiglia`
- `Crea nuova famiglia`
- `Confronta`
- `Vedi fonte`
- `Segna ambiguo`

## 8. Gates

- OA-G1 SOURCE_READY: immutable source/page/transform/evidence provenance exists.
- OA-G2 OBJECT_ACQUIRED: candidate geometry/signature exists.
- OA-G3 OBJECT_CLASSIFIED: object type/family classification exists.
- OA-G4 HUMAN_VERIFIED: explicit human decision exists on the exact candidate/provenance fingerprint.
- OA-G5 STRUCTURAL_IDENTITY: structural identity and required relations are explicitly resolved.
- PROJECT_MATERIAL_READY: all required project-material validators pass.

No later gate repairs an earlier one.

## 9. Project-material outputs

Downstream material may include:
- StructuralNode
- Column
- Beam
- Slab
- FoundationBeam
- FoundationNode
- Reinforcement
- Section
- Material
- Load
- Constraint
- Storey
- StructuralRelation

Every promoted record SHALL carry geometry, identity, properties, source/evidence lineage, state and human-validation lineage.

## 10. Development program

### OA-0 — Domain foundation
Implement object types, prototype/family/candidate/CAD-object identities, provenance, signatures, review decisions, state machine and fail-closed promotion policy.

### OA-1 — Human Object Workbench
Implement CAD-oriented primary review, object selection, state visualization, family summary, blocker summary and source drill-down.

### OA-2 — Human teaching
Implement `Questo è un...`, prototype creation and project-family creation/versioning.

### OA-3 — Similarity engine
Implement deterministic similarity first; add CV/embedding only as secondary evidence.

### OA-4 — Cluster validation
Implement group review, representative comparison and anomaly-first resolution.

### OA-5 — Structural resolver
Resolve same object, vertical chain, beam line, frame, family and other structural relations without conflating drawing similarity with structural identity.

### OA-6 — Project material gates
Publish deterministic readiness validators for project geometry, sections, reinforcement and foundations.

## 11. Pilot vertical slice

Pilot: `PILASTRI G4 / TAV-05S`.

Purpose:
- validate the domain model against a bounded structural-object class;
- use registered source/evidence references where available;
- learn project-local column symbol families;
- expose candidates/families/blockers in the Workbench;
- prove fail-closed promotion before extending to beams/foundations/reinforcement.

The pilot SHALL NOT manufacture missing human decisions, structural identity or canonical-write authority.

## 12. Current governance constraint

This tranche is based on the governing CEW candidate where professional HVA, B1 promotion and canonical writes remain unauthorized. Therefore OA-0/OA-1 may create domain contracts, candidate/work state and review UI, but SHALL NOT enable canonical engineering writes or assert real professional validation.

## 13. Acceptance criteria for first tranche

OA-0/OA-1 first slice is acceptable only if:

1. provenance is explicit and fingerprintable;
2. object candidate and structural identity are distinct types;
3. review is bound to exact candidate/provenance fingerprint;
4. ambiguous/blocked/rejected objects cannot promote;
5. absent human confirmation cannot promote;
6. absent authority cannot write canonical engineering state;
7. the Workbench can present object/family/blocker state without relying on image crops as its primary operational representation;
8. source evidence remains reachable for audit;
9. pilot data can be represented without inventing structural conclusions;
10. validators are deterministic and fail closed.
