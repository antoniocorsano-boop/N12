# N12 Source Preservation Policy v1

## Purpose
Prevent recurrence of the historical `CHAT_SOURCE_BINARY_INGESTION_GAP`.

## Mandatory chain
For every primary source received from chat, File Library, Drive, scanner, camera, email or other transient channel:

`original bytes -> SHA-256 -> immutable persistent archive -> independent redundant backup -> SourceVersion -> Page -> EvidenceRegion -> Observation/interpretation`

No interpretive or canonical promotion may bypass this chain.

## Fail-closed rules
1. A chat attachment is transient until its bytes are persisted outside the conversation runtime.
2. A transcription, OCR result, crop, screenshot, CSV, SVG or derived raster never replaces the primary source.
3. Every derived asset must store the source SHA-256 and transformation provenance.
4. If source bytes are unavailable, state is `SOURCE_BYTES_MISSING`; knowledge may remain historical/reference-only but cannot be promoted as newly verified evidence.
5. Original bytes are immutable. Rotation, crop, enhancement, OCR and annotation create derived assets only.
6. Recovery packages require an inventory and individual hashes before interpretation.
7. Minimum preservation redundancy: one immutable source archive, one independent backup, and one repository manifest containing hashes and locators.

## Recovered package 2026-09-09
- 43 original JPG photographs recovered.
- RC-P10 and RC-P13 identified from visible page marks and technical content.
- Canonical preservation bundle: `N12_RECOVERY_CANONICAL_2026-09-09.zip`.
- Bundle SHA-256: `4afcb3adaec87813fa888d5ccea5d5ffad60df92e9a8b98d00a524d950a61a64`.
- Redundant Drive copy ID: `1OsVXN7PwEKBCOU379qU1YAcF5lGhiyvG`.
- Repository binary ingestion remains a separate required step; the manifest does not pretend that Git contains the image bytes.

## Authority boundary
This policy governs provenance and preservation only. It does not itself authorize structural assertions, canonical model writes, or KG-G5 promotion.
