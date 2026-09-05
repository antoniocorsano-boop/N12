# CEW Professional Evidence Workbench — Technical Projection Model v1

**Status:** `DESIGN_BASELINE_PROPOSED`  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Purpose

Define the derived scene model that turns verified document geometry, recognition outputs and already-governed structural records into a professional technical representation without creating a parallel engineering authority.

Invariant:

`document geometry != technical candidate != structural identity`

## 2. Coordinate spaces

Every geometry object declares one coordinate space:

- `SOURCE_PAGE_PT` — PDF/page points;
- `SOURCE_NORMALIZED_0_1` — normalized page coordinates;
- `TECHNICAL_2D` — workbench technical drawing coordinates;
- `STRUCTURAL_MODEL_XY` — governed structural/model coordinates projected to 2D;
- `VIEWPORT_PX` — transient display coordinates, never persisted as engineering geometry.

Implicit conversion is forbidden. Every cross-space conversion references a `RegistrationTransform` or deterministic PageTransform.

## 3. Core object families

### DocumentGraphicPrimitive
Derived directly from source extraction.

Required fields:

- `object_id`
- `source_version_id`
- `page_id`
- `primitive_type` (`LINE`, `POLYLINE`, `ARC`, `RECT`, `PATH`, etc.)
- `geometry`
- `coordinate_space`
- `extractor_evidence[]`
- `agreement_state`
- `authority_state=DERIVED_DOCUMENT_GEOMETRY`

### RecognizedText

- `object_id`
- source/page/bbox;
- literal text;
- normalized candidate text if available;
- extractor/OCR origin;
- confidence/evidence state;
- linked EvidenceRegions;
- validation state.

### RecognizedDimension

- graphic/text anchors;
- literal value;
- parsed numeric candidate when safe;
- unit candidate;
- witness/extension geometry when recognized;
- validation state;
- no structural meaning implied.

### TechnicalObjectCandidate

Candidate semantic grouping over primitives/text.

Examples:

- `GRID_AXIS_CANDIDATE`
- `BEAM_CANDIDATE`
- `COLUMN_CANDIDATE`
- `REINFORCEMENT_CANDIDATE`
- `SECTION_LABEL_CANDIDATE`

Required:

- member primitives;
- candidate properties;
- evidence links;
- recognition rationale/origin;
- candidate state;
- no canonical identity unless separately linked.

### GovernedStructuralObjectProjection
Read-only projection of an existing governed M0G/CEW object.

Required:

- existing canonical/governed id;
- source authority state;
- model geometry reference;
- evidence/binding links;
- projection geometry;
- projection is never a clone/new identity.

### EvidenceLink
Explicit relation between source evidence and a scene object.

Types:

- `SUPPORTS`
- `DERIVED_FROM`
- `CANDIDATE_CORRESPONDENCE`
- `GOVERNED_BINDING`
- `CONFLICTS_WITH`

Each link declares its authority/state. Visual proximity cannot create a link.

### WorkingEdit
Non-canonical edit bound to one object/property.

Required:

- `working_edit_id`
- target object/property;
- base value/revision;
- proposed value;
- author/session;
- reason/comment where applicable;
- timestamp;
- state (`DRAFT`, `READY_FOR_REVIEW`, `WITHDRAWN`, `HANDED_OFF`);
- `canonical_write=false`.

### ReadingIssue
Graphically anchored unresolved question.

Required:

- issue id;
- anchor object/geometry/evidence;
- question/type;
- unresolved fields;
- alternatives;
- state;
- working resolution;
- evidence links;
- review/handoff state.

### RegistrationTransform
Explicit mapping between coordinate spaces.

Required:

- transform id/version;
- `from_space`, `to_space`;
- transform type;
- control correspondences;
- parameters/matrix;
- residual/error metrics;
- origin/method;
- verification actor/process;
- state;
- source/scene revisions.

## 4. Registration transform types

Initial supported types:

- `IDENTITY_PAGE` — same Page coordinate basis;
- `AFFINE_2D` — scale/rotation/translation/shear from sufficient governed correspondences;
- `HOMOGRAPHY_2D` — only when explicitly required and verified for planar distortion.

No freehand visual alignment may silently become VERIFIED.

States:

- `UNAVAILABLE`
- `PROPOSED`
- `VERIFIED`
- `REJECTED`
- `STALE`

Verification criteria/tolerances must be separately versioned and based on source class; this model does not invent universal numeric thresholds.

## 5. Dual-vector reuse adapter

PyMuPDF and Docling Parse are upstream evidence producers.

Their `AGREE/PARTIAL/DISAGREE` result feeds primitive state:

- agreement may support `EXTRACTED_AGREED`;
- partial/disagreement remains visible as extraction uncertainty;
- disagreement cannot be resolved by silently preferring one extractor;
- extractor output cannot promote DOC/MIS or structural geometry.

The workbench adapter normalizes output; it does not replace the agreement gate.

## 6. F6 structural-scene reuse adapter

Existing M0G member/node records are projected as `GovernedStructuralObjectProjection` only when their identifiers and authority states are preserved.

The F6 semantic evidence↔member link is represented as `EvidenceLink`, not as a spatial registration.

`UNBOUND` remains `UNBOUND` even if a candidate-comparison context is displayable.

## 7. Layer composition

Technical scene layers consume object families:

- `DOCUMENT_LINEWORK` → DocumentGraphicPrimitive;
- `RECOGNIZED_TEXT` → RecognizedText;
- `DIMENSIONS` → RecognizedDimension;
- `TECHNICAL_CANDIDATES` → TechnicalObjectCandidate;
- `STRUCTURAL_GOVERNED` → GovernedStructuralObjectProjection;
- `ISSUES` → ReadingIssue;
- `WORKING_EDITS` → visual deltas/annotations;
- `VALIDATION_STATE` → overlays/badges, not duplicate objects.

## 8. Object identity rules

Workbench object ids are stable within their derived scene revision, but are not engineering identities.

A TechnicalObjectCandidate may later link to a governed structural object only through an explicit governed relation.

Never derive identity from:

- nearest geometry;
- same colour/shape;
- page proximity;
- similar label alone;
- automatic registration alone.

## 9. Editing semantics

Recognized text/value edits create WorkingEdit deltas.

The base recognized/source literal remains immutable.

The technical viewport may render the proposed value in place, clearly marked as working state. Provenance inspector can always show base and proposal.

Undo/redo changes WorkingEdits, not source/canonical records.

## 10. ReadingIssue resolution semantics

`RESOLVED` means the workbench issue has a reviewed resolution/handoff according to its workflow; it does not by itself mean a canonical engineering assertion was promoted.

If current sources cannot support a reading, the correct terminal working state may be `NOT_RESOLVABLE_FROM_CURRENT_SOURCES`.

## 11. Serialization boundary

The client consumes/produces versioned workbench scene/proposal documents. Suggested logical envelopes:

- `TechnicalSceneManifest`
- `WorkbenchSceneChunk`
- `WorkingSessionPatch`
- `ReadingIssueSet`

All envelopes include project/scope/source/scene revision and authority flags.

## 12. Acceptance criteria

The model is correctly implemented only when tests prove:

- every object has declared coordinate space and provenance;
- dual-vector disagreement cannot become authoritative geometry;
- candidate and governed structural identities are distinct;
- F6 links do not masquerade as spatial registration;
- WorkingEdit preserves base value and is non-canonical;
- ReadingIssue is object/geometry anchored;
- only VERIFIED RegistrationTransform enables spatial sync/overlay;
- stale source/scene revision invalidates registration/working attachment fail-closed.
