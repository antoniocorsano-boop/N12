# CEW Document & Drawing Workspace v1 — Product Contract

Status: B1 mandatory extension  
Program: `CEW-GOAL-01`

## Purpose

Make the project documentation a first-class working environment before evidence review, reconstruction or FEM.

The user journey becomes:

`PROJECT -> DOCUMENTS -> DRAWINGS -> DRAWING VIEWER -> DOCUMENT UNDERSTANDING -> EVIDENCE -> RECONSTRUCTION -> MODEL`

This workspace exposes existing CEW source/version/page/derived/evidence primitives; it does not create a second authority.

## Product surfaces

### `/documents`
Project document library showing all available primary project information by human category: drawings, calculation reports, photos, surveys/tests, CAD/BIM and other project records when registered.

Required fields on primary surface:
- human title / source code;
- document family;
- discipline;
- level/storey/use;
- source status;
- page count when known;
- evidence count;
- open questions/reviews;
- action to open document/drawing.

### `/drawings`
Drawing register focused on graphical structural/project sheets.

For every drawing, expose:
- source code and descriptive classification;
- role and project level;
- immutable source status;
- pages;
- current viewer orientation state;
- derived reading aids;
- EvidenceRegion count;
- open review count;
- links into the drawing viewer.

### `/drawings/{source_id}`
Engineering drawing viewer.

Minimum controls:
- fit page;
- fit width;
- zoom;
- pan;
- rotate clockwise/counter-clockwise in 90° increments;
- reset orientation;
- show/hide EvidenceRegion overlays;
- open original verified PDF;
- open linked evidence;
- technical provenance/details.

Viewer rotation is display state only. It never changes SourceVersion, Page, PageTransform or EvidenceRegion authority.

## Existing governed inputs

- `tavole_originali_remote_index_v1.csv` — primary drawing register and immutable hashes;
- SourceVersion identities already bound in CEW viewer/evidence registries;
- `CEW_PAGE_REGISTRY_v1.csv` — page identity/dimensions;
- `CEW_PAGE_TRANSFORM_REGISTRY_v1.csv` — invertible coordinate transforms;
- `CEW_DERIVED_ASSET_REGISTRY_v1.csv` — derived reading aids;
- `CEW_EVIDENCE_REGION_REGISTRY_v1.csv` — governed evidence geometry;
- `CEW_SOURCE_VIEWER_BINDINGS_v1.csv` — task/source/viewer bindings.

## Intake/versioning boundary

A later slice adds new-document intake. New bytes are first `IntakeCandidate`; after hash/duplicate/classification/review they can become a new immutable `SourceVersion`. Existing N12 documents are imported by reference from their current immutable archive; they are not re-uploaded.

## Document understanding

A drawing may have a `DocumentMap` containing proposed/validated title, scale, orientation, levels, frames, sections, details, schedules, reinforcement exploded views, legends, dimensions, callouts and unresolved regions.

OCR/vector/AI outputs are candidates until the declared validation boundary is satisfied.

## Human-centred acceptance

The workspace must support at least the benchmark tasks in `automation/CEW_USABILITY_METRICS_MODEL_v1.json`.

A structural engineer without repository knowledge must be able to:
1. find TAV-05A;
2. understand what kind of drawing it is and where it belongs;
3. open it in a readable orientation;
4. distinguish original PDF from derived aids;
5. navigate to an evidence region and back to full drawing context;
6. understand what is known, what is unresolved and what is merely viewer state.

## Authority rules

- source bytes remain immutable;
- viewer orientation never changes canonical geometry;
- OCR/AI does not silently promote claims;
- derived images remain reading aids;
- a visible region does not create structural binding;
- evidence state, use state and workflow state remain distinct;
- no direct canonical write from document/drawing UI.

## B1 completion change

B1 may not be completed only because Source Hub/Evidence Workspace works. `Documents + Drawings + Drawing Viewer + Evidence` must form one usable project journey and pass the declared usability/HVA metrics.
