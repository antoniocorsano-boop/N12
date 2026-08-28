# CEW Human-Centred Service Model v2

Status: REQUIRED PRODUCT DESIGN AND HUMAN-EVIDENCE CONTRACT  
Supersedes for current CEW product design: `CEW_HUMAN_CENTRED_GOVUK_MODEL_v1.md`  
Governing model: `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`

## 1. Purpose

CEW adopts GOV.UK Service Standard / Service Manual principles as its primary service-design reference and specializes them for structural engineering and AI-assisted professional work.

The v2 model incorporates a critical lesson from the first B1.7 Acceptance Lab: **the user must perform their professional task; the evaluation system must observe the task.** The participant must not be required to understand or operate CEW's internal validation machinery.

## 2. Core service principle

The primary user experience is organized around professional meaning:

`PROJECT -> DOCUMENT -> DRAWING -> WHAT I SEE -> EVIDENCE -> WHAT I KNOW -> ENGINEERING QUESTION -> PROFESSIONAL DECISION`

The internal technical chain remains essential for traceability:

`Project -> Source -> SourceVersion -> Page -> DocumentMap -> EvidenceRegionCandidate -> EvidenceRegion -> Observation/Claim -> Entity/Property -> Gate/Decision`

The second chain supports the first. It must not become mandatory vocabulary for ordinary task completion.

## 3. GOV.UK adaptation

### Understand users and needs

Study the responsible engineer, evidence/document reviewer, modelling specialist, survey/investigation specialist and checker in their real working context. Understand consequences of error, not only screen preferences.

### Solve the whole problem

Design around the complete service journey from project/source understanding through evidence, reconstruction, model, investigations, analysis, verification, intervention and dossier.

### Provide a joined-up experience

Document, drawing, evidence, reconstruction and model context remain connected through stable identity and provenance without forcing the user to navigate implementation structure.

### Make the service simple to use

Professional meaning appears first. Internal identifiers, gate codes, commit SHAs and machine diagnostics are progressively disclosed.

### Make sure everyone can use the service

Accessibility, responsive behavior, keyboard operation, readable language and differences in digital confidence are acceptance concerns, not cosmetic polish.

### Work as a multidisciplinary team

Product, structural engineering, existing-structure assessment, human factors, service design, accessibility, security, QA, software and specialist engineering perspectives are represented as distinct roles even when one person temporarily fulfils several roles.

### Use agile and iterative delivery

Research and evaluation occur before, during and after implementation. Human evidence is not postponed to a final release ceremony.

### Define success and measure it

Effectiveness, efficiency, satisfaction/confidence and professional-safety metrics are combined with observation. Completion rate alone is insufficient.

### Operate a reliable service

Real deployed behavior, authentication, persistence, observability and rollback are part of acceptance.

### Choose technology based on need

AI, OCR, vector extraction, FEM or any UI framework are implementation choices. They do not define the product or professional authority.

## 4. Three human-evidence modes

### 4.1 Formative research

Purpose: understand the human problem before or while designing.

Typical questions:
- How does the engineer recognize the correct drawing today?
- Which professional terms are natural?
- Which uncertainty causes hesitation?
- What is the consequence of choosing the wrong source/version?
- Which information must be visible together?

Outputs:
- research observations;
- user/professional needs;
- journey changes;
- terminology changes;
- backlog/capability changes;
- design hypotheses.

Formative research does not produce a release PASS.

### 4.2 Evaluative usability / Human Factors

Purpose: observe whether a design or candidate supports realistic work.

The participant receives a credible professional situation and desired outcome. The system/researcher observes behavior and records friction, false success, help, recovery, confidence and mental model.

Outputs:
- task evidence;
- usability findings;
- critical misunderstandings;
- design residuals;
- rework decisions.

### 4.3 Release Human Validation / Acceptance (HVA)

Purpose: decide whether an immutable candidate satisfies declared human, safety and authority criteria.

The reviewer, not the participant, makes the release decision using the collected evidence.

HVA remains separate from professional engineering approval.

## 5. Participant experience contract

During a representative task the participant should see only what is needed to perform the work.

The participant surface may contain:
- professional context;
- one dominant task/question;
- the product under evaluation;
- natural help if help is intentionally part of the service;
- short post-task questions.

The participant surface must not primarily expose:
- `UX-DOC-01` style internal test identifiers;
- runtime commit SHA;
- deployment IDs;
- gate state;
- result-state enums such as `FALSE_SUCCESS`;
- HVA release decision codes;
- receipt JSON mechanics;
- counters that pressure the participant to optimize for the test;
- repository paths or architecture jargon not required by the professional task.

## 6. Reviewer experience contract

The reviewer surface is separate and may show:
- candidate revision/environment;
- task definitions and success conditions;
- session replay/path where permitted;
- time on task;
- interaction count;
- help requests;
- recoveries/backtracks;
- errors and false success;
- mental-model responses;
- accessibility observations;
- participant comments;
- critical safety/provenance blockers;
- comparison with prior benchmark rounds;
- release decision controls;
- generated receipt preview.

