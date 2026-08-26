# CEW Human Engineering Experience Model v1

Status: `UX FOUNDATION — EXPERIMENTAL / NON-PROMOTIVE`

## 1. Purpose

CEW is operated primarily by a civil/structural engineer who must understand an existing construction, judge the quality of the available evidence, build and review structural knowledge, evaluate uncertainty, and make accountable technical decisions. The interface shall therefore expose the engineer's work model, not the repository's internal model.

The canonical human mental sequence is:

`Opera → Fonte → Evidenza → Elemento strutturale → Proprietà → Stato di conoscenza → Comportamento → Problema → Decisione → Intervento → Verifica`

Repository IDs, hashes, generation identifiers and gate receipts remain available, but are secondary provenance detail.

## 2. Primary professional role

Primary role: **Ingegnere civile / strutturista responsabile della conoscenza, modellazione e valutazione di una costruzione esistente.**

The UI shall assume professional competence. It shall not simplify engineering concepts into consumer language. It shall instead:
- use standard civil/structural engineering vocabulary;
- distinguish documentary fact, measurement, reference, inference and missing knowledge;
- expose assumptions and limits near the information they affect;
- preserve unit, sign convention, coordinate system and scenario context;
- make the consequence of an unresolved item explicit.

## 3. Human authority

The human is not a generic approver. Human authority is specialized by decision class:
- **technical reading decision** — what is directly visible/readable in a primary source;
- **binding decision** — whether source evidence belongs to a structural entity;
- **engineering assumption decision** — which admissible hypothesis is used in a scenario;
- **investigation decision** — which uncertainty is worth reducing and by which test;
- **intervention decision** — which objective/candidate is accepted for a proposed generation;
- **promotion decision** — whether a validated candidate may alter an authorized canonical projection.

The interface shall never disguise one class as another.

## 4. Professional experience principles

CEW shall feel like a precise technical instrument. Professional gratification comes from:
1. **control** — the engineer can see what will change before committing;
2. **clarity** — source, evidence, interpretation and model are visually separable;
3. **precision** — units, coordinates, version and epistemic state remain explicit;
4. **speed** — source ↔ model ↔ property ↔ decision navigation is immediate;
5. **trust** — every important value can reveal its provenance and limits;
6. **continuity** — the system restores project/scenario/entity context after interruption;
7. **closure** — unresolved work exposes the next technically meaningful action.

CEW shall not use celebratory gamification, streaks, achievement badges or patronizing praise.

## 5. Language model for the interface

Primary labels use engineering meaning: `Pilastro P21 — Piano terra`, `Sezione 40 × 50 cm`, `Armatura longitudinale`, `Schema di armatura — Copertura`, `Non determinabile dalla fonte corrente`, `Richiede verifica sulla tavola originale`, `Associazione all'elemento non ancora determinata`.

Raw objects such as `OBS-*`, `GCFP-*`, `SourceVersion`, SHA-256 and receipt IDs are displayed under **Provenienza tecnica** or equivalent detail surfaces.

## 6. Decision grammar

A decision surface must state, in this order: subject, primary evidence, model/scenario context, CEW request/proposal, professional alternatives, consequence, and provenance on demand.

For a source-to-model binding, preferred choices are:
- `Associazione confermata`
- `Non appartiene a questo elemento`
- `Non determinabile dalla fonte`
- `Serve altra evidenza`

A choice is never preselected when it would create engineering authority.

## 7. Context hierarchy

Persistent context: `Progetto · Generazione/Stato · Livello/Zona · Entità/Task`.
Example: `N12 · Stato esistente · Piano terra · Pilastro 21`.
Scenario, model generation and source generation must never be silently switched.

## 8. Human-review safeguards

- evidence is shown beside the candidate or decision;
- source drift invalidates stale review;
- no canonical write occurs directly from a visual control;
- the UI emits a decision receipt, then downstream governance validates it;
- an unavailable value is presented as missing knowledge, not as UI error;
- uncertainty and conflict are first-class states;
- keyboard operation and focus order are mandatory;
- color is never the only carrier of technical state.

## 9. Success criterion

A technician unfamiliar with repository internals can open a project, navigate from entity to source evidence, understand knowledge state, review a bounded decision and obtain a traceable receipt without editing JSON/CSV or knowing internal CEW IDs.
