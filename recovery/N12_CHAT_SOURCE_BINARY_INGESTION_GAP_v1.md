# N12 Chat Source Binary Ingestion Gap v1

Date: 2026-09-09
Scope: forensic diagnosis of historical calculation-report images supplied through conversation, especially the source family containing RC-P10 / RC-P13.

## Finding

N12 had a real and functioning binary-persistence mechanism for repository-resident sources, but conversation-uploaded primary images followed a different path that did not guarantee binary ingestion into the immutable project archive.

This is directly evidenced by the historical calculation relation Page 2 uploaded on 2026-08-22:

- source reference: `USER_UPLOAD_ORIGINAL_CALCULATION_RELATION_PAGE_2_2026-08-22`;
- source class: `USER_UPLOADED_PRIMARY_IMAGE`;
- format / dimensions: PNG, 1305x1740;
- SHA-256: `8728e4d09d5dd3b9c5ce34a5a75bd52dd889e9c55d28991d2b6a35dabdb1a66b`;
- evidence status: `CURRENT` / direct primary source for the claims transcribed from the page;
- explicit residual: binary image remains conversation-provided evidence pending repository binary ingestion; persist original image in immutable project archive when connector permits binary ingestion.

The same record is present on the operational `work/m0-global-model` lineage after the FPEP/M1F merges.

## Why this differs from persisted drawing sources

FPEP P01-P03 operated from repository-resident immutable sources. P01 binds source identity to an object already present in `archive/originali-alta-risoluzione`; P02 materializes high-resolution evidence after verifying SHA-256 and byte size; P03 exports already persisted P02 evidence. Those PRs were merged into `work/m0-global-model`.

Therefore the successful FPEP persistence chain was:

`repository immutable binary -> verified source identity -> deterministic derived evidence -> persisted/exported evidence`

The calculation-report chat-upload path was instead capable of reaching:

`conversation binary -> image fingerprint/hash -> direct-source transcription -> canonical/knowledge registration`

without necessarily completing:

`conversation binary -> immutable repository binary object`

This is the ingestion gap.

## Historical-calculation recovery state

`M1F_EXTERNAL_EVIDENCE_ACQUISITION_QUEUE_v1.csv`, later merged through PR #39 into `work/m0-global-model`, still keeps `M1F-EXT-005` as `READY_ON_NEW_SOURCE` and explicitly requests recovery of the previously photographed 12 calculation pages or the complete historical calculation dossier.

`M1F_HISTORICAL_CALC_SOURCE_AVAILABILITY_v1.csv` states that:

- the active operational tree does not contain a complete historical calculation-frame/load-page source set;
- the immutable drawing archive contains the registered original drawing PDFs but no separately named historical calculation dossier;
- `archive/source-index` contains the source-index structure and canonical `telaio_5.csv`, not the missing calculation-page archive.

Thus the 24 August FPEP/M1F lineage had already diagnosed the same source-byte residual.

## RC-P10 / RC-P13 implication

The repository proves that RC-P13 was used as documentary authority for Telaio 5 sections and historical loads, and historical chat/consolidated evidence proves that RC-P10/RC-P13 images were supplied before repository initialization.

However, as of this audit:

- no immutable repository binary has been recovered for RC-P10;
- no immutable repository binary has been recovered for RC-P13;
- no currently inspected live Actions artifact contains those source images;
- no evidence supports declaring that they were never saved somewhere outside the currently recovered stores;
- the Page-2 record proves that conversation-uploaded relation images could be fingerprinted and used while their binary remained outside repository ingestion.

Correct state:

`CHAT_SOURCE_BINARY_INGESTION_GAP_PROVEN = TRUE`

`REPOSITORY_BINARY_PERSISTENCE_MECHANISM_PROVEN = TRUE`

`RC_P10_RC_P13_REPOSITORY_BINARY_RECOVERED = FALSE`

`RC_P10_RC_P13_NEVER_SAVED = NOT_PROVEN`

## Required correction for CEW/N12

A future primary image supplied through chat, file library, connector, browser or other transient surface must not become promotion-capable merely because its content and SHA-256 have been recorded.

Before any source-dependent evidence can become promotion-capable, the system must require:

1. original byte acquisition;
2. SHA-256 and byte-size verification;
3. immutable project storage / repository or governed object-store locator;
4. stable `SourceVersion` identity;
5. reproducible `Page` / image geometry;
6. only then `EvidenceRegion -> Observation -> interpretation`.

If the runtime cannot persist the original bytes, the source may support provisional analysis but must carry an explicit blocker such as `SOURCE_BYTES_NOT_MATERIALIZED` and must not satisfy a reproducibility/promotion gate.

## Recovery consequence

For RC-P10 / RC-P13, derived data, historical consolidated ZIP descriptions, chat summaries, canonical Telaio 5 tables, OCR output and knowledge-graph assertions remain useful recovery aids but cannot substitute for the original image SourceVersion.

The remaining forensic search should prioritize historical Actions artifacts, attachment/object identifiers and any external immutable storage references. Repeating semantic searches over the derived textual corpus has low expected value.
