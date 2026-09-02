# CEW — New Project Pre-Acquisition Analysis v1

## Decision

A new CEW project MUST NOT begin from a known object list such as columns, beams, walls or foundations.

The initial user interaction begins from the project documents themselves. CEW first builds a source-bound, non-semantic map of the document set, discovers recurring graphic structures, compares those structures with governed reference knowledge, and only then asks the human high-information questions that can teach project-local meanings.

The canonical upstream sequence for a new project is therefore:

```text
DOCUMENT INTAKE
  -> IMMUTABLE SOURCE REGISTRATION
  -> DOCUMENT / PAGE PREFLIGHT
  -> GRAPHIC PRIMITIVE DISCOVERY
  -> NON-SEMANTIC GRAPHIC CLUSTERING
  -> GOVERNED LIBRARY MATCH PROPOSALS
  -> HUMAN TRIAGE / TEACH "THIS IS A..."
  -> PROJECT-LOCAL PROTOTYPES AND FAMILIES
  -> FIND SIMILAR
  -> GROUP REVIEW + EXCEPTIONS
  -> CANONICAL CAD PROMOTION
  -> STRUCTURAL IDENTITY
  -> ENGINEERING USE
```

No downstream stage may repair or silently fill gaps in an upstream stage.

## Why this is required

The G4/TAV-05S pilot begins from unusually strong prior information: a known support register and five candidate section families. That is suitable for validating Object Acquisition, but it is not representative of a new project.

In a new project CEW may initially know only:

- one or more files;
- their bytes, origin and acquisition context;
- page boundaries;
- whether pages are vector, raster, mixed or sparse;
- graphic/text/image primitives that can be extracted reproducibly.

CEW MUST NOT assume that a repeated rectangle is a column, that a long line is a beam, or that a familiar symbol carries the same meaning as in another project.

## 1. Stage NP0 — Document intake

### Input

Raw project documents supplied by the user or acquired through an explicitly governed import.

### Required output

For every source:

- `Source` identity;
- immutable `SourceVersion`;
- exact SHA-256;
- source locator / acquisition record;
- media type;
- page count when applicable;
- original bytes retained as evidentiary authority.

### User interaction

The user should primarily answer document-level questions, not object-level questions:

- "These are all the documents currently available";
- "This file is a structural drawing / calculation report / survey / unknown";
- "These two files are revisions of the same document";
- "This document is incomplete / uncertain".

Unknown is a valid state.

## 2. Stage NP1 — Automatic document/page preflight

CEW analyzes each page without requiring semantic object knowledge.

Minimum signals:

- native vector drawing count;
- text block count;
- raster image regions;
- page geometry and rotation;
- density / distribution of drawing content;
- presence of repeated graphic structures;
- extraction modality: `NATIVE_VECTOR`, `RASTER_OR_SCANNED`, `MIXED`, `TEXT_OR_SPARSE`.

The preflight determines which later extractors are applicable. It does not assign structural meaning.

## 3. Stage NP2 — Graphic primitive discovery

CEW generates source-bound `GraphicPrimitiveCandidate` records from reproducible page geometry.

Initial primitive families include:

- `TEXT_BLOCK`;
- `LINEAR_STROKE_GROUP`;
- `RECTILINEAR_CLOSED_SHAPE`;
- `CURVED_OR_ARC_SHAPE`;
- `FILLED_OR_HATCHED_REGION`;
- `RASTER_IMAGE_REGION`;
- `COMPLEX_VECTOR_GROUP`;
- `UNKNOWN_GRAPHIC_GROUP`.

Each candidate MUST carry:

- `source_version_id`;
- page index / page identity;
- normalized bbox;
- detector and detector version;
- a stable feature signature;
- geometry/statistics used to derive that signature;
- `semantic_meaning = null`.

A crop may be generated as a reading aid, but it is not the candidate identity or evidentiary authority.

## 4. Stage NP3 — Non-semantic clustering

The first clustering question is:

> "Which graphic occurrences appear to belong to the same visual/topological family?"

It is NOT:

> "Which occurrences are columns?"

CEW groups primitive candidates using stable features such as:

- primitive family;
- aspect ratio bucket;
- relative scale bucket;
- stroke/fill family;
- topology signature;
- local neighbourhood pattern;
- visual embedding or raster descriptor when governed and reproducible.

Output: `GraphicClusterCandidate`.

A cluster receives an opaque project-local identity such as `GC-0007`, not a structural label.

## 5. Stage NP4 — Governed graphic reference library

CEW may compare a project cluster against a shared Graphic Knowledge Fabric / reference library.

The library is advisory, never evidentiary authority for the current project.

### Required library tiers

1. `EXTERNAL_REFERENCE`
   - documentation, standards, manuals, public example drawings and other externally acquired sources;
   - each source must retain URL/source identity, acquisition date, license/usage note where available, hash/fingerprint and extraction provenance.

2. `SHARED_VALIDATED`
   - cross-project examples/generalizations accepted through CEW human governance;
   - positive, negative and uncertain examples are retained;
   - generalizations have explicit scope such as discipline, document family, drafting era, notation family, country/language and source modality.

3. `PROJECT_LOCAL`
   - examples taught by the current project's human reviewer;
   - highest relevance for the current project, but still separate from canonical object promotion.

### Library match output

A match is a `KnowledgeMatchProposal`, for example:

