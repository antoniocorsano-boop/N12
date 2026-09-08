# CEW Visual Prototype Learning Architecture v1

## Status

**CANONICAL PROJECT ANALYSIS — IMPLEMENTATION FOUNDATION**

This document freezes the learning architecture for Civil Existing Workflow (CEW). It applies upstream of object classification, canonical CAD promotion and structural identity.

## Problem

A genuinely new project starts with documents, not known columns, beams, walls or foundations. CEW must therefore be able to discover recurring graphics, ask the human what selected examples mean, remember positive and negative examples, and improve similarity proposals over time without turning model output into project truth.

## Canonical learning sequence

```text
DOCUMENT INTAKE
  -> IMMUTABLE SOURCE REGISTRATION
  -> PAGE PREFLIGHT
  -> GRAPHIC PRIMITIVE DISCOVERY
  -> NON-SEMANTIC CLUSTERING
  -> EXTERNAL REFERENCE PROPOSALS
  -> HUMAN TRIAGE
  -> TEACH_THIS_IS / POSITIVE / NEGATIVE / AMBIGUOUS
  -> LEARNING RECEIPT
  -> PROJECT-LOCAL PROTOTYPE MEMORY
  -> FIND_SIMILAR
  -> GROUP REVIEW
  -> more learning receipts
  -> later promotion gates
```

Learning is iterative. Human correction is training evidence, not a discarded interaction event.

## Four distinct knowledge layers

### 1. External Reference Memory

Human-reviewed public standards, manuals and graphical conventions.

- tier: `EXTERNAL_REFERENCE`
- may suggest similarity or context;
- never establishes project meaning;
- never becomes project-local training evidence automatically.

### 2. Generic Learned Prototype Memory

Cross-project examples that may eventually be promoted after independent governance and sufficient evidence. This tier is **not automatically populated by v1**.

### 3. Project-local Prototype Memory

Human-taught concepts for one project. This is the first operational learning tier.

Examples:

- “this is the graphic family I mean by column in this project”;
- positive occurrences confirmed by the human;
- rejected false positives as counterexamples;
- ambiguous examples retained but excluded from positive/negative centroids.

### 4. Counterexample Memory

Negative examples are first-class learning evidence. They are retained with the same source/provenance discipline as positive examples and penalize future similarity proposals.

## Embedding channels

CEW must not couple its learning model to one foundation model. A `VisualEmbedding` is a governed feature vector with an explicit provider, version and input fingerprint.

### Channel A — Structured Graphic Descriptor

Implemented in v1 and available without machine-learning dependencies.

Signals include:

- primitive family;
- aspect bucket;
- area bucket;
- complexity bucket;
- filled/not-filled;
- stroke-width bucket.

This channel is deterministic and explainable. It is useful immediately but is not presented as a visual foundation model.

Provider id:

`CEW_STRUCTURED_GRAPHIC_DESCRIPTOR_V1`

### Channel B — Visual Foundation Embedding

Target provider: **DINOv3 frozen feature extraction**.

DINOv3 is treated as a pluggable feature provider, not as project authority. CEW must remain functional when it is unavailable. The initial contract state is:

`DINOV3_PROVIDER_NOT_CONFIGURED`

A future provider implementation may add image-region embeddings and dense retrieval without changing the learning receipts or prototype-memory schema.

### Optional proposal helpers

SAM-family segmentation and open-set grounding/detection models may later assist region proposal and user interaction. They are proposal providers only. They do not create semantic authority, project identity or canonical geometry.

## Prototype memory

A project-local learned concept contains:

- `concept_id`;
- human meaning/label;
- project id;
- positive examples;
- negative examples;
- ambiguous examples;
- embedding channels and provider versions;
- positive centroid per channel;
- negative centroid per channel when available;
- applied learning receipt ids;
- provenance references for every example.

The memory is a derived learning state. The immutable audit authority is the ordered append-only set of `LearningReceipt` records.

## LearningReceipt

Every human teaching/correction action produces a receipt.

Allowed roles:

- `POSITIVE` — confirmed example of the taught concept;
- `NEGATIVE` — confirmed counterexample / false positive;
- `AMBIGUOUS` — unresolved; retained but excluded from centroids.

A receipt must bind:

- decision id;
- concept id;
- human reviewer;
- example role;
- source version id;
- page id/index;
- evidence/region/candidate fingerprint;
- embedding fingerprint(s);
- provider id/version;
- timestamp.

No receipt grants CAD, structural or engineering authority.

## Similarity

The v1 engine performs cosine similarity per available channel.

For a channel with positive examples:

`positive_similarity = cosine(candidate, positive_centroid)`

If negative examples exist:

`negative_similarity = cosine(candidate, negative_centroid)`

The candidate score is a review aid derived from positive similarity with an explicit negative penalty. It never creates a semantic decision.

When multiple channels exist, each channel remains visible in the result. A fused ranking may be produced using governed weights, but the component scores must remain inspectable.

## Active learning loop

```text
prototype / taught example
  -> retrieve candidates
  -> human confirms group
  -> POSITIVE receipts
  -> human rejects false positives
  -> NEGATIVE receipts
  -> human marks unresolved
  -> AMBIGUOUS receipts
  -> recompute derived prototype memory
  -> retrieve again
```

The system therefore improves every time the human corrects it.

## New-project behaviour

For a project with no prior knowledge CEW must be able to say:

> I found recurring graphic groups. I do not yet know what they mean in this project.

External-reference matches and generic memories may be shown as hypotheses. The first project-local semantic assignment requires an explicit human teaching action.

## Promotion boundary

Learning does **not** imply:

- `oar_human_confirmation=true`;
- `oar_classification_confirmed=true`;
- EvidenceRegion canonicalization;
- CAD canonical write;
- structural identity;
- engineering material readiness.

All of these remain separate downstream gates.

## Provider roadmap

### v1 — implemented foundation

- structured graphic embeddings;
- project-local prototype memory;
- positive/negative/ambiguous learning receipts;
- centroid-based similarity;
- counterexample penalty;
- deterministic replay from receipts;
- explicit DINOv3 provider state `NOT_CONFIGURED`.

### v2 — visual foundation provider

- frozen DINOv3 image-region embeddings;
- embedding cache bound to immutable derived assets;
- nearest-neighbour retrieval across page/project;
- fusion with vector/structured channel.

### v3 — richer human assistance

- prompted region proposal/segmentation;
- open-set text grounding as suggestion only;
- group approval and exception-oriented active learning.

### v4 — optional trained heads

Only after a sufficiently large governed dataset exists:

- small classifier / metric-learning head over frozen embeddings;
- project-independent generic prototype promotion;
- specialized detector only when evidence volume and validation justify it.

## Authority invariant

Every automatic learning/search output carries:

```text
project_semantic_authority = NONE
canonical_write_authorized = false
structural_identity_authorized = false
engineering_authority_effect = NONE
human_project_validation_required = true
```

The original document and human-reviewed project evidence remain authoritative.