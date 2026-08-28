# Documentation Authority Model v1

Status: REQUIRED GOVERNANCE CONTRACT  
Applies to: repository-wide product and development documentation  
Date: 2026-08-28

## 1. Purpose

This document defines how product, development, architecture, automation, state and evidence documents relate to one another.

The goal is to prevent documentation drift caused by multiple chats, parallel branches, historical plans, product experiments and agent-generated artifacts.

The rule is simple:

> **No document is authoritative merely because it is newer, longer or easier to find. Authority comes from its declared role in this hierarchy and from the current machine-readable governance manifest.**

## 2. Documentation layers

### L0 — Repository governance

Defines how the organization/product agency operates.

Examples:
- `docs/GOVERNANCE/AI_NATIVE_PRODUCT_AGENCY_OPERATING_MODEL_v1.md`
- this document.

L0 governs process and documentation authority. It does not own engineering facts.

### L1 — Product / programme contracts

Defines product identity, product architecture, programme objectives, capabilities, sequencing and high-level authority boundaries.

Examples:
- CEW product completion programme;
- CEW human-centred product architecture;
- eTwin platform extension programme;
- product-specific development models.

L1 specializes L0 for a product or programme.

### L2 — Capability and interaction contracts

Defines how a bounded capability behaves.

Examples:
- Source Hub contract;
- Document & Drawing Workspace contract;
- Evidence Workspace contract;
- human research/evaluation contract;
- Project/Discipline/Scope contract.

L2 may not silently contradict L0/L1. A justified divergence requires a decision record.

### L3 — Machine-readable execution contracts

Defines schemas, queues, agent contracts, gate state, manifests, task/result formats and validators.

Examples:
- `automation/*.json` contracts;
- agent result schemas;
- development queues;
- usability metrics models;
- orchestration manifests.

L3 must point back to its governing L0/L1/L2 documents.

### L4 — Current state

Describes what is true now about product/program runtime or engineering work.

Examples:
- `data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json` for CEW product/runtime state;
- `automation/ETW_PROGRAM_STATUS_v1.json` for eTwin programme state;
- `knowledge/CURRENT_STATE.json` for N12 engineering authority.

Current state must not be used to redefine architecture or policy. It reports admitted state under those contracts.

### L5 — Evidence, receipts and acceptance records

Records observed execution.

Examples:
- automated validation receipts;
- HVA receipts;
- Production smoke receipts;
- deployment receipts;
- acceptance reports.

Receipts are evidence of what happened on an identified revision/environment. They do not replace the contract that defines what should happen.

### L6 — Decision records

Records why a material rule, model, contract or product direction changed.

Decision records bridge historical and current authority. They explain supersession and consequences.

### L7 — Historical / analytical material

Includes prior plans, analyses, experiments, reports and superseded contracts retained for traceability.

Historical material may be highly valuable but is not current authority unless explicitly re-admitted.

## 3. Precedence rule

When two documents appear to conflict:

1. determine whether they address the same domain and scope;
2. prefer the current authority declared in `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`;
3. apply the L0 -> L1 -> L2 -> L3 contract hierarchy;
4. use current state only to determine admitted execution/maturity state;
5. use receipts only as evidence of observed execution;
6. consult decision records for intentional supersession;
7. if the conflict remains unresolved, fail closed and create a decision/work item rather than choosing silently.

## 4. Engineering authority exception

This documentation model does **not** move N12 engineering authority into product documentation.

For N12:
- engineering facts remain governed by `knowledge/CURRENT_STATE.json` and governed canonical artifacts;
- CEW/eTwin documents may project or reference engineering state but do not own it;
- product maturity, UI state, agent output and deployment state never upgrade engineering epistemic state.

## 5. Versioning and supersession

### Immutable history principle

A versioned document should not be rewritten merely to make the past look consistent with the present.

Preferred pattern:

`v1 -> decision record -> v2 -> manifest points to v2`

Existing v1 files remain available for audit.

### Living canonical documents

Some programme documents intentionally remain living documents despite a version suffix. When such a document is updated, the change must be attributable to a branch/PR and material semantic changes should still have a decision record.

### Supersession metadata

A replacement document must state what it supersedes. The governance manifest records the current document for each governance role.

## 6. State documents

State documents must satisfy all of the following:
- report current admitted state, not future aspiration;
- identify update date/time where practical;
- point to governing programme/contracts;
- separate product/runtime state from engineering authority;
- distinguish deployed, validated, human-evaluated and promoted states;
- never infer human approval from CI;
- never infer promotion from deployment.

## 7. Receipts

A valid receipt identifies, where applicable:
- work item / slice;
- immutable revision;
- environment/deployment;
- observed result;
- gates/checks;
- human reviewer where required;
- residuals/blockers;
- authority effect;
- whether promotion is authorized.

A receipt cannot retroactively validate a different revision unless an explicit equivalence rule exists.

## 8. Decision records

Material decisions include:
- changing an authority boundary;
- changing a human acceptance model;
- changing promotion semantics;
- adopting or retiring a programme architecture;
- allowing new canonical writes;
- changing project/discipline isolation;
- changing solver/evidence authority;
- changing the meaning of an epistemic or workflow state.

Decision records use stable IDs and remain append-only/superseded rather than silently deleted.

## 9. Directory roles

The current repository directories are retained to preserve references.

- `docs/GOVERNANCE/` — cross-product operating and authority rules;
- `docs/PROGRAM/` — product/programme delivery models and roadmaps;
- `docs/ARCHITECTURE/` — structural product/system architecture;
- `docs/PRODUCT/` — bounded product capability contracts;
- `docs/ACCEPTANCE/` — acceptance plans/reports and human evaluation material;
- `docs/AUDIT/` — audits and independent assurance;
- `docs/DECISIONI/` — material decision records and engineering/product decisions;
- `docs/MIGRATION/` — migration/adoption boundaries;
- `automation/` — machine-readable contracts, queues and orchestration state;
- `data/canonical/` — current canonical product/runtime data where declared;
- `knowledge/` — N12 engineering authority and knowledge state;
- `automation/receipts/` — durable execution evidence.

Mass file moves are not required to obtain coherence. Authority is established by the manifest and references first; physical reorganization may be done later through explicit migration work.

## 10. Conversation rule

A conversation may:
- discover a problem;
- propose a model;
- coordinate work;
- interpret repository evidence.

A conversation does not become durable governance until the relevant decision/contract/state is persisted in the repository.

When a conversation produces a material correction, the repository should receive at least one of:
- updated current state;
- a new/revised contract;
- a decision record;
- a receipt/evidence artifact;
- a backlog/work-item change.

## 11. Agent consumption rule

Agents must begin cross-cutting product work by reading:

1. `automation/PRODUCT_GOVERNANCE_MANIFEST_v1.json`;
2. the referenced L0 governance model;
3. the product/programme contract for their work item;
4. the current state file;
5. the selected queue/work item;
6. applicable capability contracts;
7. relevant decision records and receipts.

Agents must not reconstruct current policy from file modification timestamps or chat history.

## 12. Validation

`PRODUCT_GOVERNANCE_MANIFEST_v1.json` is validated in CI so that referenced authoritative documents exist and required governance roles are declared.
