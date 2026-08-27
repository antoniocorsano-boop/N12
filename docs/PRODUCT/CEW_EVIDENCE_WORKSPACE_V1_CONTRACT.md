# CEW Evidence Workspace v1 — Product Contract

Status: B1 implementation contract  
Program goal: `CEW-GOAL-01`

## Purpose

Evidence Workspace is the engineer-facing place where a source can be inspected, its governed evidence region understood in context, the linked structural context reviewed and a human engineering observation recorded without learning CEW's internal identifiers or parser grammar.

The workspace integrates three contexts simultaneously:

1. **SOURCE EVIDENCE** — the immutable primary source and its reproducible evidence geometry;
2. **ENGINEERING ENTITY CONTEXT** — what CEW currently knows about the affected structural scope, including explicit `UNBOUND` where applicable;
3. **HUMAN DECISION** — the engineer's observation, outcome and requested epistemic use.

It does not make any of these contexts an authority for the others.

## Source-view scales

Evidence Workspace MUST expose three source scales derived from the same immutable page and the same canonical EvidenceRegion:

- **MICRO** — evidence region itself, intended for direct reading;
- **MESO** — evidence region plus surrounding authored context, intended to understand nearby labels/support sequences/detail continuity;
- **MACRO** — complete source/page context, intended to understand the location and drawing-level semantics.

MICRO and MESO are runtime-derived reading aids. MACRO may use the original PDF/page viewer or a verified full-page preview. None becomes primary authority merely because it is easier to read.

The source chain must remain reconstructible as:

`SourceVersion -> Page -> PageTransform -> EvidenceRegion`

No crop coordinate manually supplied by the UI may replace the canonical region geometry.

## Runtime source rendering

For N12 B1:

- primary PDF location and SHA-256 come from `data/canonical/tavole_originali_remote_index_v1.csv`;
- page identity comes from `CEW_PAGE_REGISTRY_v1.csv`;
- transforms come from `CEW_PAGE_TRANSFORM_REGISTRY_v1.csv`;
- region geometry comes from `CEW_EVIDENCE_REGION_REGISTRY_v1.csv`;
- task/viewer binding comes from `CEW_SOURCE_VIEWER_BINDINGS_v1.csv`.

A runtime renderer may retrieve a PDF only from a commit-pinned immutable archive URL, verify its registered SHA-256, and render the canonical region. Hash mismatch is fail-closed.

## Evidence question presentation

The primary heading must be a human-readable engineering question. Examples:

- `Completa quantità e diametro dell’armatura`;
- `Completa le quote dell’armatura documentata`;
- `Verifica il collegamento tra dettaglio e modello strutturale`.

`ERW-*`, `M1E-*`, `F7`, EvidenceRegion IDs, SourceVersion IDs and transform IDs remain in an expandable **Provenienza tecnica** area.

## Known / unknown / conflict presentation

The workspace must show separately:

- **Già documentato** — current governed claims relevant to the question;
- **Da verificare** — unresolved information, without filling it by analogy;
- **Conflitti o limiti** — explicit conflicts, `UNBOUND`, unreadable dimensions or other constraints;
- **Stato massimo ammissibile** — the epistemic ceiling for this task, presented in understandable terms with the technical state available in provenance.

No visual proximity in the source or model may create structural binding.

## Linked structural context

When `model_entities` contains a governed entity reference, the workspace may display that structural entity/context.

When no entity is bound, or the source binding is structurally `UNBOUND`, the interface must say so explicitly and must not choose the nearest member as a convenience.

B1 does not require a full 3D workspace; it requires a visible linked-entity state that preserves the authority boundary and can be extended by B2.

## Human observation contract

The observation field is natural engineering language.

The user MUST NOT be instructed to type a parser-specific grammar such as a fixed `2 Φ12 superiori + 2 Φ12 inferiori` syntax.

Rules:

1. raw human observation is preserved verbatim in the receipt;
2. machine parsing may extract only explicitly stated semantics;
3. parsing failure never rewrites the observation;
4. directional meaning such as upper/lower must be preserved;
5. `2 Φ12 superiori + 2 Φ12 inferiori` may never be reduced to an undirected `4 Φ12` assertion;
6. missing direction/count/diameter remains missing;
7. a confirmed observation requires direct-primary-source acknowledgement where the task contract requires it.

The historical natural-language form `i filari lunghi 1040 son 2 f 12 superiori e 2 f 12 inferiori` is an admissible style of user input. The UI must accept such natural wording without asking the engineer to reformulate it for the parser.

## Submit boundary

The existing governed F7 chain remains authoritative for review processing:

`human receipt -> receipt validation -> F7 bridge -> promotion evaluation -> semantic gate -> patch candidate`

Evidence Workspace submit:

- may persist a runtime audit receipt;
- may return a governed patch candidate;
- must always retain `canonical_write_authorized=false` and `canonical_write_performed=false` unless a separate future canonical-writer authority explicitly changes the architecture;
- may not mutate F2 geometry;
- may not reopen M0-G;
- may not close R09–R11 when processing R08.

## Human-factors acceptance

### HF-EVIDENCE-01 — Context without repository knowledge
The engineer sees the question, source, known/unknown state and action without interpreting internal IDs.

### HF-EVIDENCE-02 — Three source scales
MICRO, MESO and MACRO are available from the same verified SourceVersion/Page/EvidenceRegion chain.

### HF-EVIDENCE-03 — Simultaneous decision context
Source evidence, linked structural context and human-decision form are present on the same workspace.

### HF-EVIDENCE-04 — Natural engineering language
The observation field contains no prescribed machine grammar and raw input is preserved.

### HF-EVIDENCE-05 — Authority clarity
The interface states that review is not a canonical write and that derived images are reading aids only.

### HF-EVIDENCE-06 — Unbound honesty
An unbound source/model relationship remains explicitly unbound.

## Production acceptance

B1 requires an authenticated production smoke on the deployed CEW runtime. The smoke must verify:

- Project Home -> Source Hub navigation;
- Source Hub -> Evidence Workspace navigation;
- verified source rendering or explicit fail-closed response;
- MICRO/MESO/MACRO controls;
- F7 submit path still available;
- production audit backend remains append-only;
- canonical write remains unauthorized.

No synthetic production receipt containing fabricated engineering evidence may be submitted merely to satisfy the smoke test.
