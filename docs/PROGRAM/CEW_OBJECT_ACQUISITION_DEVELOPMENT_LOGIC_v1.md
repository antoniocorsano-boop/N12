# CEW Object Acquisition & Recognition — Development Logic v1

**Status:** `OA-0 FOUNDATION`  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Governing priority

CEW must acquire and validate project objects before downstream modeling.

Canonical sequence:

`Source -> Document registration -> Type-specific object pass -> Prototype/Family -> Find Similar -> Human cluster review -> Canonical CAD object proposal -> Structural identity review -> Project material -> M0-G/M0-S/M0-A -> engineering model`

M0-G, M0-S, M0-A, EdiLus, FEM, assessment and intervention design are downstream consumers. They must not be used to repair missing acquisition upstream.

## 2. Unit of work

The unit of document understanding is an **object**, not a line and not a crop.

A crop may support provenance and review. The operational representation must be a current CAD/vector object or scene object linked back to immutable evidence.

## 3. Type-specific passes

The operator chooses one object type per pass. Initial types include columns, beams, beam-section symbols, slabs, foundation beams, longitudinal reinforcement, stirrups, axes, dimensions, callouts, nodes and technical text.

The system does not ask a global question such as “what is in the drawing?”. It runs bounded questions such as “find columns in this drawing”.

## 4. Human teaching loop

Primary loop:

`select -> This is a... -> create/reuse prototype -> Find Similar -> review cluster -> confirm/reject/ambiguous -> repeat`

Human effort is concentrated on exceptions and blockers. Batch confirmation is permitted only for an explicit reviewed cluster on the same governed source/revision.

## 5. Project-specific graphic grammar

CEW learns the graphic grammar of the project rather than assuming a universal drafting convention.

`ObjectPrototype` captures a documented example. `ObjectFamily` groups approved project-specific representations. Similarity may use geometry, dimensions, orientation, topology, spatial context and associated text. Vision embeddings may be added later but cannot create authority.

## 6. Workbench interaction

OA extends the existing Professional Workbench at `/workbench`; it must not create a parallel product.

Primary view: clean technical/CAD scene.

Source view: on-demand evidence/provenance.

The interface must visibly distinguish:

- verified;
- proposed;
- ambiguous;
- blocking;
- not analysed.

The blocking panel is a first-class surface and must explain why the current type pass or gate cannot close.

## 7. Authority boundaries

- immutable source remains probative authority;
- visual similarity does not establish structural identity;
- detector confidence is not engineering confidence;
- human validation of a graphic object is not automatically structural validation;
- CAD reconstruction is an operational representation, not a substitute for source evidence;
- OA cannot bypass R2GM geometry acceptance where R2GM is required;
- no OA-0 artifact authorizes canonical engineering writes.

## 8. Promotion gates

- `OA-G1 SOURCE_READY`
- `OA-G2 OBJECT_ACQUIRED`
- `OA-G3 OBJECT_CLASSIFIED`
- `OA-G4 HUMAN_VERIFIED`
- `OA-G5 STRUCTURAL_IDENTITY`

Only the complete gate chain for a target scope may emit `PROJECT_MATERIAL_READY`.

## 9. Development sequence

### OA-0 — Foundation
Persist object contracts, gates, queue, validator and integration boundary.

### OA-1 — Human Workbench
Add type filter, CAD-first scene, family panel, object inspector, blocker panel and source disclosure.

### OA-2 — Human Teaching
Implement `This is a...`, prototype creation and family assignment.

### OA-3 — Deterministic Similarity
Geometry/dimension/orientation/topology/context matching, with explicit reason codes.

### OA-4 — Cluster Review
Human batch review with exceptions, ambiguity and rejection handling.

### OA-5 — Structural Resolver
Resolve same-object/family/vertical-chain/frame/member relationships without proximity-only identity.

### OA-6 — Project Material Gate
Emit governed project-material packages consumable by M0-G/M0-S/M0-A.

## 10. Pilot

First pilot: **columns on one governed structural drawing**.

Success is not measured by number of recognized marks. The pilot succeeds when one human-taught column prototype can produce a reviewable similarity cluster, human decisions are persisted non-canonically with provenance, blockers are explicit, and approved objects can reach an OA gate state without inventing structural identity.

## 11. Current boundary

This OA-0 branch is stacked on CEW B1.8 / Professional Workbench head `f0f829cd5afdadbcc1eecb0f9d3a3fb38c962efa`.

It does not assert professional HVA, real R2HR/R2GM project decisions, Production deployment, B1 promotion, `CEW_PROMOTED_BASELINE`, or canonical engineering authority.