## 7. Telemetry principle

Telemetry is normally collected invisibly during the task.

Visible timers/counters are permitted only when the real service itself contains them or when the research protocol explicitly requires them. Otherwise they risk changing participant behavior and invalidating the observation.

Metrics are evidence, not automatic judgment.

## 8. Critical-error model

The following are non-compensable blockers where applicable:
- wrong Project or discipline scope;
- wrong Source or SourceVersion;
- treating a derived reading aid as the authoritative original;
- believing viewer/display operations modify the authoritative source;
- believing review automatically changes canonical engineering state;
- inability to trace a decision-relevant statement back to source/evidence where required;
- cross-project or cross-discipline leakage;
- false success on a safety/authority-critical task.

A fast task cannot compensate for these errors.

## 9. Usability residuals vs safety blockers

Examples of usability residuals:
- avoidable extra interactions;
- slower-than-baseline navigation;
- minor terminology hesitation;
- need for noncritical help;
- visual hierarchy friction.

Examples of safety/authority blockers:
- wrong source/version;
- wrong project/scope;
- authority confusion;
- provenance loss;
- canonical-write misconception;
- hidden uncertainty causing a false conclusion.

They are reported separately.

## 10. Mental-model checks

Critical concepts are tested after action using natural questions rather than leading instructions.

Example for drawing rotation:

> After rotating the drawing to read it, what do you think changed?

Possible interpretation categories:
- display/view only;
- original document changed;
- not sure.

The task prompt should not pre-teach the expected answer unless the real service itself must teach it before safe operation.

## 11. CEW representative journey design

Representative tasks should be written as professional situations.

### B1 example — find a drawing

Participant prompt:

> You need to check the structural drawing for the fourth floor/impalcato. Find the relevant drawing and open it.

Internal evaluation may verify that the correct governed source/version was selected and that the primary source status was understood.

### B1 example — orient a drawing

Participant prompt:

> The drawing is not convenient to read. Adjust the view so you can read it, then return the view to its initial orientation.

After action, ask whether the original document changed.

### B1 example — evidence round trip

Participant prompt:

> You want to check where this evidence comes from in the complete drawing. Open its source context and then return to the evidence.

### B1 example — original vs reading aid

Participant prompt:

> You have the original document and a copy prepared to make reading easier. Which one would you use as the source to verify or cite the information?

## 12. Baselines and benchmarks

For each durable capability CEW should maintain an evaluation twin containing:
- stable representative task IDs internally;
- human-facing prompts by benchmark version;
- success conditions;
- critical blockers;
- baseline metrics;
- qualitative findings;
- accessibility notes;
- candidate revision/environment;
- decision and residuals.

The first credible round establishes a baseline. Arbitrary time/click thresholds should not be invented merely to create a PASS condition.

## 13. Inclusion and accessibility

Human evaluation includes:
- keyboard operation where relevant;
- screen-size/responsive behavior;
- legibility and contrast;
- terminology comprehension;
- error recovery;
- different levels of digital confidence;
- avoidance of unnecessary memory burden;
- clarity of irreversible vs reversible actions.

Automated accessibility checks are useful but do not replace human evaluation of critical workflows.

## 14. AI interaction principles

When AI participates in CEW:
- AI suggestions are clearly distinguishable from governed facts;
- uncertainty/provenance is visible at the decision point;
- AI must not create professional authority through confidence or fluent wording;
- users are not required to understand model internals;
- high-impact AI proposals have a review path;
- evaluation tests whether users over-trust or misunderstand AI-generated material;
- human review evidence is captured without rewriting the original observation.

## 15. Human evidence receipt

A release HVA receipt should identify:
- product/capability/slice;
- immutable candidate revision;
- environment/deployment;
- benchmark/task version;
- participants/reviewer identifiers at the permitted privacy level;
- task outcomes;
- critical blockers;
- usability residuals;
- mental-model findings;
- accessibility findings where applicable;
- reviewer decision;
- production-smoke requirement/state;
- authority effect (`NONE` unless separately governed);
- promotion eligibility.

## 16. B1.7 finding and required redesign

The first B1.7 Acceptance Lab successfully proved that the measurement contract existed, but the observed participant surface mixed:
- product work;
- task instructions;
- telemetry;
- test result entry;
- release/HVA decision;
- receipt export.

This is treated as a Human Factors finding against the **acceptance instrument**, not as evidence that CEW B1 itself passed or failed.

The admissible next design is a separated Participant / Reviewer / Receipt architecture. The decision is persisted in `docs/DECISIONI/PRODUCT_HF_001_PARTICIPANT_REVIEWER_SEPARATION_v1.md`.

## 17. Release rule

A user-facing CEW capability cannot be declared product-complete solely from CI, deployment readiness or a participant reaching the final screen.

Applicable representative tasks require human evidence with no unresolved critical safety/authority misunderstanding, followed by the required same-revision operational smoke and promotion process.
