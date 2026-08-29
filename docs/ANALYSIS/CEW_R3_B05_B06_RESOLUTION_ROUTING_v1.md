# CEW R3 — B05 / B06 Resolution Routing v1

Status: PROJECT ANALYSIS — CURRENT ROUTING BASIS
Date: 2026-08-25
Project: N12
Work item: CEW-R3-SYNCHRONIZED-EVIDENCE-MAP-V0

## Purpose

Prevent repeated blind re-reading and route each residual through the most useful next module using already-canonical evidence.

## B05 — Foundation section/reinforcement coverage

### Established facts

The P08 TAV-01A binding review reprojected all seven TAV-01A groups onto P07 primary geometry. It did not carry forward earlier counts by assumption.

P08 result:
- 39 primary-coincident direct property bindings;
- 1 supported binding: 22bis-27, retained as SUPPORTED and not promoted to direct;
- 15 primary P07 incidences remain `ND_DOCUMENTARY_COVERAGE`;
- three literal TAV-01A G06 steps — 25-26, 28-29, 31-32 — are not P07 physical incidences and are explicitly barred from creating foundation members.

The 15 documentary gaps are:

`3-11; 5-6; 6-7; 7-8; 17-18; 18-19; 19-20; 11-19; 19-25; 21-22; 22-22bis; 22bis-23; 23-24; 25-28; 28-31`.

### Routing decision

B05 is classified as a **confirmed documentary coverage gap**, not merely an unsearched image area.

Therefore CEW must not recommend repeated full-sheet TAV-01A re-reading as the default next action. The Evidence Region Review Pack may still be used for a targeted audit if a concrete missed-detail hypothesis arises, but lack of a group binding remains ND unless new primary evidence or a human-approved local verification supplies it.

Preferred resolution order:
1. recover another primary/historical source, if one exists;
2. use targeted local verification / investigation for affected members where decision-relevant;
3. retain affected members unresolved in scenarios that do not require them;
4. never transfer a neighbouring/homologous group without explicit source equivalence.

## B06 — Superstructure reinforcement residuals

B06 remains suitable for documentary localization because the M1A indexes retain source locators for specific unresolved or partially bound details.

The cleanest current candidate is:
- source: `TAV-06A`;
- immutable archive path: `archive/documentazione_originaria/tavola 6.pdf`;
- archive commit used by R3 review pack: `78c20a52db4f391ce0d13b9705b9f04737e218c9`;
- archive blob SHA: `c3048472adfdaa5b1e902f84c20ccfb20d679b1f`;
- PDF page: 1;
- canonical source locator: `TAV06A P07`;
- target entity: `G5-B017`;
- source state: `DOC_SOURCE_UNBOUND`.

The canonical TAV-06A group index states that P07 shows an inclined member with two support stations and one free overhang end, but this topology is not a direct match to current `G5-B017 = 12-19`. Therefore the source detail must not assign B017 reinforcement automatically; it is useful evidence for why B017 remains unresolved.

### Routing decision

Create a `MACHINE_PROPOSED` EvidenceSnippet candidate for `TAV06A P07 → G5-B017`. It is a navigational/evidence candidate only and does not change B017 reinforcement state.

Other B06 residuals should be routed similarly only where a canonical source locator and entity identity can be established from existing M1A ledgers.

## Evidence Region Review Pack

PR #54 introduced the deterministic review-pack mechanism:
- immutable PDF → 300 dpi derivative;
- exact archive commit and blob SHA recorded;
- deterministic 4×4 overlapping regions;
- bbox in pixels and normalized coordinates;
- review HTML + machine-readable manifest;
- all tiles `CONTEXT_ONLY`;
- no automatic claim/issue promotion.

Run `32808748683`, artifact `9549061362`, produced:
- B05: 1 source / 16 regions;
- B06: 5 sources / 80 regions;
- artifact digest: `sha256:a1dc8cd3b940e452886910a40d29a5eb7c9d368b9efc630a525625d5c388ab5d`.

## Product lesson

The CEW blocker-resolution module must distinguish at least:
- `SEARCHABLE_DOCUMENTARY_RESIDUAL`: additional source-region localization is likely useful;
- `CONFIRMED_DOCUMENTARY_GAP`: the known source set has already been systematically reviewed and new evidence/investigation is the proper route;
- `CONFLICT`: multiple claims exist and need adjudication;
- `MEASUREMENT_REQUIRED`: the missing fact is inherently current-state and cannot be recovered safely from historical drawings alone.

This distinction prevents cyclic rework while preserving every unresolved fact explicitly.
