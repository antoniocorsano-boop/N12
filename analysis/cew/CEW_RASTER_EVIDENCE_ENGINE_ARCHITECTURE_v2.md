# CEW Raster Evidence Engine v2 — Architecture

Status: **GOVERNED IMPLEMENTATION IN PROGRESS**

Machine contract: `automation/CEW_RASTER_EVIDENCE_ENGINE_CONTRACT_v2.json`

## 1. Purpose

The raster engine is not a semantic recognizer. Its job is to produce trustworthy, source-bound graphic evidence when the preferred vector path is empty, unavailable or unsafe inside the runtime resource envelope.

The governing question is not merely **“did CEW find something?”**. The engine must be able to answer:

- what part of the page was actually observed;
- at what effective raster scale;
- through which deterministic plan;
- which raw raster signal supported each derived region;
- whether the observation was complete, partial, blank or inconclusive;
- what CEW is explicitly *not* authorized to infer.

The evidence chain is:

`PDF / Page -> RasterPlan -> Evidence Tiles -> Raw Signal -> Detection Mask -> Derived Graphic Regions -> GraphicPrimitiveCandidate -> Non-semantic Clusters -> Human Triage`

Semantic classification, structural identity, F2 writes and CAD promotion remain outside this engine.

## 2. Why v1 is insufficient

The v1 fallback scales the whole page so its longest dimension is bounded and then checks a fixed raster grid. A cell becomes a candidate only if a fixed fraction of sampled pixels is dark enough.

That design is resource-safe but weak for technical drawings because:

1. elongated pages can collapse the short dimension too far;
2. thin technical strokes can carry strong geometric meaning while occupying very little area;
3. a fixed grid is an algorithmic partition, not document geometry;
4. grid cells create weak candidate identities and poor clustering;
5. zero candidates do not distinguish a truly blank page from insufficient detector recall.

The v2 design preserves the successful process-isolation and fail-closed boundary while replacing the perceptual model.

## 3. Architectural principles

### 3.1 Observation before interpretation

Raster capture, signal detection, region construction, candidate adaptation, clustering and semantic review are separate stages.

A detection mask may be morphologically expanded for continuity, but declared candidate geometry must remain traceable to original raster/page coordinates.

### 3.2 Tiled full-page coverage

The engine must not depend on a single globally reduced bitmap. It builds a deterministic `RasterPlan` and processes page clips sequentially.

Each tile records:

- page index;
- clip bbox in page coordinates;
- normalized bbox;
- scale;
- raster dimensions;
- tile sequence and deterministic tile id;
- overlap geometry;
- observation status.

Only one bounded tile bitmap is required in memory at a time.

### 3.3 Geometry-aware scale

The plan derives scale from page geometry and budget. Elongated pages are tiled instead of globally compressed. Any scale degradation caused by a tile-count or time budget is recorded explicitly.

### 3.4 Thin-line preservation

Signal detection must not rely on a single area-density threshold. It must preserve long horizontal and vertical runs even when dark-pixel ratio is low.

The minimum detector signals are:

- local estimated background;
- threshold actually used;
- raster signal occupancy;
- connected/continuous signal spans;
- local density;
- boundary contact.

### 3.5 Non-semantic regions

The engine emits geometric regions such as line-like, dense, complex or unknown graphic regions. It does not emit labels such as beam, column, wall, dimension or reinforcement.

### 3.6 Cross-tile reconciliation

Overlap exists to prevent a page object from becoming multiple candidates only because it crossed a tile boundary. Reconciliation is deterministic and based on page coordinates, neighboring tiles and compatible geometric families.

### 3.7 Measurable coverage

For every page CEW reports:

- planned area;
- processed area;
- coverage ratio;
- tiles planned;
- tiles completed;
- tiles failed;
- effective raster scale;
- scale degradation state.

`READY` is forbidden when required observation coverage is incomplete.

## 4. Epistemic terminal states

### READY

The required observation completed and the result is evidentially sufficient. This can mean graphic regions were found, or a blank page was positively demonstrated after complete observation.

### INCONCLUSIVE

