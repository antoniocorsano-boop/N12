# CEW EWS-2 — Unified Focused Context Rail v1

**Status:** IMPLEMENTED_PENDING_VALIDATION  
**Authority effect:** NONE  
**Canonical write:** false

## HVA trigger

The professional HVA showed that a resizable rail alone does not create usable professional software when the complete OA lifecycle is rendered as one vertical form. The anti-pattern is therefore not width but simultaneous lifecycle exposure.

## Interaction rule

The Context Rail is a task controller, not a container for every available form.

**One primary work panel is visible at a time.**

Rail phases:

1. `ACQUIRE` — select/teach an example;
2. `FIND_SIMILAR` — start deterministic similarity;
3. `REVIEW_SET` — summary, bounded candidate set, active candidate, review actions;
4. `RESOLVE_IDENTITY` — explicit structural-identity candidate construction;
5. `VALIDATE_IDENTITY` — explicit OA-G5 decision.

Downstream phases stay hidden and disabled until their governed eligibility exists. Eligibility never auto-opens a downstream phase: the operator must use an explicit transition.

## Review-set ergonomics

During `REVIEW_SET`, visible content is restricted to summary, filters, a bounded candidate set, one active candidate and review actions. OA-2 teaching, the legacy OA-4 persistence form, OA-5 resolver and OA-G5 decision form are hidden.

OA-4 remains the persistence owner behind EWS-4. EWS-2 does not persist, compute similarity, create family membership or create structural identity.

## Governance

WorkMode and rail state are presentation state only. They cannot create engineering authority, canonical writes or project material. OA-G5 and OA-6 remain separate governed gates.
