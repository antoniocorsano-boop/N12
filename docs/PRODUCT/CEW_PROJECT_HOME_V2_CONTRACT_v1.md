# CEW Project Home v2 — Product Contract

Status: A2 implementation contract  
Program goal: `CEW-GOAL-01`

## Purpose

Project Home is the authenticated starting surface for the structural engineer. It must answer, without repository knowledge:

1. What project am I working on?
2. What is currently established and what is not?
3. What requires my attention now?
4. Where am I in the engineering lifecycle?
5. What can CEW do next without exercising engineering authority for me?

Project Home is a product navigation and decision-orientation surface. It is **not** an engineering authority and does not promote evidence, close residuals, approve rules, authorize solver execution or issue structural conclusions.

## Primary information architecture

The first screen MUST present the following hierarchy:

- **Progetto** — project identity and assessment context.
- **Stato del lavoro** — concise product/engineering readiness state, including explicit incomplete states.
- **Cosa richiede attenzione** — actionable human-review or information-completion items.
- **Percorso di valutazione** — P0–P16 lifecycle grouped into understandable professional stages.
- **Accessi di lavoro** — Sources, Evidence, Reconstruction, Structural Model, Properties, Condition, Investigations, Scenarios, Analysis/FEM, Verification, Interventions, Dossier/Audit.

Internal implementation identifiers such as `ERW-*`, `M1E-*`, `F7`, workflow names, branch names, commit SHAs and gate IDs MUST NOT be required to understand or navigate the primary workflow. They may be available in a technical detail layer.

## Engineer-first terminology

Primary labels MUST use professional engineering language. Examples:

- `Residual` → **Dato da completare** or **Questione aperta** depending on context.
- `Human Review Task` → **Revisione evidenza**.
- `EvidenceRegion` → **Regione di evidenza** only in the provenance/detail layer; primary UI should say **Fonte da verificare**.
- `Current Work Item` → **Attività corrente**.
- `Calculation Model Ready = false` → **Modello di calcolo non ancora autorizzabile**.
- `HUMAN_AUTHORITY_REQUIRED` → **Decisione dell’ingegnere richiesta**.

The terminology layer must preserve the underlying canonical/internal identifier but treat it as secondary metadata.

## Project Home state rules

Project Home may read:

- CEW product/runtime state from `data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json`;
- N12 issue and evidence task registries through their governed readers;
- lifecycle definitions from `automation/CEW_PROJECT_LIFECYCLE_MODEL_v1.json`.

It MUST NOT infer engineering completion from phase position, UI progress, number of documents, number of extracted entities, or solver availability.

A phase may be shown as available/in progress while engineering blockers remain open. The UI must preserve that distinction.

## Attention model

The attention area must prioritize human-actionable items using human-readable questions. For evidence review:

- show the engineering question first;
- show source identity/context next;
- show what is already known and what remains unknown;
- offer a clear action such as **Rivedi evidenza**;
- keep internal task/residual IDs in an expandable or technical-detail context, not as the card title.

No card may imply that opening or submitting a review automatically changes canonical engineering data.

## Lifecycle presentation

P0–P16 must be visible as a professional lifecycle, but not as a forced wizard. Grouping for Project Home v2:

1. **Definisci e raccogli** — P0–P2
2. **Ricostruisci e comprendi** — P3–P8
3. **Completa la conoscenza** — P9
4. **Prepara il modello di valutazione** — P10–P12
5. **Analizza e verifica** — P13–P14
6. **Progetta e gestisci l’intervento** — P15–P16

Every group must remain traceable to the exact P-phase IDs in the lifecycle model.

## Technical Control Room

The existing technical Control Room is retained as a secondary diagnostics/audit surface at a non-primary route. It may expose issue IDs, task IDs, gate states and implementation detail. It must not be the default landing page.

## Human-factors acceptance fixtures

A2 passes only if automated acceptance verifies at least the following:

### HF-HOME-01 — Orientation

An authenticated engineer landing on `/` can identify project, readiness state, current attention items and lifecycle without seeing a repository-oriented dashboard as the primary experience.

### HF-HOME-02 — Action clarity

At least one evidence-review item exposes a human-readable engineering question and a `Rivedi evidenza` action without requiring the user to interpret `ERW`, `M1E` or `F7`.

### HF-HOME-03 — Authority clarity

The home page explicitly states that CEW supports engineering work but does not replace the responsible engineer's decisions, and that review submission is not itself a canonical write.

### HF-HOME-04 — Incomplete-state visibility

When `calculation_model_ready=false`, the UI must visibly state that the calculation model is not yet authorized/ready; it must not display a generic green completion state.

### HF-HOME-05 — Lifecycle without false progress

P0–P16 are exposed as lifecycle navigation/context while the page explicitly distinguishes product workflow state from engineering readiness.

### HF-HOME-06 — Technical detail remains reachable

The legacy technical Control Room remains reachable from Project Home, but is not the main entry surface.

## A2 completion boundary

A2 may be marked complete only when:

- the contract exists;
- the terminology layer validates;
- the authenticated runtime `/` renders Project Home v2;
- the technical Control Room is moved to a secondary route;
- the existing F7 evidence-review flow remains reachable and governed;
- human-factors acceptance fixtures pass;
- regression gates for CEW evidence/control/review remain green.

A2 completion does not imply that Source Hub, Evidence Workspace, Reconstruction, FEM, Verification or Intervention workflows are complete. Those remain subsequent work packages.
