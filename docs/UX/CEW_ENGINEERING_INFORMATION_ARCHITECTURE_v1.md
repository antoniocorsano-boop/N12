# CEW Engineering Information Architecture v1

Status: `UX FOUNDATION — EXPERIMENTAL / NON-PROMOTIVE`

## Navigation follows engineering work

Primary project navigation: **Quadro progetto; Fonti e tavole; Modello strutturale; Materiali e armature; Carichi; Analisi; Stato e degrado; Indagini; Interventi; Quantità e costi; Fascicolo.** Repository concepts, agents and CI gates are not primary navigation destinations.

## Workspace anatomy

- left rail — project/domain navigation and scoped task queues;
- top context bar — project, state/generation, level/zone, selected entity/task;
- central workspace — drawing, 3D, table, graph, analysis or comparison;
- right inspector — properties, epistemic states, evidence, residuals and scenario/result bindings;
- decision trail — collapsible source → observation → interpretation → decision → model chain.

## Cross-navigation

Every supported structural entity exposes: `Apri nella tavola · Mostra nel modello · Vedi proprietà · Vedi provenienza · Vedi residui`.

Every evidence region exposes: `Apri fonte · Mostra osservazione · Mostra entità candidate · Mostra decisioni`.

Every analysis result exposes: `Scenario · Assunzioni · Entità coinvolte · Solver mapping · Evidenza a monte`.

## Progressive technical disclosure

Level 1: engineering statement. Level 2: supporting source/model context. Level 3: full provenance including internal IDs, generations, hashes, receipts and detector/solver versions. Complexity is staged, never irreversibly hidden.

## Empty and blocked states

A blocked state explains what is unavailable, why it matters, which upstream evidence/decision is missing, whether CEW can continue elsewhere, and the next valid action.

## UX1 first vertical slice

`primary drawing + frozen EvidenceRegion + structural context/entity candidates + epistemic state + bounded human decision + receipt preview`.

UX1 is an experimental work item, not a canonical CEW milestone. It reads frozen `CEW-F2` geometry and cannot relocalize evidence, close F2, emit `EVIDENCE_PROVENANCE_PASS`, or authorize F3 or any later canonical milestone.
