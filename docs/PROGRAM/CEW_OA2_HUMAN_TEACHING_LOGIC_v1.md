# CEW OA-2 — Human Teaching Logic v1

## Scope

OA-2 adds one bounded human action to the existing Professional Workbench:

`select object -> This is a... -> explicit type -> family label -> prototype proposal`

The proposal is project-specific, provenance-bearing and non-canonical.

## Invariants

- the selected technical object must already exist in the governed Workbench scene;
- object type is provided explicitly by the human;
- geometry may be preserved as representation but may not infer the object type;
- SourceVersion, Page and EvidenceRegion provenance are mandatory;
- the human family label is preserved without semantic compression;
- no structural identity is created;
- no canonical write is authorized;
- `Find Similar` is not available in OA-2;
- OA-3 remains blocked until OA-2 runtime integration and validation pass.

## Output

`HUMAN_TAUGHT_NON_CANONICAL_PROTOTYPE`

with:

- prototype id;
- explicit object type;
- project-specific family id/label;
- selected anchor object id;
- source evidence;
- human teaching decision;
- exact revision;
- authority flags all non-promotive.

## Current implementation boundary

The deterministic core and validation gate are implemented. Runtime Workbench interaction remains the next OA-2 sub-step. No synthetic test proposal is project evidence.
