# CEW Code Development Model v1

Status: REQUIRED DEVELOPMENT CONTRACT

CEW adopts the delivery pattern already used in Docente OS and CurManLight Arena, adapted to structural engineering.

## Delivery loop

`CANONICAL BASELINE -> SMALL VERTICAL SLICE -> DEDICATED BRANCH -> PR -> AUTOMATED GATES -> HUMAN/VISUAL ACCEPTANCE -> PRODUCTION SMOKE -> RECEIPT -> PROMOTION`

## Rules

- Every slice starts from an explicit baseline SHA/ref.
- One branch carries one bounded product objective.
- A slice integrates data contract, runtime, user journey, tests and governance where applicable.
- Pull request review precedes promotion.
- Automated checks are necessary but not sufficient for user-facing engineering workflows.
- Human/Visual Acceptance is mandatory for representative journeys.
- Production capability requires a real deployed smoke test.
- Failed gates are investigated; tests are not weakened only to obtain green CI.
- Parallel preparation is allowed; promotion is serialized by the product orchestrator.
- Every completed slice has a receipt recording baseline, head, outputs, gates, residuals and boundaries.
- Engineering data is never altered merely to satisfy product tests.
- UI, agents, parsers and solvers do not become engineering authority by implementation convenience.

## Gate families

`DATA_GATE`, `ENGINEERING_GATE`, `INTEGRATION_GATE`, `HUMAN_GATE`, `HUMAN_AUTHORITY_GATE`, `HUMAN_FACTORS_GATE`, `HVA_GATE`, `SECURITY_GATE`, `PRODUCTION_SMOKE`, `QA_GATE`.

## Completion

A slice is COMPLETE only when its bounded goal is achieved, required checks pass on one identified revision, HVA/usability evidence exists where applicable, production smoke passes when production changes, no blocking residual remains, a receipt is archived and the orchestrator releases the next slice.

## Forbidden patterns

- long-lived branches accumulating unrelated work;
- architecture-only completion without runtime evidence;
- weakening gates to preserve legacy assumptions;
- treating a successful build as a successful service;
- exposing repository identifiers as the primary workflow;
- hidden manual corrections without provenance;
- normalization that loses engineering meaning.
