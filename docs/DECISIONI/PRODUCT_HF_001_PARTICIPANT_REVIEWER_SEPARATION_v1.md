# PRODUCT-HF-001 — Participant / Reviewer Separation

Status: ACCEPTED PRODUCT DECISION  
Date: 2026-08-28  
Applies to: CEW, eTwin and future human-acceptance instruments  
Origin: direct observation of the first CEW B1.7 Acceptance Lab participant surface

## Context

The first CEW B1.7 Acceptance Lab correctly implemented several governance requirements:
- revision-bound evaluation;
- representative task IDs;
- time/interactions/help/recovery metrics;
- critical source/authority/canonical-write checks;
- explicit human HVA decision;
- receipt export;
- no canonical engineering write.

However, direct use of the participant screen exposed a deeper Human Factors defect: the same surface asked one person to simultaneously:

1. perform the professional product task;
2. understand internal test identifiers and technical acceptance language;
3. watch telemetry counters;
4. self-record test outcomes;
5. act as the release/HVA reviewer;
6. export governance evidence.

This made the evaluation difficult and cognitively confusing and risked changing the participant's behavior.

## Decision

Human acceptance is split into four explicit layers:

### 1. Participant surface

Shows only:
- realistic professional context;
- one dominant task at a time;
- the product being evaluated;
- natural help where part of the intended service;
- short post-task mental-model questions.

It does not primarily expose internal task IDs, commit SHAs, telemetry counters, HVA decision enums or receipt mechanics.

### 2. Observation / telemetry layer

Collects task time, interactions, help, recoveries, navigation and declared observations without pressuring the participant to optimize the test.

### 3. Reviewer surface

Shows revision/environment, task evidence, critical failures, usability residuals, mental-model findings, accessibility findings and benchmark comparison. The reviewer makes the HVA/release decision.

### 4. Receipt layer

Generates machine-readable revision-bound evidence after reviewer action.

## Consequences

- `CEW_B1_USABILITY_ACCEPTANCE_CONTRACT_v1` remains historical evidence of the B1.7 preparation model but is not the target participant interaction model for promotion.
- The current B1.7 automated instrument PASS proves only that the first instrument behaved according to its contract.
- The observed difficulty is a finding against the **acceptance instrument**, not automatic proof that CEW B1 itself failed.
- A new human-centred acceptance implementation is required before B1 promotion.
- eTwin Human Factors work must consume the same participant/reviewer separation rather than create an incompatible acceptance harness.
- Release decision codes remain machine/reviewer concepts; participant language remains professional and task-oriented.

## Non-compensable safety rule

Critical source/version, project/scope, authority, provenance or canonical-write misunderstandings remain blockers regardless of task speed or completion.

## Supersession

This decision may be superseded only by a later explicit product Human Factors decision with evidence. It must not be silently reversed by UI implementation convenience.
