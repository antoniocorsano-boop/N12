# CEW Professional Review + Precision Registration Baseline v1

**Status:** BASELINE_FROZEN_FOR_IMPLEMENTATION

## Mission

CEW SHALL treat professional review ergonomics and spatial precision as two independent, testable gates. A visually plausible marker is not precision evidence, and a compact panel is not sufficient if scroll ownership is ambiguous.

## Decision

The Professional Workbench evolves through two independent gates:

### UX_GATE

Required invariants:

- exactly one vertical scroll owner in the Context Rail;
- fixed/sticky WorkMode header;
- fixed/sticky primary action zone;
- no nested vertical scrolling in review-set or active-candidate surfaces;
- no full vertical lifecycle form;
- secondary fields and provenance use progressive disclosure;
- the source canvas remains stable while the rail scrolls;
- rail width and disclosure state are UI preferences only and carry no authority.

### SPATIAL_PRECISION_GATE

A global registration is only a first-order navigation model. It does not authorize a precise object locator.

Canonical precision chain:

`SOURCE PAGE → NATIVE DZI FRAME → GLOBAL REGISTRATION → STRUCTURAL_GCP → LOCAL RESIDUAL MODEL → DOCUMENT SNAP → VERIFIED_LOCATOR`

States:

- `UNLOCATED`
- `REGISTERED_GLOBAL_NEEDS_LOCAL_QA`
- `LOCALLY_CORRECTED_TO_VERIFY`
- `SNAPPED_TO_DOCUMENT_GEOMETRY`
- `HUMAN_VERIFIED_LOCATOR`

Only the final two states may be considered for professional automatic focus; `HUMAN_VERIFIED_LOCATOR` is required before a locator may be treated as verified evidence navigation.

## Structural GCP

A `STRUCTURAL_GCP` is a semantically meaningful document control point, such as a verified column centre, grid intersection or other governed feature. It SHALL contain at minimum:

- source/version/page/sheet scope;
- feature type;
- support or object reference where applicable;
- native DZI coordinates;
- common metric coordinates;
- selection method;
- validation state;
- reviewer/receipt reference when human verified.

SIFT/image-feature inliers remain evidence for global image registration but SHALL NOT be promoted automatically to `STRUCTURAL_GCP`.

## Residual diagnostics

For every candidate locator CEW SHALL be able to report:

- global predicted native x/y;
- snapped or verified native x/y when available;
- `dx`, `dy`, Euclidean residual;
- nearest structural-GCP distance;
- registration/correction method;
- locator state.

Thresholds SHALL NOT be frozen before the real residual distribution is measured. First diagnostic outputs MUST report median, P90, max and spatial pattern when sufficient verified points exist.

## Local correction policy

Preferred order:

1. global affine registration;
2. semantic structural GCPs;
3. local piecewise-affine/TIN correction when residual field demonstrates local deformation;
4. document-geometry snap;
5. explicit human verification where required.

TPS/rubber-sheet methods are exceptional and require a separate gate because they may distort structural linework between control points.

## Marker semantics

The source marker SHALL NOT communicate acceptance or rejection. Red is reserved for error/rejection semantics. Locator presentation SHOULD distinguish:

- verified locator;
- to-verify locator;
- unlocated.

The marker is a navigation aid, never structural identity and never canonical geometry.

## Authority boundaries

- global registration != verified locator;
- locator != structural identity;
- locator != canonical geometry;
- UI state != governed state;
- similarity score != position;
- visual proximity != identity;
- canonical_write_authorized = false;
- OA-6 remains blocked.

## Implementation program

- `PR-0` — Precision Diagnostics Foundation: structural-GCP schema, global-prediction register, residual fields, fail-closed states.
- `PR-1` — One Scroll Owner Workspace: remove nested vertical scrolling and create sticky header/action regions.
- `PR-2` — Structural GCP Capture: document snap + explicit GCP review/receipt.
- `PR-3` — Residual Field Analysis: median/P90/max + spatial pattern + diagnostics visualization.
- `PR-4` — Local Registration Controller: piecewise affine/TIN only when justified by residual field.
- `PR-5` — Verified Locator Review: snap, residual gate, human verification, professional focus.
- `PR-6` — Precision HVA: distributed support sample and end-to-end professional review.

## External patterns informing this baseline

- Bluebeam Revu: dockable panels, independent document views, content-based alignment/snap.
- AutoCAD: object snaps to semantically defined geometry rather than approximate clicks.
- QGIS Georeferencer: control points, residuals and transformation choice as first-class QA.
- ArcGIS Georeferencing/Adjust: global transformation plus local correction when appropriate.

These systems are references for interaction and registration patterns only; CEW authority and provenance rules remain stricter and evidence-first.
