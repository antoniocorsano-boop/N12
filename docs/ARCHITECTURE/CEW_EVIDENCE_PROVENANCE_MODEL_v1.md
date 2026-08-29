# CEW Evidence Provenance Model v1

## Milestone

`CEW-F2 — EVIDENCE_FOUNDATION`

CEW-F2 establishes the minimum provenance chain required to move from an immutable `SourceVersion` to an exact source location and then to a literal observation, without conflating reading, interpretation, or structural binding.

## Mandatory chain

`SourceVersion -> Page -> EvidenceRegion -> Observation`

`Assertion` and `Binding` are downstream objects and are deliberately excluded from the Observation authority boundary.

## Principle: localization is evidence infrastructure

A technical reading is not reproducibly reviewable unless CEW can navigate another reviewer to the same immutable source version and the same exact region.

Existing N12 readings remain valid under their previous gate authority, but CEW migration shall not invent page numbers, bounding boxes, polygons, render transforms, or source-native coordinates to make them appear fully localized.

## Page

A `Page` identifies one page/sheet surface of one immutable SourceVersion.

Required when `READY`:
- `page_id`
- `source_version_id`
- zero-based `page_index`
- source-native width and height when known
- source-native unit or declared PDF/page coordinate convention
- page readiness state

Page identity is scoped to SourceVersion. A better scan/new SourceVersion receives new Page identities even when it depicts the same authored sheet.

## Coordinate spaces

CEW supports explicit coordinate spaces. No coordinate tuple is valid without its coordinate-space identity.

Initial spaces:

- `SOURCE_NATIVE`: page/PDF native coordinate system with declared dimensions and unit/convention.
- `NORMALIZED_0_1`: normalized page coordinates, origin and axis direction explicitly defined by the contract.
- `DERIVED_ASSET_PIXELS`: pixel coordinates belonging to a specific DerivedAsset; valid only when the asset identity and deterministic transform back to Page are recorded.

Canonical interchange recommendation for regions is `NORMALIZED_0_1`, with origin top-left, `x` increasing right and `y` increasing down. Source-native metadata and transforms are retained so viewers can reproduce the selection.

A 300-dpi render pixel bbox is not source-native provenance unless CEW stores the specific DerivedAsset identity plus an exact transform to the parent Page.

## EvidenceRegion

An `EvidenceRegion` is a reproducible geometric selection on one Page.

Initial geometries:
- `BBOX`
- `POLYGON`
- `FULL_PAGE`

For a `BBOX` in normalized coordinates:
- `x`, `y`, `width`, `height` are within `[0,1]`;
- width and height are positive;
- `x + width <= 1`;
- `y + height <= 1`.

A region may have workflow state:
- `READY`
- `NEEDS_PAGE_METADATA`
- `NEEDS_REGION_LOCALIZATION`
- `NEEDS_TRANSFORM`
- `UNRESOLVED`

These are workflow states, not `DOC/MIS/RIF/INF/ND` states.

## Observation

An `Observation` records what was literally observed or directly extracted in an EvidenceRegion.

Examples:
- text `1040` is directly readable;
- quantity and diameter are unreadable;
- an intermediate sagomato continuation is graphically visible while some dimensions are unreadable;
- an unlabelled roof reinforcement scheme is directly visible.

Observation fields include:
- `observation_id`
- `source_version_id`
- `evidence_region_id`
- `observation_type`
- literal/value payload
- optional unit
- `reading_state`
- method (`HUMAN`, `AI`, `DETERMINISTIC_EXTRACTION`, `MIGRATED_CANONICAL_EVIDENCE`)
- method/tool version where applicable
- epistemic ceiling
- provenance note

An Observation does **not** assert which structural member it belongs to. Structural binding is a separate downstream object.

## Partial and unreadable evidence

CEW must preserve incompleteness explicitly. For example:

- `length = 1040`, quantity = unreadable, diameter = unreadable;
- `length = 865`, quantity = unreadable, diameter = unreadable;
- sagomato continuation = directly visible, selected dimensions = unreadable.

The unreadable portion must not be completed by symmetry, context, homologous runs, AI confidence, or drawing-grammar analogy unless a later inference object explicitly creates an `INF` candidate within its epistemic ceiling.

## Migrating existing N12 readings

A migrated reading may enter F2 before its exact region is known, but it must be labelled `NEEDS_REGION_LOCALIZATION`. This does not downgrade the pre-existing canonical technical gate; it states that CEW's new byte-to-region provenance link is incomplete.

For F2 reference acceptance, the following four items must each receive an exact reproducible region on a READY SourceVersion:

- `T5A-G01 / G01-R06`
- `T5A-G07 / G07-R07`
- `T5A-G05 / G05-R04`
- `T6A-G03`

F2 remains `IN_PROGRESS` until all four are localized and validated.

## Derived crop rule

A crop is generated **from** an EvidenceRegion. It is never the authority object that defines the region.

If an historical crop exists without a reversible transform to an immutable Page, CEW may retain it as a migration aid but shall not promote its pixel coordinates to exact source provenance.

## Viewer handoff

CEW-F3 consumes only F2-ready Pages and EvidenceRegions for permalink/deep-zoom navigation. F3 may generate tile pyramids and enhanced views, but those derived assets cannot change the F2 observation content or authority.
