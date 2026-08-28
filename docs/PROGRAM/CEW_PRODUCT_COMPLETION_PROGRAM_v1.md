# CEW Product Completion Program v1

Status: EXECUTION PROGRAM  
Date: 2026-08-28  
Reference product: CEW / CEW-EX  
Reference project: N12  
Architecture PR: #95  
Program goal: `CEW-GOAL-01`  
Governing agency model: `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`  
Current development model: `docs/PROGRAM/CEW_CODE_DEVELOPMENT_MODEL_v2.md`  
Current human-centred model: `docs/PROGRAM/CEW_HUMAN_CENTRED_GOVUK_MODEL_v2.md`

## 1. Goal

Deliver CEW as a production-grade, human-centred operating environment for structural assessment of existing structures.

A responsible structural engineer shall be able to progress through:

`PROJECT -> SOURCES -> EVIDENCE -> HISTORY/SURVEY -> RECONSTRUCTION -> STRUCTURAL MODEL -> PROPERTIES -> CONDITION -> INVESTIGATION -> AS-IS -> SCENARIOS -> SOLVER HANDOFF -> FEM -> VERIFICATION -> INTERVENTION -> AS-BUILT/MONITORING -> DOSSIER`

without repository knowledge and while preserving bidirectional traceability:

`SOURCE -> EVIDENCE -> CLAIM -> ENTITY/PROPERTY -> GENERATION -> SCENARIO -> SOLVER PROJECTION -> RESULT -> VERIFICATION -> DECISION`

and:

`DECISION/BLOCKER -> IMPACT -> INFORMATION NEED -> WORK PACKAGE -> EVIDENCE ACQUISITION -> CLAIM UPDATE -> NEW AUTHORIZED GENERATION`.

The product is developed as capabilities and representative professional journeys, not as isolated pages or AI features.

## 2. Definition of done

`CEW-GOAL-01` is COMPLETE only when all of the following are true:

1. CEW product state and N12 engineering state are formally separated and machine-reconciled.
2. P0-P16 exist as runtime product primitives with gates and deliverables.
3. Project Home communicates phase, blockers, solver eligibility and next actions without requiring internal IDs.
4. Source/Document capability supports immutable intake/versioning, drawing discovery, governed viewing and source-use state.
5. Evidence capability shows source context, linked engineering meaning and human review without exposing internal identifiers as the primary workflow.
6. Reconstruction Workspace synchronizes source, 2D, table, 3D and residual context.
7. Engineering Properties workspaces expose provenance and epistemic state for sections, reinforcement, materials, loads, foundations and geotechnics.
8. Investigation workflow runs end-to-end from blocker to field/test result to updated claim.
9. AS-IS generation and scenario/rule-pack authorization are first-class.
10. A solver-neutral projection is generated from the current canonical model.
11. A current-canonical OpenSees adapter exists; `M0-OS-0002` remains historical prototype only.
12. EdiLus handoff/mapping explicitly distinguishes automated and manual boundaries.
13. FEM run receipts and immutable result bundles map back to CEW entity IDs.
14. Verification Workspace maps demand/capacity/failure mode to rules, scenarios, results and evidence gaps.
15. Intervention alternatives create new generations; AS-IS history remains immutable.
16. Dossier/Audit reconstructs the complete decision chain.
17. Applicable DATA, ENGINEERING, HUMAN, INTEGRATION, HUMAN-FACTORS, ACCESSIBILITY, SECURITY and PRODUCTION gates pass.
18. No decision-grade feature requires direct editing of repository files.
19. User-facing capabilities have representative human evidence with participant/reviewer separation and no unresolved non-compensable safety/authority error.
20. Production promotion is based on same-revision evidence and not inferred from CI or deployment status alone.

## 3. Product operating model

CEW specializes the repository-wide AI-native Product Agency model.

Preparation and verification may be parallel. Promotion is serialized.

