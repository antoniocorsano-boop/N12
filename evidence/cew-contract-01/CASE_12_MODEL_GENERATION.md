# CASE 12 — N12 ModelGeneration reale

**Gate:** C01-T02, C01-T09, C01-T10  
**Operational SHA:** `d806dcca72779b5a186defe557a7a9b739575a90`  
**Workflow run:** `32955421352` — Validate CEW Structural Model Builder — PASS  
**Artifact:** `9601773275` — `N12-CEW-canonical-structural-model-v0`

## Scopo

Formalizzare come `ModelGeneration` CEW una trasformazione N12 realmente eseguita e verificata, senza introdurre alcun SolverRun.

## Input e output

Il builder `scripts/cew_structural_model_builder.py` consuma sei artefatti canonici/promossi identificati nel manifest `N12_CEW_MODEL_GENERATION_v1.json`; il JSON prodotto dal run storico incorpora i loro SHA-256.

L'output reale `N12_CEW_CANONICAL_STRUCTURAL_MODEL_v0.json` è stato recuperato dall'artifact GitHub Actions non scaduto e ha SHA-256:

`4e1c3f341093e9b60670099802bdee0c5fcdc174b12aedb63922f49301a965b2`

L'archivio artifact è registrato da GitHub con digest:

`sha256:5278bec007f427f6535947343b29d0f586da461f4acdac6aa4502aea73a1d5a5`

## Verification

Il workflow ha verificato deterministicamente l'inventario e le relazioni principali: 629 nodi di sovrastruttura, 165 support-core, 464 face-node, 464 rigid offset, 359 membri ordinari, 38 supporti e 55 membri di fondazione, 6 geometrie speciali di copertura, nessuna topologia creata per prossimità, modello solver-independent e un solo residuo geometrico dichiarato (`FOUNDATION_NUMERIC_Z`).

## Snapshot e scenario

Per questa qualifica `canonical_snapshot_id` è un riferimento congelato all'input-set sul commit operativo esatto; non pretende di sostituire il futuro schema fisico di CanonicalSnapshot. `scenario_id` è esplicitamente `null`: il run del builder non applica uno Scenario CEW.

## Assurance

La receipt `N12_CEW_MODEL_GENERATION_RECEIPT_v1.json` registra commit, workflow, artifact, input digest, output digest e verifica. È classificata `QUALIFICATION_RECEIPT`, non `Result` ingegneristico.

## Guardrail

- `solver_authorized=false`;
- `calculation_model_ready=false`;
- nessun `SolverRun` creato;
- nessun `Result` creato;
- il residuo `FOUNDATION_NUMERIC_Z` resta ND;
- il modello derivato non diventa evidenza primaria.

Questo caso chiude la prova di riproducibilità della `ModelGeneration` nel perimetro CEW-CONTRACT-01; la prova `ModelGeneration → SolverRun → Result` resta obbligatoria in CEW-FEM-01.
