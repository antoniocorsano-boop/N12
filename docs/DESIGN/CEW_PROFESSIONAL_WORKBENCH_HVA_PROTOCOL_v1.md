# CEW Professional Evidence Workbench — Human Validation Protocol v1

**Status:** `PROTOCOL_READY_FOR_IMPLEMENTATION — HVA_NOT_AUTHORIZED`  
**Scope:** professional engineering usability/mental-model validation  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Purpose

Validate that a professional engineer can use the Workbench to solve a realistic document-reading problem efficiently and safely, without confusing source evidence, recognition candidates, working edits or promoted engineering state.

The protocol validates a product candidate; it does not promote engineering facts or B1 by itself.

## 2. Entry gate

No human round may start until the exact candidate revision demonstrates:

- Product Contract implementation gate PASS;
- drawing-first layout present;
- F3 deep-zoom source viewport integrated;
- technical vector scene present;
- selectable technical objects;
- object-anchored WorkingEdit;
- graphical ReadingIssue;
- explicit registration state;
- Split implemented;
- Overlay disabled unless registration VERIFIED;
- progressive disclosure implemented;
- runtime/auth/audit exact-revision checks PASS;
- `canonical_write_authorized=false`.

Current B1.8 candidate does not satisfy this entry gate.

## 3. Participant framing

Participant is told only the professional scenario and product purpose necessary to perform work.

Do not teach CEW internal ids, epistemic vocabulary or success rules before the task.

Suggested framing:

> Devi verificare una lettura su una carpenteria esistente. Usa la fonte e la rappresentazione tecnica come faresti nel lavoro normale. Se un dato non è supportato dalla fonte, lascialo irrisolto.

## 4. Representative end-to-end task

Target workflow:

`find → orient → compare → identify uncertainty → inspect evidence → propose/correct → resolve or leave OPEN`

A suitable real case must include at least one genuinely unresolved or ambiguous reading so the participant can demonstrate that the product supports uncertainty rather than forcing completion.

The task data must be revision-bound and must not be secretly corrected by the HVA harness.

## 5. Subtasks

### HVA-PWB-01 — Locate and orient

Goal: locate the correct governed source and obtain a readable view.

Observe:

- source choice;
- navigation/orientation;
- loss/recovery of context;
- help requests;
- accidental wrong-source/version access.

Critical blocker: wrong source/version accepted as success.

### HVA-PWB-02 — Compare source and technical scene

Goal: use Split or appropriate modes to understand what the technical representation is showing.

Observe:

- ability to select a technical object;
- ability to reach linked source evidence;
- understanding of candidate vs governed object;
- semantic/spatial sync mental model.

Critical blocker: inferred correspondence treated as governed when no link exists.

### HVA-PWB-03 — Resolve a reading issue

Goal: inspect an unresolved item and decide whether to confirm, edit, leave unreadable or seek more evidence.

Observe:

- issue discovery;
- source-context use;
- alternative evidence use;
- editing/recovery;
- whether unsupported completion occurs.

Critical blocker: silent inference of unsupported value.

### HVA-PWB-04 — Understand working edit authority

Goal: create a working proposal and explain what changed.

Accepted mental model:

- source did not change;
- canonical engineering state did not change;
- workbench proposal changed;
- later governed review/promotion is separate.

Critical blocker: participant believes editing the technical scene directly changed the source/canonical model because the UI implied it.

### HVA-PWB-05 — Registration/overlay mental model

Where a VERIFIED registration exists, use Overlay and inspect correspondence.

Where it does not, participant should understand why Overlay/spatial sync is unavailable without being forced to understand transform mathematics.

Critical blocker: unverified alignment presented as reliable spatial truth.

## 6. Observation model

Collect, without displaying live test counters to participant:

- task completion/outcome;
- navigation path;
- source/version choices;
- mode changes;
- zoom/pan/rotation use;
- object selections;
- evidence reveal actions;
- issue actions;
- working edits/cancellations;
- help requests;
- backtracks/recovery;
- time on task as descriptive baseline;
- post-task ease/confidence;
- mental-model answers;
- free comment.

Time/interaction counts do not create arbitrary pass thresholds in the first credible baseline round.

## 7. Critical blockers

Non-compensable:

- `FALSE_SUCCESS`;
- wrong project/scope/source/source-version accepted;
- source/derived authority confusion;
- technical candidate mistaken for governed structural identity due to UI behavior;
- unverified registration treated as verified spatial correspondence;
- unsupported `ND/UNREADABLE` value silently completed;
- working edit interpreted/presented as canonical write;
- provenance/evidence link unavailable for an object presented as supported;
- cross-project/discipline leakage;
- participant cannot access primary source evidence for a claimed supported reading.

A critical blocker cannot be offset by speed or confidence.

## 8. Noncritical usability residuals

Examples:

- toolbar discoverability;
- inefficient mode switching;
- excessive pan/zoom;
- hard-to-find layers;
- inspector density;
- minor terminology confusion recovered without authority error;
- performance friction that does not corrupt evidence/decision.

These may support pass-with-residual only after review and only with no critical blocker.

## 9. Reviewer decisions

Allowed:

- `PASS_FOR_PROFESSIONAL_WORKBENCH_HVA`
- `PASS_WITH_NONCRITICAL_USABILITY_RESIDUAL`
- `FAIL_REWORK_REQUIRED`

The system must prevent PASS export while critical blockers remain.

## 10. Accessibility separation

Professional HVA does not replace manual accessibility validation.

Manual accessibility still checks at least:

- keyboard-only completion of essential flow;
- non-drag alternatives;
- focus visibility/order;
- object/issue/layer inspector operability;
- state communication without colour alone;
- narrow/tablet review behavior;
- target size/spacing.

## 11. Participant count and rounds

This protocol does not encode an arbitrary statistical sample size.

Recommended sequencing:

- owner/internal pilot to find obvious product defects — not sufficient for acceptance;
- credible professional round with multiple independent users when available;
- targeted repeat after blocking redesign.

Governance may set required participant count separately based on release risk and available professional reviewers.

## 12. Receipt contract

HVA receipt must include:

- exact runtime/client revision;
- source/scene revision identities;
- task dataset identity;
- participant/reviewer identities according to privacy policy;
- outcomes/critical blockers/residuals;
- registration state encountered;
- reviewer decision;
- accessibility state separately;
- `canonical_write_authorized=false`;
- `engineering_authority_effect=NONE`;
- required next gate.

No HVA receipt directly promotes engineering facts or B1.

## 13. Same-revision rule

If workbench code, scene contract, relevant source dataset, registration contract or interaction semantics change after HVA, the acceptance evidence becomes stale unless an explicit equivalence decision proves the change does not affect the validated behavior.

Default is to repeat HVA.

## 14. Post-HVA sequence

Only after accepted professional HVA:

`manual accessibility → same-revision Production deployment/smoke → governed B1 promotion decision`

No automated CI result may substitute for these human gates.

## 15. Current state

The protocol is versioned, but the current B1.8 surface does not satisfy the entry gate.

Therefore:

`PROFESSIONAL_HVA_PROTOCOL = READY_FOR_IMPLEMENTATION`

`HVA_EXECUTION_AUTHORIZED = false`

`PROFESSIONAL_WORKBENCH_READINESS = REWORK_REQUIRED`