- Product work begins from a need/capability and representative journey.
- Specialist agents may analyze and prepare one bounded work package.
- Each promotable slice has one promotion owner.
- Independent support agents may block but cannot promote.
- Human research/evaluation and professional engineering authority are distinct.
- The Product Orchestrator selects the next eligible promotion item from the persistent queue.
- Human engineering authority stops an item at `HUMAN_AUTHORITY_REQUIRED` where declared.
- N12 engineering state remains authoritative for N12 engineering facts.
- CEW product state remains authoritative for CEW runtime/product maturity only.
- UI, agent output and solver output are not canonical engineering authority.
- Deployment, Production and canonical authority remain distinct dimensions.

## 4. Standing agent board

| Agent | Goal | Forbidden authority |
|---|---|---|
| `PRODUCT_STATE_AGENT` | eliminate product-state drift and project N12 engineering state into CEW phases | changing N12 engineering facts |
| `HUMAN_FACTORS_AGENT` | research/evaluate real professional journeys and reduce comprehension/error risk | engineering approval or unilateral release approval |
| `SOURCE_EVIDENCE_AGENT` | deliver immutable source intake, document/drawing use and contextual evidence resolution | silent claim promotion |
| `RECONSTRUCTION_AGENT` | integrate source, 2D, table, 3D and residuals over stable identities | proximity-based connectivity |
| `PROPERTIES_INVESTIGATION_AGENT` | expose properties, blockers and executable investigations | inventing missing inputs |
| `RULE_SCENARIO_AGENT` | make information requirements, rule packs and scenarios explicit/versioned | adopting rules without human approval |
| `SOLVER_FEM_AGENT` | build current-canonical solver projections and result round trip | treating solver output as evidence |
| `VERIFICATION_INTERVENTION_AGENT` | build verification, intervention and lifecycle workflows | final professional approval |
| `SECURITY_ASSURANCE_AGENT` | independently test authentication, isolation, fail-closed behavior and privacy boundaries | product promotion |
| `AUTHORITY_AUDIT_AGENT` | independently test canonical/provenance/professional-authority boundaries | changing engineering authority |
| `QA_ASSURANCE_AGENT` | independently validate contracts, traceability, regressions and release readiness | altering engineering meaning to make tests pass |
| `PRODUCT_ORCHESTRATOR` | select dependencies, validate result handshakes and control release | bypassing agent/human gates |

The same person may temporarily fulfil more than one human role, but the authority roles remain logically distinct and evidence must record which role was exercised.

## 5. Capability delivery model

Every user-facing work item declares:

`NEED -> CAPABILITY -> REPRESENTATIVE JOURNEY -> SLICE -> CANDIDATE -> HUMAN EVIDENCE -> RELEASE -> OBSERVATION -> PROMOTION`

The product state distinguishes:
- technical delivery;
- human evidence;
- deployment/release ring;
- promotion;
- professional/engineering authority.

A single `COMPLETE` flag cannot substitute for these dimensions.

## 6. Current Source / Document / Evidence programme — B1

B1 was reopened after real use showed that CEW exposed evidence review before providing a sufficiently usable P1/P2 document-and-drawing journey.

The capability goal is now:

> **A structural engineer can find, inspect and verify governed project drawings and move between drawing context and evidence without repository knowledge or authority confusion.**

### Prepared slices

- **B1.1 — Document & Drawing Foundation** — document library/drawing register foundation.
- **B1.2 — Governed Drawing Viewer** — display-only viewer, orientation/zoom/pan and governed overlays.
- **B1.3 — DocumentMap** — governed document-understanding layer over READY pages.
- **B1.4 — Intake & Versioning** — metadata-first intake/version analysis; private byte persistence remains separately governed.
- **B1.5 — Machine Document Candidates** — OCR/vector/AI outputs normalized into noncanonical candidates.
- **B1.6 — EvidenceRegion Candidate Boundary** — reviewed candidate geometry remains distinct from F2 EvidenceRegion authority.
- **B1.7 — Usability/HVA Instrument v1** — automated instrument implemented and deterministic gates validated.

### B1.7 human finding

Direct use of the first B1.7 Acceptance Lab showed that the participant surface mixed professional work, test telemetry, outcome entry, release decision and receipt export. The instrument therefore **must not be used as the target promotion interaction without redesign**.

This does not automatically mean the B1 product journey failed. It is an observed Human Factors defect in the acceptance instrument.

