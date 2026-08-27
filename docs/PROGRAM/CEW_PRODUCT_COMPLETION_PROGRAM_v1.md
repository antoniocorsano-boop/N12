# CEW Product Completion Program v1

Status: EXECUTION PROGRAM  
Date: 2026-08-27  
Reference product: CEW / CEW-EX  
Reference project: N12  
Architecture PR: #95  
Program goal: `CEW-GOAL-01`

## 1. Goal

Deliver CEW as a production-grade, human-centred operating environment for structural assessment of existing structures.

A responsible structural engineer shall be able to progress through:

`PROJECT -> SOURCES -> EVIDENCE -> HISTORY/SURVEY -> RECONSTRUCTION -> STRUCTURAL MODEL -> PROPERTIES -> CONDITION -> INVESTIGATION -> AS-IS -> SCENARIOS -> SOLVER HANDOFF -> FEM -> VERIFICATION -> INTERVENTION -> AS-BUILT/MONITORING -> DOSSIER`

without repository knowledge and while preserving bidirectional traceability:

`SOURCE -> EVIDENCE -> CLAIM -> ENTITY/PROPERTY -> GENERATION -> SCENARIO -> SOLVER PROJECTION -> RESULT -> VERIFICATION -> DECISION`

and:

`DECISION/BLOCKER -> IMPACT -> INFORMATION NEED -> WORK PACKAGE -> EVIDENCE ACQUISITION -> CLAIM UPDATE -> NEW AUTHORIZED GENERATION`.

## 2. Definition of done

`CEW-GOAL-01` is COMPLETE only when all of the following are true:

1. CEW product state and N12 engineering state are formally separated and machine-reconciled.
2. P0-P16 exist as runtime product primitives with gates and deliverables.
3. Project Home communicates phase, blockers, solver eligibility and next actions without requiring internal IDs.
4. Source Hub supports immutable intake/versioning and source-use state.
5. Evidence Workspace shows MICRO/MESO/MACRO source context, linked engineering entity and human decision on one screen.
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
17. Applicable DATA, ENGINEERING, HUMAN, INTEGRATION, HUMAN-FACTORS, SECURITY and PRODUCTION gates pass.
18. No decision-grade feature requires direct editing of repository files.

## 3. Operating model

Preparation may be parallel. Promotion is serialized.

- Specialist agents may analyze and prepare one bounded work package.
- Each agent returns exactly one result package.
- Agents cannot promote engineering facts or approve professional decisions.
- The Product Orchestrator selects the next eligible promotion item from the persistent queue.
- Human engineering authority stops an item at `HUMAN_AUTHORITY_REQUIRED`.
- N12 engineering state remains authoritative for N12 engineering facts.
- CEW product state remains authoritative for CEW runtime/product maturity.
- UI, agent output and solver output are not canonical engineering authority.

## 4. Standing agent board

| Agent | Goal | Forbidden authority |
|---|---|---|
| `PRODUCT_STATE_AGENT` | eliminate product-state drift and project N12 engineering state into CEW phases | changing N12 engineering facts |
| `HUMAN_FACTORS_AGENT` | make each workspace answer one dominant engineering question and pass representative tasks | engineering approval |
| `SOURCE_EVIDENCE_AGENT` | deliver immutable source intake and contextual evidence resolution | silent claim promotion |
| `RECONSTRUCTION_AGENT` | integrate source, 2D, table, 3D and residuals over stable identities | proximity-based connectivity |
| `PROPERTIES_INVESTIGATION_AGENT` | expose properties, blockers and executable investigations | inventing missing inputs |
| `RULE_SCENARIO_AGENT` | make information requirements, rule packs and scenarios explicit/versioned | adopting rules without human approval |
| `SOLVER_FEM_AGENT` | build current-canonical solver projections and result round trip | treating solver output as evidence |
| `VERIFICATION_INTERVENTION_AGENT` | build verification, intervention and lifecycle workflows | final professional approval |
| `QA_ASSURANCE_AGENT` | independently validate contracts, traceability, human factors and release readiness | altering engineering meaning to make tests pass |
| `PRODUCT_ORCHESTRATOR` | select dependencies, validate result handshakes and control release | bypassing agent/human gates |

## 5. Execution waves

### Wave A — Product spine

- A0 State Reconciliation Gate
- A1 Lifecycle domain model
- A2 Project Home v2
- A3 Terminology/identity layer
- A4 Human-factors acceptance harness

### Wave B — Source to model

- B1 Source Hub
- B2 Evidence Workspace
- B3 Reconstruction Workspace
- B4 Structural Model Workspace
- B5 Engineering Properties workspaces

### Wave C — Assessment readiness

- C1 Engineering Rule Pack
- C2 Information Requirements
- C3 Executable Investigation Workspace
- C4 Knowledge/LC-FC decision pack
- C5 AS-IS generation and scenarios

### Wave D — Solver/FEM

- D0 Retire stale FEM prototype authority
- D1 Solver-neutral projection
- D2 Current-canonical OpenSees adapter
- D3 EdiLus handoff/mapping
- D4 Analysis run + immutable result bundle
- D5 Result import / engineering-twin maps
- D6 Independent benchmark path

### Wave E — Verification and lifecycle

- E1 Verification Workspace
- E2 Sensitivity/uncertainty
- E3 Intervention generations
- E4 Executed/As-built generation
- E5 Monitoring/reassessment
- E6 Technical Dossier Builder

### Final gate

- Z0 `CEW-GOAL-01` Production Acceptance

## 6. Stop rules

The orchestrator stops rather than guesses when:

- an engineering decision requires human authority;
- required primary evidence is missing;
- a source/evidence conflict is unresolved;
- a product capability is not backed by runtime/CI evidence;
- a solver adapter cannot represent a structural feature;
- result-to-entity mapping is incomplete;
- human-factors acceptance shows that a representative task cannot be completed safely and intelligibly.

## 7. Completion policy

The queue may not be declared complete by documentation alone. Every item requires:

- declared outputs;
- validation evidence;
- a result receipt;
- completed dependencies;
- applicable human authority;
- no unresolved blocking gate.

The final production acceptance must demonstrate the complete source-to-decision round trip on N12 without requiring repository knowledge.
