# ETW upper-floor / stair-tower photo evidence v1

## Source

- source type: user-supplied field photograph
- acquisition context: project conversation, 2026-08-19
- local evidence filename: `image-1787160252561.jpg`
- SHA-256: `c84764fcda31e2f203797dacf19ea87b1ed8496f529b8a4e29967153a198d6c5`
- raster size: `1152 x 1536 px`
- evidence class: `PHOTO_RIF_PRIMARY`
- binary archival in repository: `PENDING` (hash and observations frozen here; do not substitute another image with the same descriptive label)

## What the photograph directly supports

The photograph visibly documents, for the photographed wing/view:

1. an upper residential volume whose footprint is set back/reduced relative to the visible lower facade;
2. an exterior terrace/open setback in front of that upper volume;
3. a pitched roof over the upper residential volume, with a clearly visible eaves line and inclined roof plane;
4. a stair-tower volume rising above the principal roof plane;
5. a distinct pitched roof over the stair-tower volume;
6. a multi-height roof configuration: main upper-floor roof plus a higher stair-tower roof.

These are photo-supported geometric/topological observations. They do **not** by themselves resolve hidden structural members.

## What the photograph does NOT prove

The photograph alone does not resolve:

- exact persistent column-chain IDs;
- which exact three column positions per wing terminate;
- beam section dimensions;
- ridge/eaves beam reinforcement;
- exact ridge/eaves elevations;
- hidden column locations inside masonry;
- structural function of the visible lightweight/metal external frames;
- correspondence of this single view to all three wings.

Those properties remain `ND`, `RIF`, or `CANDIDATE` until reconciled with structural/architectural sources.

## eTwin consequences

The following constraints are strengthened:

- ordinary-floor vertical extrusion into the upper/sub-roof level is prohibited;
- the upper level is modeled as a `FloorVariant` with reduced footprint and terrace regions;
- the stair tower is a distinct upper structural/architectural volume;
- roof geometry must support multiple roof planes/elevation bands;
- ridge and eaves entities must be resolved from TAV-06S / roof evidence, not invented from the photograph;
- column absence at the upper level is compatible with the observed reduced footprint, but exact terminations remain `EXPECTED_TERMINATION_CANDIDATE` until chain binding.

## Reconciliation target

Primary documentary cross-check:

`G4 / TAV-05S (IV impalcato) -> G5 / TAV-06S (copertura)`

with architectural views used as independent geometric control where available.

Required output chain:

`PHOTO -> OBSERVATION -> roof/setback claim -> TAV-05S/TAV-06S reconciliation -> chain/beam candidate -> well-formedness decision`.
