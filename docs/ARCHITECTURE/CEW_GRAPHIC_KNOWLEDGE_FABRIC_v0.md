# CEW Graphic Knowledge Fabric v0

Status: EXPERIMENTAL SYSTEM CAPABILITY
Pilot producer: N12 / TAV07
Canonical promotion: DISABLED

## 1. Decision

Graphic-symbol knowledge is a CEW system capability, not a property of one project.

N12 is a pilot that contributes evidence and project-specific decisions. Its labels must be reusable by other projects only through an explicit transfer model that preserves provenance, scope, counterexamples and human authority.

The system therefore separates:

1. **Project knowledge** — what was actually validated in one project.
2. **Family knowledge** — recurring conventions supported across sufficiently affine projects/documents.
3. **Global knowledge** — conventions shown to transfer across multiple families.

A project may specialize or contradict shared knowledge without rewriting it.

## 2. Generalize -> retrieve by affinity -> combine -> specialize

The operational cycle is:

`Project evidence -> reviewed examples -> family/global generalization proposal -> human validation -> shared knowledge pack`

and for a new project:

`Project context -> affinity resolver -> global + family + local evidence ensemble -> ranked candidate meanings -> project human validation -> local specialization`

Shared knowledge produces priors and candidates. It never becomes project truth by import alone.

## 3. Context profile

Transferability is evaluated from explicit metadata rather than geometric similarity alone.

Initial affinity dimensions:

- discipline;
- document family;
- drawing type;
- structural system;
- drafting era;
- authoring office / designer family;
- notation family;
- country / technical tradition;
- language;
- source modality.

The resolver weights highly discriminating dimensions more strongly, especially drawing type, authoring office and notation family.

Unknown metadata lowers transfer confidence instead of being silently treated as a match.

## 4. Knowledge unit

Every reusable example preserves at least:

- project namespace;
- source SHA-256;
- stable candidate fingerprint (`GCFP-*`);
- native region identity through the producing project;
- proposed/validated meaning;
- verdict `POSITIVE | NEGATIVE | UNCERTAIN`;
- context profile;
- human reviewer;
- review timestamp.

No source file path is required in a portable shared pack.

## 5. Combination policy

A candidate meaning may receive support from several layers simultaneously:

- **LOCAL**: examples from the current project; highest specialization weight.
- **AFFINE**: examples from other projects, weighted by context affinity.
- **FAMILY**: human-validated family generalizations, weighted by profile affinity.
- **GLOBAL**: human-validated cross-family knowledge, used as a broad prior.

Positive and negative evidence are both accumulated. `UNCERTAIN` reduces certainty without being converted to a negative label.

Conflicting local/shared knowledge produces an explicit conflict; it is not resolved by hidden precedence.

## 6. Generalization gates

### Project -> Family

A family proposal requires, at minimum:

- human-reviewed positive examples;
- support from at least two distinct projects;
- compatible family context;
- no unresolved material counterevidence.

### Family -> Global

A global proposal requires, at minimum:

- support from at least three distinct projects;
- support across at least two distinct family signatures;
- explicit human validation of the generalization.

Thresholds are policy and may evolve without changing the knowledge contract.

## 7. Import trust boundary

A knowledge pack exported by one CEW installation is portable and content-fingerprinted.

When imported elsewhere, shared generalizations enter as **`IMPORTED_SUPPORTED`**, not as locally `HUMAN_VALIDATED` knowledge. A local human or trusted governance policy must promote them before they acquire the full local shared-knowledge weight.

This allows knowledge exchange between repositories, organizations or future CEW services without creating a silent authority channel.

## 8. Specialization rule

A project-specific decision is an overlay. It never edits the shared rule.

Example:

- GLOBAL: a graphic pattern often denotes a column marker;
- FAMILY A: in 1970s reinforced-concrete structural drawings by office X it strongly denotes a column marker;
- PROJECT N12: a particular occurrence is validated as a title-block rectangle, therefore `NEGATIVE` for `COLUMN_MARKER` locally.

The N12 counterexample improves future transfer and remains available for family/global recalibration.

## 9. System boundary

The reusable CEW capability is `knowledge.graphic_conventions`.

`document.symbol_learning` remains responsible for producing project-bound training examples from source observations.

`knowledge.graphic_conventions` is responsible for:

- cross-project storage;
- affinity scoring;
- ensemble resolution;
- family/global generalization proposals;
- portable knowledge packs;
- specialization overlays;
- conflict exposure.

`human.review` remains the authority for semantic validation.

## 10. Pilot use

N12/TAV07 is the first producer, not the namespace of the system.

The current TAV07 review package can contribute examples after human labeling. Before those labels exist, the system is allowed to return `NO_TRANSFERABLE_MEANING` or low-confidence candidates; it must not bootstrap its own truth from detector output.