```text
GC-0007
  possible meaning: COLUMN_SYMBOL
  library layer: SHARED_VALIDATED
  score: 0.82
  supporting examples: 14
  counterexamples: 2
  project semantic authority: NONE
```

The system must show both support and conflict where available.

### Internet acquisition rule

Information found on the internet MUST NOT be converted directly into project truth.

External material is first acquired into an evidence-backed reference pack. Only then may it contribute to a library proposal. The pack must be reproducible and fingerprinted. A model's general knowledge or an unrecorded web result is not a CEW library entry.

## 6. Stage NP5 — Human triage interaction

The initial CEW interface for a new project is a **Document Discovery Workspace**, not an object register.

Recommended interaction sequence:

### A. Documents

Show:

- document cards;
- page thumbnails / CAD-like page view;
- modality and extraction status;
- warnings and unreadable pages;
- suggested document family only as a proposal.

Human actions:

- `CONFIRM_DOCUMENT_FAMILY`;
- `CORRECT_DOCUMENT_FAMILY`;
- `LEAVE_UNKNOWN`.

### B. Discovered graphic families

Show cluster cards such as:

```text
Family GC-0007
27 similar occurrences
mostly rectangular
repeated on pages 1, 2, 4
library suggestions:
  74% COLUMN_SYMBOL
  18% GRID_OR_MARKER
```

Do not make the user inspect thousands of raw primitives.

Human actions:

- `THIS_IS_A...` / `TEACH_THIS_IS`;
- `NOT_THIS`;
- `UNCERTAIN`;
- `SPLIT_CLUSTER`;
- `MERGE_CLUSTERS`;
- `IGNORE_FOR_NOW`.

### C. Teach once, search many

Once the human labels a representative occurrence or corrected bbox:

```text
human example
  -> ObjectPrototype / graphic training example
  -> FIND_SIMILAR
  -> ranked occurrence proposals
  -> group approval / rejection
  -> exceptions only
```

This is the default mature workflow. Local snap remains a geometry-editing aid, not a recognizer.

## 7. Stage NP6 — Project-local vocabulary formation

As human labels accumulate, CEW builds project-local knowledge:

- meanings;
- prototypes;
- positive examples;
- negative examples;
- uncertain examples;
- families;
- page/context affinities;
- exceptions.

Only after this stage may the UI increasingly use semantic names such as "pilastro" instead of opaque cluster IDs.

## 8. Stage NP7 — Object Acquisition and review

Project-local prototypes drive `FIND_SIMILAR` across pages and documents.

Every result remains an `ObjectCandidate` until reviewed.

Human review should operate primarily on groups:

- approve clear group;
- reject false positives;
- reassign outliers;
- mark ambiguous;
- teach additional prototype when a family is heterogeneous.

## 9. Promotion boundary

The following are separate gates and MUST NOT collapse into one action:

1. graphic occurrence discovered;
2. cluster membership proposed;
3. semantic meaning proposed;
4. human project meaning validated;
5. object occurrence localized;
6. object type/family confirmed;
7. canonical EvidenceRegion promoted;
8. canonical CAD object promoted;
9. structural identity assigned;
10. engineering use authorized.

## 10. Authority model

All NP0–NP6 automatic outputs have:

```json
{
  "semantic_authority": "NONE_UNTIL_PROJECT_HUMAN_VALIDATION",
  "canonical_write_authorized": false,
  "structural_identity_authorized": false,
  "engineering_authority_effect": "NONE"
}
```

A library proposal can improve ranking. It cannot establish project truth.

## 11. Determinism and provenance requirements

A pre-acquisition result must be reproducible from:

```text
immutable SourceVersion
+ extractor version
+ extraction parameters
+ optional governed library generation/fingerprint
```

Every candidate and cluster must trace back to source/page geometry. Library proposals must also name the exact library generation/pack used.

## 12. Library readiness rule

CEW MUST explicitly distinguish:

- `LIBRARY_NOT_CONFIGURED`;
- `LIBRARY_EMPTY`;
- `LIBRARY_AVAILABLE_UNVERIFIED_FOR_CONTEXT`;
- `LIBRARY_MATCHES_AVAILABLE`.

The system must never imply that a mature internet-derived graphic library exists when no governed pack has actually been imported and validated.

## 13. First implementation slice

The first executable slice for this analysis is intentionally upstream and generic:

```text
arbitrary PDF bytes
  -> source hash verification
  -> per-page modality preflight
  -> source-bound graphic primitive candidates
  -> deterministic non-semantic cluster candidates
  -> optional governed reference-pack matching
  -> human-triage queue
```

No N12-specific support IDs, column families or structural labels are permitted as required input.

## 14. Acceptance gates

The slice passes only if:

- a synthetic/unknown PDF can be processed with zero semantic prior;
- every primitive candidate is source/page/bbox bound;
- clusters have opaque IDs and no automatic semantic meaning;
- optional reference-pack matches remain proposals only;
- absence of a library is explicit and non-fatal;
- no canonical, structural or engineering authority is granted;
- the result exposes a human triage queue rather than silently promoting objects;
- the same source bytes and extractor version produce stable candidate/cluster identities.

## 15. Relationship to the G4 pilot

The G4 pilot remains a downstream validation of the mature interaction pattern:

```text
TEACH_THIS_IS -> FIND_SIMILAR -> REVIEW_SIMILAR_GROUP
```

The New Project Pre-Acquisition workflow defined here is what produces the unknown clusters and first human teaching opportunities that precede that pattern on a real greenfield project.
