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

## Repository birth and calculation-report timeline

The repository itself was initialized **after** the calculation-report evidence had already been interpreted.

Chronology on 2026-08-16 UTC:

- `17a90a875de5b17ebb43fae9606669aaefd19e83` at `19:55:42Z` — `chore: initialize N12 structural project registry`. The initial README already states that Telaio 1 and Telaio 5 reconstruction from the calculation report is advanced and states that ZIPs and original photographs remain source/evidence.
- `f638fda8eba30d16718b96bc0a8be800f9c504b2` at `19:55:51Z` — `docs: add canonical evidence and modeling protocol`. It establishes the hierarchy `original source -> raw extraction -> reconciliation -> canonical data -> model`.
- `118bb00109f6429c8ef085b2ad20512ffe263de0` at `19:56:04Z` — `docs: seed structural master register from consolidated evidence`. It records Telaio 1 from calculation-report consolidated v12, Telaio 5 from v17, and historical loads from `RC-P13 / v16`.
- `bcf10e1ae4d93872d7472404bd5cb4d897fc9e37` at `19:56:09Z` — `data: add canonical Telaio 5 geometry`. Rows G1-G3 explicitly carry provenance `RC-P13_v16`.
- `643dc8934ec0c8ac37613ec2880cf9e02f5a9df2` at `19:56:17Z` — historical DXF artifacts are registered.

Forensic consequence: RC-P10 / RC-P13 source photographs pre-date repository initialization. They cannot be expected in the root commit unless they were deliberately imported later. Recovery must therefore focus on later source-import/archive branches, workflow artifacts, and automatic persistence commits.

## Confirmed persistence mechanisms

### 1. Git archive branch

Branch `archive/originali-alta-risoluzione` at `78c20a52db4f391ce0d13b9705b9f04737e218c9` contains original PDF sources under `archive/documentazione_originaria/` and many committed JPG evidence files under `docs/FOGLIO_LAVORO/sdr1_evidence/`.

This proves that binary evidence persistence in Git was actually implemented.

The archive branch history shows a deliberate high-resolution source import:

- `b7dfce208100c28d1e83fba8cf7c52bf01a7befc` — `docs(archive): add 18 original carpenteria PDFs + update manifest`.
- `ef3a84c3fcbb97913fdc448dd2d95acd258e8e8e` — first real document-reading test; evidence crops saved.
- `78c20a52db4f391ce0d13b9705b9f04737e218c9` — `docs(archive): freeze high-resolution original drawings`.

No corresponding import commit has yet been identified for the calculation-report photographs.

### 2. GitHub Actions persistence

Workflow `.github/workflows/render-hires.yml` on `work/m0g-source-recovery` uses `permissions: contents: write`, creates high-resolution source artifacts, commits TAV-02S evidence to `evidence/hires/TAV-02S`, and uploads a retained workflow artifact.

Commit observed from the workflow:

`f5ce01071fe9dcd4d92315f6280531fe726d4e73` — `evidence: persist TAV-02S hires raster and tiles`.

This proves that automatic binary persistence from Actions into Git was active.

A second historical workflow, `.github/workflows/render-archived-structural-sources.yml` on `work/m0-global-model`, reads immutable PDFs directly from `archive/originali-alta-risoluzione`, extracts embedded rasters and commits rendered derivatives to `analysis/source_renders`. Its scope is TAV02S/TAV07, not the calculation-report photographs.

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

### 5. Storey source render artifact recovered

Run: `32526144143`
Workflow: `Storey Source Render`
Artifact:

- id: `9462249667`
- name: `storey-source-renders-v1`
- size: `33018652` bytes
- digest: `sha256:34706315e1c2d7767957a773ff84c0076f2a3a7be5af41d1749f2b1901331049`
- expires: `2026-09-20T20:57:52Z`
- expired: false

The ZIP was downloaded and inspected. It contains exactly:

