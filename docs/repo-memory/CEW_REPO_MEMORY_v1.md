# CEW Repository Memory v1

**Status:** ACTIVE / REPO-NATIVE MEMORY FOUNDATION  
**Date:** 2026-10-28  
**Scope:** Civil Existing Workflow / N12  
**Authority effect:** NONE  

## Purpose

CEW has accumulated reusable engineering, evidence, learning, review and assurance capabilities across many branches and pull requests. Some of that work is qualified but not merged into `main`. A future task can therefore appear to need a new component even when an equivalent or adjacent component already exists elsewhere in the repository history.

Repository Memory exists to prevent that loss of project knowledge.

It implements one operational rule:

> **SEARCH REPO MEMORY BEFORE DESIGNING OR BUILDING A NEW CEW CAPABILITY.**

This is the internal counterpart of the canonical Master principle `BUILD LAST — REUSE FIRST`.

## What Repository Memory is

Repository Memory is a governed index of reusable project knowledge. It records:

- capabilities that already exist or were previously explored;
- exact source PR/branch/ref and current status;
- contracts, implementations, validators and workflows that embody the capability;
- authority boundaries;
- whether the capability should be reused, adapted, benchmarked, superseded or avoided;
- lessons learned from failed or duplicated approaches;
- architectural decisions and the evidence that motivated them;
- unresolved gaps that remain genuinely new work.

It is not a replacement for Git history, source evidence, the CEW Master Plan, issue/PR discussion or human engineering judgment.

## Memory layers

### Layer 1 — Human-readable memory

Files under `docs/repo-memory/` explain the project state to a human or agent entering the repository with no conversation context.

Minimum set:

- `CEW_REPO_MEMORY_v1.md` — operating contract;
- `CEW_B01_RECONCILIATION_MATRIX_v1.md` — capability-by-capability reuse decision for the current CEW-B01 work;
- `CEW_LESSONS_LEARNED_v1.md` — durable lessons with consequences for future work.

### Layer 2 — Machine-readable capability registry

`governance/repo-memory/CEW_CAPABILITY_REGISTRY_v1.json`

Each capability records at least:

- stable `capability_id`;
- name and scope;
- source PR, branch and exact reference used for the memory entry;
- status (`CANONICAL`, `QUALIFIED_NONCANONICAL`, `EXPERIMENTAL`, `SUPERSEDED`, `BLOCKED`, `UNKNOWN`);
- key files/interfaces;
- authority effect;
- reuse disposition (`REUSE`, `ADAPT`, `PORT`, `REFERENCE_ONLY`, `DO_NOT_REUSE`);
- known limitations;
- last verification date.

### Layer 3 — Reuse decisions

A task that overlaps an existing capability records an explicit decision:

`existing capability -> inspected -> reuse/adapt/port/reject -> reason -> new work boundary`

The decision is about implementation reuse, not engineering truth.

### Layer 4 — Enforcement

Repository Memory is active, not advisory-only.

- `automation/validate_cew_repo_memory.py` validates registry integrity, capability references, reuse dispositions and plan compliance.
- `.github/workflows/validate-cew-repo-memory.yml` runs the validator and its tests on candidate heads.
- New active CEW implementation plans must contain `## Repository Memory / Reuse Assessment`.
- Historical plans created before memory activation are not rewritten retroactively. A grandfathered plan is accepted only when `governance/repo-memory/CEW_LEGACY_PLAN_REUSE_ASSESSMENTS_v1.json` records an explicit external reuse assessment bound to valid capability IDs.
- Hidden filename exceptions in validator code are forbidden: exemptions must be data-governed and inspectable.

The enforcement layer changes development process only. It grants no engineering, evidentiary, structural or canonical authority.

## Required pre-build lookup

Before adding a new CEW capability, the task owner should answer these questions:

1. What capability am I about to create?
2. Does Repository Memory already contain it or an adjacent implementation?
3. Are there open/draft historical PRs carrying qualified work not present in `main`?
4. What exact interface or contract can be reused?
5. If reuse is rejected, what concrete incompatibility justifies new code?
6. Does the proposed work preserve the authority boundary of the reused component?
7. What is the smallest genuinely new adapter, validator or CEW-specific logic required?

No answer may rely only on conversational memory.

## Status semantics

### CANONICAL

The capability is part of the current approved CEW baseline or Master.

### QUALIFIED_NONCANONICAL

The capability has meaningful implementation/evidence or passed a dedicated gate but is not canonical because its PR/branch was not integrated or its promotion gate remains open.

This status is important: **non-merged does not mean nonexistent or disposable**.

### EXPERIMENTAL

Useful spike or candidate implementation that may teach the project something but must not be treated as the preferred reusable implementation without reconciliation.

### SUPERSEDED

Retained for provenance/regression but replaced by a later capability or contract.

### BLOCKED

Conceptually valid but unusable until a named dependency/gate is satisfied.

### UNKNOWN

Insufficient evidence to classify safely.

## Reuse dispositions

- `REUSE` — consume the existing interface with minimal or no change.
- `ADAPT` — preserve the existing capability and add a bounded adapter for the current task.
- `PORT` — move a bounded implementation/contract from a noncanonical branch into the active line after dependency and license review.
- `REFERENCE_ONLY` — use the prior work as methodological/architectural evidence, not executable dependency.
- `DO_NOT_REUSE` — prior approach is known to be wrong, obsolete or unsafe for the current task; reason must be recorded.

## CEW-specific invariants

Repository Memory must preserve the project’s existing authority separation:

- source documents remain evidentiary authority;
- detector/grammar/similarity output remains proposal or hypothesis until the required human gate;
- similarity does not create object type, family membership or structural identity;
- learned/prototype memory does not create canonical geometry;
- `INF`, `INC` and `ND` never become `DOC` implicitly;
- adapters may translate representations but may not silently increase epistemic authority;
- historical object counts, identifiers and coordinates are regression evidence, not production oracles.

## WIP rule

Repository Memory is cross-cutting governance support, not a second product stream. Under CEW WIP=1 it should be updated inside the active macro-task when a reconciliation finding is material, rather than spawning parallel feature development.

## Update triggers

Update Repository Memory when any of the following occurs:

- a capability is introduced, qualified, rejected or superseded;
- a new external tool is benchmarked;
- a duplicated implementation is discovered;
- a human review reveals a systemic architectural lesson;
- a previously noncanonical branch becomes the selected reuse source;
- an implementation assumption proves false;
- a gate changes what downstream work is authorized.

## Current activation

Repository Memory v1 is activated by the CEW-B01 drawing-grammar reconciliation performed on 2026-10-28. The first concrete finding is that the new B01 drawing-grammar work overlaps three pre-existing capability lines:

- engineering drawing grammar (#143);
- deterministic similarity (#116);
- zero-prior discovery / prototype learning (#137).

The active reconciliation is recorded in `CEW_B01_RECONCILIATION_MATRIX_v1.md` and the durable consequences in `CEW_LESSONS_LEARNED_v1.md`.
