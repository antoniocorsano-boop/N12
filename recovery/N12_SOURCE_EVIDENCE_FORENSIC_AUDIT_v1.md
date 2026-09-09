# N12 Source Evidence Forensic Audit v1

Date: 2026-09-09
Scope: recovery of original source bytes for historical calculation-report evidence, especially RC-P10 / RC-P13 used in Telaio 5 reconstruction.

## Purpose

Establish where historical source evidence was actually persisted and distinguish:

- original source bytes still recoverable;
- derived evidence persisted in Git;
- workflow artifacts still recoverable;
- historical source traces without current bytes;
- derived/canonical knowledge that must not substitute for source evidence.

No canonical engineering data is modified by this audit.

## Confirmed persistence mechanisms

### 1. Git archive branch

Branch `archive/originali-alta-risoluzione` at `78c20a52db4f391ce0d13b9705b9f04737e218c9` contains original PDF sources under `archive/documentazione_originaria/` and many committed JPG evidence files under `docs/FOGLIO_LAVORO/sdr1_evidence/`.

This proves that binary evidence persistence in Git was actually implemented.

### 2. GitHub Actions persistence

Workflow `.github/workflows/render-hires.yml` on `work/m0g-source-recovery` uses `permissions: contents: write`, creates high-resolution source artifacts, commits TAV-02S evidence to `evidence/hires/TAV-02S`, and uploads a retained workflow artifact.

Commit observed from the workflow:

`f5ce01071fe9dcd4d92315f6280531fe726d4e73` — `evidence: persist TAV-02S hires raster and tiles`.

This proves that automatic binary persistence from Actions into Git was active.

### 3. Live GitHub Actions artifact recovered

Run: `32421411208`
Workflow: `Render N12 HiRes Sources`
Head: `1e37ce1b7f02d0a6f68e2b3c5f21aed3c87e1796`
Artifact:

- id: `9425842602`
- name: `n12-hires-structural-sources`
- size: `227732563` bytes
- digest: `sha256:a604ce707225a67c12b26a617ca4255e0d6e47c0a3f4eb38d0e5c164eec8255b`
- created: `2026-08-20T21:51:45Z`
- expires: `2026-09-19T21:51:37Z`
- expired: false

The archive was downloaded and inspected. It contains 106 entries, including original PDFs, native raster and tiles for:

- TAV-01S
- TAV-02S
- TAV-05E
- TAV-06E
- TAV-06A
- TAV-07A

It does **not** contain RC-P10 / RC-P13.

### 4. Architectural HiRes artifact

Run: `32388803766`
Workflow: `Render N12 Architectural HiRes`
Artifact:

- id: `9413992775`
- name: `n12-hires-tav04arch`
- size: `54276128` bytes
- digest: `sha256:8955a685029669a907ad4a7eb8f1456161883adeb7788c0da39305bf67131b12`
- expires: `2026-09-19T15:53:44Z`
- expired: false

Scope is TAV-04 architectural source; no current evidence connects it to RC-P10 / RC-P13.

## Repository evidence for RC-P10 / RC-P13

`docs/FOGLIO_LAVORO/REGISTRO_EVIDENZE.md` on the high-resolution archive branch records, among others:

- `EV-T04` / `EV-T05` / `EV-T06`: Telaio 5 path, spans and G5 from calculation report / v17;
- `EV-S04`: T5 G1-G4 section `25×70 + 140×20 per C3-C5`, source `RC-P13_v16`;
- `EV-L01`: historical T5 loads, source `RC-P13 / v16`.

Therefore RC-P13 is not merely conversational memory: it is explicitly referenced by the repository's own evidence register dated 2026-08-17.

The same branch contains `data/canonical/telaio_5.csv` and related derived/canonical artifacts, but these are not acceptable substitutes for the original RC-P10 / RC-P13 source bytes.

## Important negative finding

The recursive tree of `archive/originali-alta-risoluzione` contains many PDF and JPG binary files, but no path named or directly identifiable as RC-P10 / RC-P13 or calculation-report photograph.

The current `work/m0g-source-recovery` workflows cover structural and architectural drawing sources, not the historical calculation-report photographs.

Therefore the audit has not yet recovered the original RC-P10 / RC-P13 bytes.

## Current forensic state

`PERSISTENCE_MECHANISM_PROVEN = TRUE`

`RC_P13_REPOSITORY_REFERENCE_PROVEN = TRUE`

`RC_P10_RC_P13_ORIGINAL_BYTES_RECOVERED = FALSE`

`RC_P10_RC_P13_KNOWN_NEVER_SAVED = FALSE`

The last statement is important: evidence does not support saying they were never saved. Persistence infrastructure existed and repository records explicitly reference the source. The correct state is **recovery not yet resolved**.

## Next recovery order

1. Enumerate historical Actions runs/artifacts associated with source/evidence/archive branches, prioritizing 2026-08-16 through 2026-08-21.
2. Inspect artifact metadata and download only artifacts whose names/jobs indicate source, evidence, report, calculation, recovery, archive, snapshot or upload.
3. Inspect automatic persistence commits produced by `github-actions[bot]` and their trees for binary additions with generic filenames.
4. Cross-check any candidate image against known RC-P10/RC-P13 signatures and historical chat timing.
5. If original bytes are found: copy without transformation, compute SHA-256, create governed SourceVersion/Page/EvidenceRegion and unlock HO-RC-001/002 only after reproducibility verification.
6. If only an expired-artifact record is found: register `KNOWN_SAVED_ARTIFACT_BYTES_EXPIRED`, preserving run/artifact metadata as provenance while keeping KG-G5 blocked.

## Authority boundary

Historical consolidated ZIPs, CSVs, chat summaries, OCR output and canonical Telaio 5 data remain derivative evidence and cannot impersonate RC-P10 / RC-P13 SourceVersions.