Decision: `docs/DECISIONI/PRODUCT_HF_001_PARTICIPANT_REVIEWER_SEPARATION_v1.md`.

### B1.8 — Human-Centred Acceptance v2

Current required B1 follow-on:

- separate participant surface from reviewer surface;
- show one professional task at a time;
- hide live test counters/internal gate/runtime terminology from participants;
- collect telemetry in the observation layer;
- add post-task mental-model checks;
- distinguish usability residuals from non-compensable safety/authority blockers;
- make reviewer decision and receipt generation separate;
- run the four representative B1 tasks on one immutable candidate;
- after HVA PASS, perform required Production smoke on the same accepted revision;
- only then promote B1 and freeze the CEW promoted baseline.

Machine contract: `automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json`.

### B1 promotion blockers

B1 remains `IN_PROGRESS` until all required B1.1-B1.8 dependencies are reconciled and, where applicable:
- private document-byte persistence boundary is authorized or explicitly scoped out of the promoted capability;
- EvidenceRegion candidate persistence/promotion boundary is authorized or explicitly scoped out;
- v2 Human Acceptance passes;
- same-revision Production smoke passes;
- durable receipt is archived;
- Product Orchestrator promotes B1.

## 7. Execution waves after B1

### Wave B2 — Reconstruction and structural model

B2 remains blocked from promotion while B1 is incomplete. Preparation may continue only where it does not require unresolved B1 authority or persistence semantics.

- Reconstruction Workspace
- Structural Model Workspace
- Engineering Properties workspaces

### Wave C — Assessment readiness

- Engineering Rule Pack
- Information Requirements
- Executable Investigation Workspace
- Knowledge/LC-FC decision pack
- AS-IS generation and scenarios

### Wave D — Solver/FEM

- retire stale FEM prototype authority;
- solver-neutral projection;
- current-canonical OpenSees adapter;
- EdiLus handoff/mapping;
- analysis run + immutable result bundle;
- result import / engineering-twin maps;
- independent benchmark path.

### Wave E — Verification and lifecycle

- Verification Workspace
- sensitivity/uncertainty
- intervention generations
- executed/as-built generation
- monitoring/reassessment
- Technical Dossier Builder

### Final gate

- Z0 `CEW-GOAL-01` Production Acceptance

## 8. Human evidence policy

CEW uses three human-evidence modes:

1. **formative research** — understand professional workflow and needs;
2. **evaluative usability / Human Factors** — observe prototypes/candidates and iterate;
3. **release HVA** — reviewer decision on an immutable candidate.

The participant performs professional work; the evaluation system observes. The participant does not operate internal release governance.

Critical wrong-source/version, provenance, project/scope, authority or canonical-write misunderstandings are non-compensable blockers. Efficiency metrics cannot offset them.

## 9. Release rings

Default CEW rings:

`DEV -> PREVIEW -> HUMAN EVALUATION -> PILOT where required -> PRODUCTION -> OBSERVED PRODUCTION`

A successful Preview or Production deployment does not imply promotion or canonical engineering authority.

## 10. Stop rules

The orchestrator stops rather than guesses when:

- an engineering decision requires human authority;
- required primary evidence is missing;
- a source/evidence conflict is unresolved;
- source/version identity is unresolved;
- a product capability lacks required runtime/CI evidence;
- human evaluation produces a non-compensable safety/authority error;
- the acceptance evidence belongs to another revision;
- project/scope isolation fails;
- a solver adapter cannot represent a required structural feature;
- result-to-entity mapping is incomplete;
- product continuity would require inventing or lossily normalizing engineering information.

## 11. Completion policy

The queue may not be declared complete by documentation alone. Every promotable item requires:

- declared capability outcome and representative journey;
- declared outputs;
- deterministic validation evidence;
- independent assurance where required;
- applicable human evidence;
- a result receipt;
- completed dependencies;
- applicable human/professional authority;
- required release/smoke evidence;
- no unresolved blocking gate.

The final production acceptance must demonstrate the complete source-to-decision round trip on N12 without requiring repository knowledge and with bidirectional provenance available at the professional decision point.
