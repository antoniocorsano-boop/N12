# CEW Document Intake & Versioning v1 — Product Contract

Status: `B1.4 PREPARATION`  
Program: `CEW-GOAL-01`

## User need

A project user must be able to add a new document without knowing repository paths or manually deciding whether the file is a duplicate, a new immutable version of an existing source, or a new source.

The system must preserve source identity and never overwrite an existing `SourceVersion`.

## Intake sequence

`local file selection -> local SHA-256 -> metadata-only analysis -> duplicate/version decision -> human classification -> private byte storage -> immutable SourceVersion proposal -> governed promotion`

## Privacy / storage boundary

B1.4 preparation deliberately separates **identity analysis** from **byte upload**.

The browser computes SHA-256 locally using Web Crypto. Before an authorized private object-store exists, CEW sends only:

- filename;
- size;
- MIME type when available;
- SHA-256;
- optional user-selected existing source identity.

The original file bytes remain on the user's device during this metadata-only analysis.

This allows duplicate/version decisions to be tested and used without pretending that Production storage has already been provisioned.

## IntakeCandidate states

- `LOCAL_SELECTED`
- `HASH_READY`
- `EXACT_DUPLICATE`
- `SOURCE_DECISION_REQUIRED`
- `NEW_SOURCE_CANDIDATE`
- `NEW_VERSION_CANDIDATE`
- `HUMAN_CLASSIFICATION_REQUIRED`
- `STORAGE_AUTHORIZATION_REQUIRED`
- `STORED_PRIVATE`
- `SOURCEVERSION_PROPOSAL_READY`
- `REJECTED`
- `FAILED`

## Deterministic duplicate rules

1. Exact SHA-256 match against a registered immutable source means `EXACT_DUPLICATE`.
2. Filename similarity alone must never create a Source binding.
3. A user may explicitly select an existing Source. If SHA differs, the candidate becomes `NEW_VERSION_CANDIDATE`; this still requires human review.
4. Without an explicit existing Source selection and without exact hash match, the candidate remains `SOURCE_DECISION_REQUIRED` / `NEW_SOURCE_CANDIDATE` depending on the completed classification step.
5. The system never overwrites an existing SourceVersion.

## Classification

Human classification must be able to record, at minimum:

- document family;
- discipline;
- project level / scope;
- role / intended project use;
- source identity choice: new Source or new version of existing Source;
- note / provenance about origin.

Machine suggestions may be presented later, but cannot finalize these fields automatically.

## SourceVersion proposal

A candidate may become `SOURCEVERSION_PROPOSAL_READY` only after:

- byte storage is private and verified;
- SHA-256 of stored bytes equals locally computed hash;
- human source/version decision is recorded;
- required classification is complete;
- no exact duplicate remains unresolved;
- storage locator is immutable/versioned;
- the promotion boundary confirms no existing SourceVersion is overwritten.

The proposal is not itself a canonical write.

## Existing N12 sources

The existing N12 source archive is already immutable and registered. It is not re-uploaded through B1.4.

B1.4 is for **new incoming project information** and future versions.

## Storage adapter

Production storage is an adapter, not part of source identity semantics.

Required properties:

- private by default;
- content-addressable or versioned immutable locator;
- server-side or post-upload hash verification;
- no public guessable raw-file URLs;
- bounded file size and MIME controls;
- audit trail;
- deletion/retention policy separate from engineering source identity.

Until such an adapter is configured, CEW must show `STORAGE_AUTHORIZATION_REQUIRED` and must not fake successful ingestion.

## Human-centred acceptance

Representative tasks:

- select a file already present in N12 and correctly understand that no upload/version is needed;
- select a changed file and explicitly choose whether it is a new version of an existing Source;
- select a genuinely new document and understand which classification fields are required;
- understand that hash analysis can happen locally before file bytes leave the device;
- understand that a successful metadata check is not yet a stored SourceVersion.

## Forbidden

- overwriting an immutable SourceVersion;
- binding by filename similarity alone;
- uploading bytes before the declared privacy/storage boundary permits it;
- treating `EXACT_DUPLICATE` as a new version;
- auto-classifying a new source as engineering authority;
- changing engineering epistemic state during intake;
- storing secrets or raw uploaded bytes in audit metadata;
- representing metadata-only analysis as completed source ingestion.
