# CEW Source & Evidence Repository v1

## Milestone

`CEW-F1 — SOURCE_FOUNDATION`

This contract establishes immutable source identity before region-level evidence, AI reading, deep zoom, knowledge graph binding, or calculation handoff.

## Principle

A filename, crop, render, OCR transcript, chat attachment label, repository path, or human description is not by itself a source identity.

A source version becomes operationally `READY` only when CEW can reproduce the exact bytes through a storage locator and verify those bytes against a registered SHA-256 digest.

## Domain objects

### Source

A logical documentary source within a project, such as `TAV-05A`.

Stable across versions. It does not itself identify bytes.

Minimum semantics:
- `source_id`
- `project_id`
- `logical_source_code`
- document role/type when known

### SourceVersion

An immutable byte-level version of a Source.

For `READY` state it requires:
- `source_version_id`
- parent `source_id`
- SHA-256
- reproducible `storage_locator`
- media type
- authority class
- version relationship

Changing bytes creates a new SourceVersion. Existing SourceVersion identity is never overwritten.

### DerivedAsset

A reproducible or disposable representation derived from one SourceVersion, for example:
- page render;
- deep-zoom pyramid;
- crop view;
- enhanced contrast view;
- OCR transcript.

A DerivedAsset is never promoted to `PRIMARY` authority and may not silently replace its parent source.

## Identity and storage

Recommended content-addressed physical key:

`sha256/<first-two-hex>/<full-sha256>`

The physical backend may be filesystem, S3-compatible storage or MinIO. Backend choice does not change documentary authority.

Git remains suitable for:
- contracts;
- registries;
- validators;
- receipts;
- canonical snapshots;
- small reproducible metadata artifacts.

Large primary PDFs/scans and tile pyramids should live in a content-addressed object store or equivalent immutable repository. Their Git-side metadata stores the digest and locator rather than treating a mutable filename as identity.

## Readiness states

These are workflow states, not epistemic states:

- `READY`: SHA-256 and reproducible storage locator are verified.
- `NEEDS_HASH`: locator exists but content digest is not registered/verified.
- `NEEDS_LOCATOR`: digest is known but the exact bytes are not reproducibly addressable.
- `NEEDS_HASH_AND_LOCATOR`: logical source is known, but immutable byte identity is not yet established.
- `UNRESOLVED`: evidence is insufficient to classify the migration gap more precisely.

`DOC/MIS/RIF/INF/ND` remain the engineering epistemic regime and are not replaced by these states.

## Ingestion flow

1. Receive source bytes.
2. Compute SHA-256 before technical interpretation.
3. Check whether identical content already exists.
4. Create or resolve logical Source.
5. Create immutable SourceVersion.
6. Persist bytes at content-addressed locator.
7. Verify read-back hash.
8. Record authority/provenance metadata.
9. Only then permit Page/Region/Observation creation to reference the SourceVersion as `READY`.

If a better scan arrives, repeat the flow and link it using `BETTER_SCAN_OF`; never overwrite the previous bytes.

## Migration from the current N12 repository

Existing N12 artifacts remain valid within their established authority, but CEW-F1 must distinguish:

- logical source references already present in canonical registers;
- exact immutable source bytes/hash/locator;
- derived renders/crops used for reading;
- canonical technical assertions created from prior evidence workflows.

Migration must not invent missing digests or storage paths. A logical source such as TAV-05A may therefore be registered as `NEEDS_HASH_AND_LOCATOR` while its existing technical evidence remains untouched.

## Reference acceptance: TAV-05A and TAV-06A

CEW-F1 is deliberately not complete merely because this schema exists.

The milestone acceptance gate `SOURCE_IDENTITY_PASS` requires both reference primary sources:
- `TAV-05A`
- `TAV-06A`

to have a `READY` SourceVersion with verified SHA-256 and reproducible storage locator.

A crop, transcription gate, 300-dpi render or repository note is insufficient to satisfy this acceptance condition.

## Downstream boundary

CEW-F2 may define `Page`, `EvidenceRegion` and `Observation`, but any new region intended for authoritative provenance must reference a CEW SourceVersion. For migrated historical work, temporary logical-source references may remain explicit until F1 migration closes; they must not be misrepresented as byte-level provenance.
