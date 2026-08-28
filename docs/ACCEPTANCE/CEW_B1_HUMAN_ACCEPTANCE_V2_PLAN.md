# CEW B1.8 — Human-Centred Acceptance v2

Status: IMPLEMENTED CANDIDATE — HUMAN ACCEPTANCE PENDING  
Program: CEW-GOAL-01 / CEW-B1-SOURCE-EVIDENCE-JOURNEY  
Governing contract: `automation/CEW_B1_HUMAN_ACCEPTANCE_CONTRACT_v2.json`

## 1. Purpose

B1.8 replaces the **participant interaction model** of the historical B1.7 Acceptance Lab while preserving B1.7 as evidence of the earlier instrument and of the Human Factors finding that triggered this redesign.

B1.8 does not change SourceVersion, Page, PageTransform, EvidenceRegion, engineering claims or canonical model state.

## 2. Human architecture

The acceptance experience is separated into four layers:

1. **Participant** — performs one realistic professional task at a time.
2. **Observation** — records declared metrics and paths without exposing live test counters.
3. **Reviewer** — interprets task evidence, mental models, blockers and usability residuals.
4. **Receipt** — exports revision-bound HVA evidence only after reviewer action.

The participant is not asked to decide whether B1 passes and does not export governance evidence.

## 3. Routes and modes

- Participant: `/acceptance/b1`
- Reviewer: `/acceptance/b1#review`

The reviewer mode is intentionally separate from the participant flow even though both are served by one static application route.

## 4. Representative tasks

### Task 1 — find the drawing

> Devi controllare la carpenteria del IV impalcato. Trova la tavola corretta e aprila.

Internal success signal: the journey reaches governed drawing `TAV-05A` without requiring repository knowledge.

### Task 2 — make the drawing readable

> La tavola non è comoda da leggere. Sistemala per leggerla e poi riporta la vista come prima.

The observer checks that a rotated display state was used and that the final display state returns to 0°. After the task the participant is asked whether the original document changed. Accepted mental model: **display/view only**.

### Task 3 — evidence and drawing context

> Vuoi verificare da quale parte della tavola deriva questa evidenza. Apri il contesto della fonte e poi torna all’evidenza.

The reference evidence is the governed `ERW-N12-001 -> CEW-N12-REG-G01-R06 -> TAV-05A` chain. The evaluation verifies that the participant understands the source/evidence round trip without needing internal identifiers.

### Task 4 — original vs reading aid

> Hai il documento originale e una copia preparata per facilitarne la lettura. Quale useresti come fonte da verificare o citare?

Accepted mental model: **the verified primary PDF**, not the derived reading aid.

## 5. Observation model

Collected locally for the acceptance session:

- time on task;
- interaction count;
- help requests;
- recovery/backtrack signals;
- navigation path;
- drawing viewer states;
- task outcome;
- ease and confidence;
- post-task mental-model response;
- free comment.

These metrics are not shown live to the participant.

The first credible B1.8 human round is a baseline. Time and interaction counts do not create arbitrary PASS thresholds.

## 6. Critical blockers

Non-compensable failures include, where applicable:

- `FALSE_SUCCESS`;
- wrong Project/scope;
- wrong Source/SourceVersion;
- primary/derived authority confusion;
- interpreting viewer state as source mutation;
- canonical-write misconception;
- provenance break;
- cross-project or cross-discipline leakage.

A critical blocker cannot be offset by speed, confidence or low interaction count.

## 7. Usability residuals

Help use, recovery/backtracking, low ease or inefficient paths are recorded separately from safety/authority blockers.

They may support `PASS_WITH_NONCRITICAL_USABILITY_RESIDUAL` only when no non-compensable blocker remains.

## 8. Reviewer decision

Allowed decisions:

- `PASS_FOR_B1`
- `PASS_WITH_NONCRITICAL_USABILITY_RESIDUAL`
- `FAIL_REWORK_REQUIRED`

If a critical blocker is present, the implementation prevents exporting a PASS decision.

## 9. Receipt boundary

The HVA receipt:

- is generated locally after reviewer action;
- contains the immutable runtime revision and deployment identity;
- contains task evidence, critical blockers and usability residuals;
- records the human reviewer and decision;
- requires subsequent same-revision Production smoke;
- does not authorize canonical writes;
- has no engineering-authority effect;
- does not itself promote B1.

No acceptance receipt is submitted to a server in this tranche.

## 10. Accessibility gate

Automated implementation checks cover semantic controls, focus visibility, responsive layout and the absence of colour-only critical decision semantics. A manual accessibility pass remains required before B1 promotion.

The manual pass must include at least:

- keyboard-only completion of the participant flow;
- keyboard access to viewer controls used by Task 2;
- visible focus on interactive controls;
- usable participant flow at narrow/mobile viewport;
- labels/questions understandable without relying on colour;
- reviewer controls distinguishable and operable by keyboard.

## 11. Same-revision promotion sequence

The admissible sequence is:

`B1.8 automated gates -> freeze immutable Preview candidate -> real participant session -> reviewer HVA decision -> manual accessibility acceptance -> same accepted revision Production deployment/smoke -> B1 promotion -> CEW_PROMOTED_BASELINE`

If code changes after HVA, the candidate revision changes and HVA must be repeated unless an explicit equivalence contract authorizes otherwise.

## 12. Non-goals

B1.8 implementation does not:

- promote B1;
- satisfy HVA automatically;
- satisfy manual accessibility automatically;
- perform Production smoke;
- resolve B1.4 private-byte persistence policy;
- resolve B1.6 candidate-persistence/promotion policy;
- alter N12 engineering facts;
- release ETW-A0 or ETW-A1.
