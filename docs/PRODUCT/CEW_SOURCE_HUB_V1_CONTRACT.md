# CEW Source Hub v1 — Product Contract

Status: B1 implementation contract  
Program goal: `CEW-GOAL-01`

## Purpose

Source Hub is the engineer-facing entry point for primary project information. It exposes what sources exist, their immutable identity, their intended engineering use, their provenance/readiness and the work that currently depends on them.

Source Hub is a read/orientation workspace. It does **not** edit a `SourceVersion`, promote engineering claims or infer structural meaning from a document merely because the document is present.

## Authoritative source chain

For N12, B1 consumes the established source/evidence chain by reference:

`immutable archive PDF -> SourceVersion identity -> Page -> page transform -> EvidenceRegion -> Observation / human review`

The primary archive remains `archive/originali-alta-risoluzione` and the operational immutable-source index remains `data/canonical/tavole_originali_remote_index_v1.csv`.

The following registries are source-of-record inputs to the user journey:

- `data/canonical/tavole_originali_remote_index_v1.csv` — primary-source path/hash/classification;
- `data/canonical/CEW_PAGE_REGISTRY_v1.csv` — physical page identity/dimensions;
- `data/canonical/CEW_PAGE_TRANSFORM_REGISTRY_v1.csv` — invertible coordinate transforms;
- `data/canonical/CEW_EVIDENCE_REGION_REGISTRY_v1.csv` — canonical evidence geometry;
- `data/canonical/CEW_SOURCE_VIEWER_BINDINGS_v1.csv` — task/evidence/source/viewer binding;
- `data/canonical/CEW_DERIVED_ASSET_REGISTRY_v1.csv` — review render metadata only.

`CEW_ERW_SOURCE_ASSET_STATUS_v1.csv` is a historical pre-F2 ERW status file and MUST NOT override later READY F2 provenance when the current governed registries demonstrate a reproducible source chain.

## Primary user questions

Source Hub must let the engineer answer without repository knowledge:

1. Which original documents are available?
2. Which of them are currently used by CEW?
3. What is the immutable version/hash of a source?
4. Which project questions/reviews depend on that source?
5. Can I open the original primary source and the evidence locations derived from it?
6. Is a displayed image primary evidence or only a reproducible review aid?

## Required source-card fields

Primary card surface:

- human source label, e.g. `TAV-05A`;
- engineering classification/use;
- immutable/source status;
- number of open review items linked to the source;
- action `Apri fonte`;
- action `Vedi evidenze` when governed EvidenceRegions exist.

Technical details remain expandable and include:

- canonical filename;
- archive commit/ref;
- remote archive path;
- Git blob SHA;
- SHA-256;
- SourceVersion IDs when available through viewer bindings;
- Page IDs;
- derived render IDs and authority state.

## Immutability and integrity rules

1. Source Hub never rewrites, recompresses or replaces the archived PDF.
2. Runtime retrieval of a primary source must be pinned to an immutable commit/ref and verified against the registered SHA-256 before it can be used to create an engineering review image.
3. A review image is always labelled as a **derived reading aid**; authority remains the verified PDF SourceVersion.
4. Hash failure is fail-closed: no review image may be presented as verified evidence.
5. Missing source bytes, render failure or network failure remain visible as source-access residuals; they must not be converted into engineering absence.

## Source Hub route and integration

Authenticated route: `/sources`

Project Home must expose `Fonti` as a real navigation link when B1 is integrated.

Source Hub may provide a source detail route such as `/sources/{source_id}`. The route may include the original PDF viewer or verified runtime preview, but internal GitHub/archive implementation detail must not be required for normal use.

## Human-factors acceptance

### HF-SOURCE-01 — Source orientation
An engineer can distinguish primary source, derived review aid and engineering claim.

### HF-SOURCE-02 — Integrity visibility
Immutable status and source identity are visible; SHA/path details are reachable but secondary.

### HF-SOURCE-03 — Work relevance
The user can see which open evidence reviews depend on a source without decoding task IDs.

### HF-SOURCE-04 — No stale-state override
Historical pre-F2 asset-status records cannot downgrade a currently READY F2 provenance chain in the product UI.

## Completion boundary

Source Hub v1 is complete for B1 only when the authenticated runtime exposes source cards from governed registries, links into Evidence Workspace, preserves the immutable archive/hash boundary and passes the B1 data, engineering, human-factors and production smoke gates.
