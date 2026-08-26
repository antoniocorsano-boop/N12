# CEW Engineering Workbench v0

Status: UX1 COMPLETE — EXPERIMENTAL / NON-PROMOTIVE  
Work item: `UX1-001`  
Parent: `CEW Human Engineering Experience Foundation v1`

## Purpose

This tranche creates the first single CEW professional workbench rather than another isolated viewer.

The reference vertical slice is the real N12 evidence unit `T6A-G03`:

`immutable primary PDF -> measured page -> frozen EvidenceRegion -> professional source view -> structural context -> explicit human decision -> non-promotive receipt proposal`

The workbench is a **read model and decision surface**. It is not a canonical writer.

## Canonical snapshot boundary

The UI does not read the stale historical copies of F2 registries inherited by experimental Platform branches.

The first slice instead consumes a pinned read snapshot from canonical commit:

`b4356bc78807257901a0b97892a63d9f4c9744c9`

and records the exact archive source:

- archive commit `78c20a52db4f391ce0d13b9705b9f04737e218c9`
- PDF `archive/documentazione_originaria/tavola 6.pdf`
- Git blob `c3048472adfdaa5b1e902f84c20ccfb20d679b1f`
- page render 300 dpi, `4299 x 25376 px`
- EvidenceRegion `CEW-N12-REG-T6A-G03`
- bbox normalized `[0.0, 0.579287, 1.0, 0.110341]`
- document-region state `READY`
- structural-binding state `UNBOUND`

`READY` evidence never implies a structural binding.

UX1 is an **experimental work item**, not a canonical CEW milestone. Its read context is `CEW-F2` because `T6A-G03` is one of the evidence units governed there. The workbench does not close F2, emit `EVIDENCE_PROVENANCE_PASS`, or authorize F3 or any later canonical milestone.

## Source staging

The primary PDF is authoritative. The browser raster is derivative review context only.

`scripts/cew_workbench_stage_tav06a.sh` fetches the exact pinned archive commit, proves the Git blob SHA, renders the first page at 300 dpi and checks the expected dimensions before emitting a runtime manifest.

If any source identity or render dimension drifts, the stage fails and the human decision controls remain disabled.

## Human interaction

Primary language is professional and contextual:

- “Tavola 6 — Armature copertura”
- “Schema di armatura di copertura”
- “Regione documentale verificata”
- “Associazione strutturale non determinata”

Raw CEW IDs live under **Provenienza tecnica**, not in the primary task language.

No decision is preselected. Because this slice has no registered structural target, `CONFIRMED` is not actionable. The UI exposes only non-promotive UX1 review outcomes and makes the unavailable confirmed path explicit.

## Receipt boundary

The frontend can create only:

`NON_PROMOTIVE_HUMAN_DECISION_PROPOSAL`

with `canonical_write = false`.

The proposal identifies `work_item = UX1-001`, `canonical_context = CEW-F2`, and `authority = EXPERIMENTAL_NON_PROMOTIVE`; it does not claim a canonical milestone transition.

No `POST`, `PUT`, `PATCH` or `DELETE` network path is present in frontend source.

A future governed intake adapter may validate a proposal against the human-decision receipt contract; that adapter remains outside this browser tranche and cannot promote evidence merely because a UI proposal exists.

## OSS implementation

Pinned direct dependencies are current stable releases verified on 2026-08-26:

- React `19.2.8`
- React Aria Components `1.20.0`
- OpenSeadragon `6.1.0`
- Vite `8.2.2`
- Storybook React/Vite `10.5.10`
- Playwright `1.62.1`
- `@axe-core/playwright` `4.13.0`

Third-party packages provide behavior/infrastructure. CEW owns engineering semantics, tokens, contracts and authority boundaries.

## Completion record

UX1 implementation authority was reviewed and aligned with the current canonical `CEW-F2` context before completion. The validated implementation head is `916a266aead0a4095252774fb573bc4ec3051496`; its Workbench, UX Foundation and Knowledge System gates are PASS, including Playwright interaction tests and the axe serious/critical accessibility gate.

The completion receipt is persisted at `automation/receipts/UX1-001.json` with `canonical_promotion = false`. Completion of this experimental product work item does not bind `T6A-G03`, close CEW-F2, emit `EVIDENCE_PROVENANCE_PASS`, or authorize F3 or later milestones.
