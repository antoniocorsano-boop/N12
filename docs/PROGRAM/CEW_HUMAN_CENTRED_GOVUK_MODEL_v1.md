# CEW Human-Centred Service Model v1

Status: REQUIRED PRODUCT DESIGN CONTRACT

CEW adopts the GOV.UK Service Standard and Service Manual as the primary human-centred service-development reference, adapted to structural engineering software.

Primary references:
- https://www.gov.uk/service-manual/service-standard
- https://www.gov.uk/service-manual/service-standard/point-1-understand-user-needs
- https://www.gov.uk/service-manual/service-standard/point-2-solve-a-whole-problem
- https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use
- https://www.gov.uk/service-manual/service-standard/point-6-have-a-multidisciplinary-team
- https://www.gov.uk/service-manual/service-standard/point-7-use-agile-ways-of-working
- https://www.gov.uk/service-manual/service-standard/point-10-define-success-publish-performance-data
- https://www.gov.uk/service-manual/service-standard/point-14-operate-a-reliable-service

## CEW adaptation

1. **Understand users and their needs** — start from the responsible structural engineer, document/evidence reviewer, survey/testing specialist and checker; study the full assessment context, not only the screen interaction.
2. **Solve a whole problem** — design the service around `project -> documents -> evidence -> reconstruction -> model -> properties -> investigations -> scenarios -> FEM -> verification -> intervention -> dossier`, not around repository folders or AI features.
3. **Joined-up experience** — document, drawing, evidence, model and analysis contexts must remain connected through stable identity and provenance.
4. **Simple to use** — users should succeed first time with minimal help; internal IDs and implementation terminology are secondary.
5. **Accessible and inclusive** — interaction, text, contrast, keyboard navigation and responsive behaviour are part of acceptance, not polish.
6. **Multidisciplinary team** — structural engineering, existing-structure assessment, materials/durability, geotechnics, field investigation, computational/FEM, information management, human factors and software/QA are represented in the agent/team model.
7. **Agile/iterative** — expose bounded slices to real representative tasks early, observe, measure and iterate.
8. **Improve frequently** — user difficulty is treated as product evidence; findings change the backlog and acceptance criteria.
9. **Secure/private** — authenticated project data, source integrity and append-only audit remain fail-closed.
10. **Define success and measure it** — every workspace has task-level usability metrics plus product/engineering safety metrics.
11. **Right technology** — technology follows the user and engineering need; CEW is not designed around AI, a solver or a particular UI framework.
12. **Open standards/components where suitable** — preserve interoperable contracts, stable identities and solver-neutral boundaries.
13. **Reliable service** — production behaviour, not only build success, is validated; QA includes human checks for user-facing critical journeys.

## CEW design loop

`USER CONTEXT -> ENGINEERING JOB TO BE DONE -> USER NEED -> END-TO-END JOURNEY -> PROTOTYPE/SLICE -> AUTOMATION BOUNDARY -> ENGINEERING GATE -> USABILITY/HVA -> PRODUCTION OBSERVATION -> ITERATE`

## Mandatory design questions for every slice

- Who is the user and what professional task are they trying to complete?
- What is the complete journey before and after this screen?
- What information must be visible at the decision point?
- What can the machine do deterministically?
- What must remain a human engineering decision?
- How can failure or uncertainty be made visible rather than hidden?
- What task metrics will demonstrate improvement?
- What evidence will prove the deployed service actually works?
