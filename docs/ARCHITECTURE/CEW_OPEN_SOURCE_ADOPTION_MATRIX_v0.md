# CEW Open Source Adoption Matrix v0

Status: EXPERIMENTAL DECISION RECORD
Date: 2026-08-26

Principle: CEW owns identity, evidence, provenance, epistemic state, generations, promotion and engineering contracts. External projects provide specialist engines behind ports/adapters.

| Capability | Candidate | Decision v0 | CEW role / constraint |
|---|---|---|---|
| Programmatic PDF extraction | PyMuPDF | ADOPT_NOW | Primary practical extractor already used; output remains generation-bound. |
| Independent PDF paths/text/images | docling-parse | ADOPT_NOW_AS_SECOND_READER | Independent extraction path for agreement/cross-check; never automatic promotion. |
| OCR/layout/document parsing | PaddleOCR 3.x family | BENCHMARK_FOR_ADOPTION | Run locally where possible; use behind provider-neutral OCR/Layout port; coordinates and model version required. |
| Raster geometry | OpenCV | ADOPT_NOW | Primitive extraction/preprocessing only; CEW performs normalization, classification and provenance. |
| HiRes source navigation | OpenSeadragon | ADOPT_NOW | Viewer/query surface; source identity and coordinate transforms remain CEW authority. |
| Canonical relational persistence | PostgreSQL | TARGET_CORE | Source/evidence/entity/generation/decision records. |
| Spatial indexing | PostGIS | TARGET_CORE | Page/region/2D/3D geometry indexing and geometric queries. |
| Semantic similarity | pgvector | TARGET_SECONDARY_INDEX | Embeddings improve retrieval/clustering; never source of truth. |
| Local analytical extracts | DuckDB/Parquet | ADOPT_WHEN_USEFUL | Reproducible analytics/export layer, not canonical write authority. |
| Graph algorithms | NetworkX | ADOPT_NOW_FOR_IN_PROCESS | Connectivity, graph validation, traversal and comparison; graph database deferred until demonstrated need. |
| IFC interoperability / geometry | IfcOpenShell | ADOPT_ADAPTER | IFC export/import and geometry utilities; CEW Smart Entity remains canonical. |
| BIM authoring UI | Bonsai | BENCHMARK_OPTIONAL | Useful human/IFC surface; do not couple CEW core to its UI/release cadence. |
| Agent durable execution | LangGraph | BENCHMARK_EXECUTION_LAYER | Use only for long-running/resumable/HITL execution; CEW queue/result/gate contracts remain authority. |
| Structural FEM Python | OpenSeesPy | BENCHMARK_SOLVER_A | Strong nonlinear structural-analysis candidate; adapter must round-trip CEW IDs. |
| General FEM | Code_Aster | BENCHMARK_SOLVER_B | Independent mature verification route; adapter must expose unsupported features and mapping. |
| Commercial FEM | EdiLus EE | EXTERNAL_ADAPTER | User engineering workflow target; never CEW canonical authority. |

## Adoption gates

A component is `ADOPT_NOW` or promoted from `BENCHMARK` only when:

1. it can run reproducibly in the CEW supported environment;
2. model/library version is captured in receipts;
3. source coordinates/IDs survive transformation where applicable;
4. failures are detectable and fail closed;
5. outputs can be regenerated from immutable inputs;
6. it does not require CEW to weaken epistemic/provenance rules;
7. a generic adapter/port isolates vendor/library churn;
8. representative N12 cases pass before declaring production use.

## Explicit non-decisions

- No dedicated graph database is required yet. PostgreSQL/PostGIS plus explicit relational edges and NetworkX are sufficient until measured workloads prove otherwise.
- No standalone vector database is required yet. pgvector keeps semantic indexes next to canonical relational metadata.
- No single OCR/HTR model is canonical. Recognition engines create observations; validated meanings belong to CEW.
- No FEM solver is authoritative. Solver agreement/disagreement is evidence about the analysis projection, not a rewrite of project evidence.
- No BIM/IFC file is the CEW canonical database. IFC is a versioned interoperable projection of Smart Entities.