The page was observed wholly or partly, but CEW cannot derive reliable graphic candidates. Typical example: raster signal is demonstrably present but region extraction yields zero reliable candidates.

An inconclusive result is not a parser failure and must remain inspectable by a human.

### FAILED

Acquisition or analysis could not complete inside the governed runtime envelope.

This separation prevents “zero candidates” from masquerading either as success or as proof of a blank page.

## 5. Blank-page rule

A blank page is a positive observation state, not the absence of detector output.

`PAGE_BLANK_OBSERVED` is allowed only when:

- required coverage is complete;
- no tile failed;
- no significant raster signal was observed;
- no contradictory page evidence exists.

If signal exists but candidates do not, the result is `INCONCLUSIVE_RASTER_DETECTION`.

## 6. Deterministic identity and provenance

Every derived candidate must preserve:

- source SHA-256;
- SourceVersion identity;
- page index;
- normalized page bbox;
- raster plan id;
- supporting tile ids;
- detector version;
- signal metrics;
- aggregation method;
- semantic authority `NONE`.

Candidate identity is derived from source/page geometry and governed detector configuration, never from transient tile processing order.

Repeated execution over the same PDF, engine version and plan must reproduce candidate ids and report fingerprint.

## 7. Trust surface

The user interface must show factual evidence rather than a generic confidence percentage.

For a page it should expose, at minimum:

- acquisition mode: VECTOR / RASTER_FALLBACK / RASTER_TILED;
- coverage percentage;
- tiles completed / planned;
- effective raster scale;
- signal state: PRESENT / ABSENT / INCONCLUSIVE;
- number of derived regions and clusters;
- automatic semantic labels: NONE;
- SourceVersion/Page governance state;
- training state;
- canonical-write state.

The page must remain visible for both `READY` and `INCONCLUSIVE` evidence sessions.

## 8. Runtime and dependency boundary

The engine remains inside the existing process-isolated preview worker. The web process owns transient job/session state and must remain healthy if the worker exits, times out or reaches its memory ceiling.

The v2 foundation requires no OpenCV, OCR package or ML model. PyMuPDF and standard-library logic are sufficient for the governed raster evidence layer. Learned visual features remain a later and separate layer.

## 9. Quality invariants

The machine contract defines ten binding invariants:

1. full observation before READY;
2. no silent empty success;
3. blank must be demonstrated;
4. bounded memory/time/tile processing;
5. web-process survival;
6. deterministic replay;
7. source/page reconstructibility;
8. zero semantic authority;
9. human-visible uncertainty;
10. no hidden fallback.

## 10. Regression corpus

The permanent regression corpus must include synthetic deterministic pages for:

- true blank;
- one very thin horizontal line;
- one very thin vertical line;
- thin-line grid;
- rectangles;
- dense/hatch-like regions;
- extremely tall page;
- extremely wide page;
- low-contrast raster-like content;
- content crossing tile boundaries;
- content only near page edges;
- mixed text and graphics.

The real `tavola 6.pdf` HVA is a required acceptance case but must not be the only regression evidence.

## 11. Tavola 6 acceptance

For the current HVA, the target outcome is not merely an HTTP success. The evidence must show:

- no 502;
- no web-process restart;
- 100% required page coverage;
- zero failed tiles;
- raster signal detected;
- one or more non-semantic graphic regions;
- one or more clusters;
- page visible to the human reviewer;
- no automatic semantic labels;
- training still blocked for unregistered preview;
- canonical write still blocked.

Only after that evidence exists can the raster discovery layer be considered trustworthy enough to support human teaching and similarity search.

## 12. Implementation sequence

The implementation sequence is binding:

1. canonical machine contract;
2. deterministic RasterPlan;
3. tiled page capture;
4. adaptive local signal detection;
5. region aggregation;
6. cross-tile reconciliation;
7. candidate adaptation with provenance;
8. quality gate including `INCONCLUSIVE`;
9. evidence-only session for inconclusive results;
10. trust indicators in the Workbench;
11. synthetic regression corpus;
12. controlled `tavola 6.pdf` HVA.

The governing CEW rule remains: **reliable evidence first, learning second, structural identity later**.
