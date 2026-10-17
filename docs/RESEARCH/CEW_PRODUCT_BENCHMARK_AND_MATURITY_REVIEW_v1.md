# CEW Product Benchmark and Maturity Review v1

Status: RESEARCH / PRODUCT DESIGN BASIS
Date: 2026-08-24

## Purpose

This review benchmarks CEW / Civil Existing Workflow against mature patterns in information management, BIM/openBIM collaboration, digital twins, structural-model collaboration and asset lifecycle management. It is not a claim of product equivalence and does not import vendor-specific architecture blindly.

## Reference patterns reviewed

### ISO 19650 family

Relevant product pattern:
- information management is broader than 3D modelling;
- information containers are persistent, recorded, versioned and organized;
- information-use status is governed separately from technical correctness;
- information can be federated from separate sources;
- the framework spans the full built-asset lifecycle.

CEW adoption:
- Source / InformationContainer as first-class records;
- CDE-like states WORKING / SHARED / REVIEW / APPROVED / SUPERSEDED / ARCHIVED;
- these use-status states stay separate from epistemic states DOC/MIS/RIF/INF/INC/ND;
- federated project model rather than one-file authority.

### buildingSMART IFC

Relevant product pattern:
- open, tool-independent exchange schema;
- stable model identity and workflow-specific exchange requirements.

CEW adoption:
- native solver-independent canonical graph remains authoritative;
- external ID registry to map CEW entity IDs to IFC GUIDs, solver IDs and other external systems;
- IFC is an interoperability projection where semantics fit, not the only canonical representation.

### buildingSMART BCF

Relevant product pattern:
- issues are contextual model objects;
- issue communication can include view, screenshot, coordinates and linked model elements;
- file and REST exchange mechanisms.

CEW extension:
- CEW Issue/Residual includes BCF-like context plus epistemic state, source snippets, engineering impact, affected verification scope, resolution routes, assigned specialist/agent, closure evidence and gate receipt.

### Bentley iTwin platform

Relevant product pattern:
- federating engineering data from multiple tools;
- alignment with reality data and other associated datasets;
- visualizing and tracking changes across asset lifecycle;
- APIs/services rather than requiring one authoring tool.

CEW adoption:
- canonical engineering graph + source evidence + inspections + solver results + future monitoring;
- no solver or CAD authoring package is the universal source of truth;
- lifecycle generations and overlays remain queryable.

### Tekla Structures / Model Sharing / Trimble Connect

Relevant product pattern:
- explicit model ownership;
- collaboration around a common model state;
- local/shared workflows;
- interoperability with other products and coordination platforms.

CEW adoption:
- explicit project/model-generation ownership and approvals;
- work-package isolation for agents and specialists;
- immutable receipts and controlled promotion to canonical generation;
- future synchronization/merge semantics must preserve entity identity and conflicts instead of last-write-wins engineering data.

### ISO 55000:2024 asset management

Relevant product pattern:
- lifecycle value and outcomes;
- assurance, adaptability, sustainability;
- maturity improvement rather than one-time project completion.

CEW adoption:
- product maturity L0-L6;
- intervention and monitoring generations;
- assessment decisions linked to objectives and future asset state.

### Existing-structure assessment frameworks (fib / ISO 16311 family)

Relevant product pattern:
- data acquisition;
- condition assessment;
- performance prediction;
- decision/intervention;
- through-life reassessment.

CEW adoption:
- Evidence Reconstruction -> Condition/Exposure -> Assessment Scenarios -> Investigation -> Solver Verification -> Intervention -> Monitoring.

## Competitive/product differentiation

CEW should not compete with high-end BIM/CDE products by rebuilding every authoring or document-management feature.

CEW differentiates through:

1. epistemic state as a first-class property;
2. claim-to-source provenance at engineering-property granularity;
3. residuals that remain actionable rather than hidden warnings;
4. visual evidence snippets bound to claims/entities;
5. incomplete canonical models that remain valid and useful;
6. multi-mode existing-structure assessment;
7. investigation planning linked to model sensitivity and future Value of Information;
8. degradation / condition overlays that cannot overwrite measurements;
9. round-trip solver identity;
10. intervention generations and auditability.

## Product anti-patterns to avoid

- "single giant model file" as the only truth;
- last-write-wins for engineering claims;
- AI confidence used as evidence state;
- visually complete 3D model interpreted as calculation readiness;
- issue lists detached from model/source context;
- independent document repository and analysis model with weak lineage;
- hidden assumptions in solver adapters;
- mixing historical, current, modeled and post-intervention properties;
- forcing all domains to be complete before unrelated work can advance;
- exposing internal repository mechanics as the primary technician UX.

## Maturity target

### L0 Document repository
Files are stored.

### L1 Traceable evidence
Claims, snippets, source lineage and conflicts are queryable.

### L2 Canonical reconstruction
Identity, geometry, topology and property graphs are controlled.

### L3 Interactive engineering twin
2D/3D maps, evidence, residuals and project state are synchronized.

### L4 Assessment-ready
Investigation planner, scenarios, solver adapters and result round-trip are production-grade.

### L5 Decision-ready
Sensitivity, uncertainty, true Value of Information and intervention comparison support decisions.

### L6 Lifecycle twin
Executed intervention, monitoring and subsequent reassessment form a continuous asset history.

## Current N12 reference position

N12 demonstrates:
- extensive L1 evidence/provenance infrastructure;
- L2 canonical geometry/topology and structural graph;
- early L3 structural viewer + evidence/scenario overlays;
- early L4 assessment, investigation and degradation safety components.

N12 is not L4 complete because current calculation-model readiness is still blocked by unresolved current materials/knowledge, numeric loads/combinations, foundation numeric Z, some foundation property bindings, reinforcement residuals and current geotechnical characterization.

## Product acceptance principle

CEW should be considered mature only when every major engineering conclusion supports bidirectional navigation:

SOURCE -> CLAIM -> MODEL -> SCENARIO -> SOLVER -> RESULT -> DECISION

and

DECISION / BLOCKER -> IMPACT -> RESOLUTION PATH -> EVIDENCE ACQUISITION -> CLAIM UPDATE -> NEW MODEL GENERATION.