- `TAV03S_300dpi.jpg`
- `TAV04S_300dpi.jpg`
- `TAV05E_300dpi.jpg`
- `TAV05S_300dpi.jpg`
- `TAV06E_300dpi.jpg`
- `TAV06S_300dpi.jpg`
- `manifest.csv`
- `run_metadata.txt`

It contains no calculation-report photographs and no RC-P10 / RC-P13 material.

## Repository evidence for RC-P10 / RC-P13

`docs/FOGLIO_LAVORO/REGISTRO_EVIDENZE.md` on the high-resolution archive branch records, among others:

- `EV-T04` / `EV-T05` / `EV-T06`: Telaio 5 path, spans and G5 from calculation report / v17;
- `EV-S04`: T5 G1-G4 section `25×70 + 140×20 per C3-C5`, source `RC-P13_v16`;
- `EV-L01`: historical T5 loads, source `RC-P13 / v16`.

Therefore RC-P13 is not merely conversational memory: it is explicitly referenced by the repository's own evidence register dated 2026-08-17 and by the initial canonical data written seconds after repository initialization.

The same branch contains `data/canonical/telaio_5.csv` and related derived/canonical artifacts, but these are not acceptable substitutes for the original RC-P10 / RC-P13 source bytes.

## Important negative findings

1. The root repository was initialized after calculation-report interpretation; no original calculation-report photograph was added in the initialization sequence.
2. The recursive tree of `archive/originali-alta-risoluzione` contains many PDF and JPG binary files, but no path named or directly identifiable as RC-P10 / RC-P13 or calculation-report photograph.
3. The deliberate archive import found so far concerns 18 original carpenteria PDFs, not the calculation report.
4. The inspected live Actions artifacts (`n12-hires-structural-sources`, `n12-hires-tav04arch`, `storey-source-renders-v1`) do not contain RC-P10 / RC-P13.
5. The historical rendering workflows inspected so far are scoped to drawing PDFs/raster, not calculation-report photographs.

Therefore the audit has not yet recovered the original RC-P10 / RC-P13 bytes.

## Current forensic state

`PERSISTENCE_MECHANISM_PROVEN = TRUE`

`CALCULATION_REPORT_KNOWLEDGE_PREDATES_REPOSITORY = TRUE`

`RC_P13_REPOSITORY_REFERENCE_PROVEN = TRUE`

`RC_P10_RC_P13_ORIGINAL_BYTES_RECOVERED = FALSE`

`RC_P10_RC_P13_KNOWN_NEVER_SAVED = FALSE`

The last statement remains important: evidence does not support saying they were never saved. Persistence infrastructure existed and repository records explicitly reference the source. The correct state is **recovery not yet resolved**.

## Next recovery order

1. Enumerate historical Actions runs/artifacts associated with source/evidence/archive branches, prioritizing 2026-08-16 through 2026-08-21 and preserving still-live artifacts before expiry.
2. Inspect artifact metadata and download only artifacts whose names/jobs indicate source, evidence, report, calculation, recovery, archive, snapshot or upload.
3. Inspect automatic persistence commits produced by `github-actions[bot]` and their trees for binary additions with generic filenames.
4. Inspect later branches whose purpose is source/evidence recovery (`work/m0g-source-recovery`, CEW source/evidence branches) for copied source bytes or immutable-source locators.
5. Cross-check any candidate image against known RC-P10/RC-P13 signatures and historical chat timing.
6. If original bytes are found: copy without transformation, compute SHA-256, create governed SourceVersion/Page/EvidenceRegion and unlock HO-RC-001/002 only after reproducibility verification.
7. If only an expired-artifact record is found: register `KNOWN_SAVED_ARTIFACT_BYTES_EXPIRED`, preserving run/artifact metadata as provenance while keeping KG-G5 blocked.

## Authority boundary

Historical consolidated ZIPs, CSVs, chat summaries, OCR output and canonical Telaio 5 data remain derivative evidence and cannot impersonate RC-P10 / RC-P13 SourceVersions.
