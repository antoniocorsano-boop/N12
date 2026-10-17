# ETW legacy terrace binding audit v1

## Verdict

The historical `model/etwin/terrace_probe.py` / `entity_binding.py` path is retained as ETW-1 provenance but is **SUPERSEDED for first-level terrace identification and binding**.

It must not be used to promote the first-level terrace, its added columns/beams, or its connection nodes.

## Why

1. `terrace_probe.py` hard-codes `TAV-05S` as source document. In the current level-sheet crosswalk this is G4 / IV impalcato, not a proved source for the physical first-level terrace.
2. `dxf_to_pdf_coords()` is explicitly described in the source as an **approximate affine transform** and uses estimated `DXF_TERRACE_BOUNDS`; it is not a persistent-identity resolver.
3. The crop manifest labels N002/N005/N039 as confirmed positions on TAV-05S, but this only proves their TAV-05S evidence chain. It does not prove membership in the first-level terrace extension.
4. Legacy N039 coordinates conflict materially with the canonical 57-node topology:
   - legacy terrace probe/entity binding: N039 ≈ `(35456, 3226)` mm;
   - `data/canonical/tav5_topology_nodes_57.csv`: N039 = `(42882.7, 19643.3)` mm.
   This conflict blocks any automatic reuse of the legacy N039 binding.
5. `entity_binding.py` contains stale terrace-specific narrative while the represented entities are TAV-05S bindings. The file is provenance, not current first-level terrace truth.

## Preserved value

The legacy artifacts remain useful as:
- proof that high-resolution TAV-05S crops can be generated reproducibly;
- TAV-05S evidence for the specific source locations stored in `evidence_crops.json`;
- provenance for ETW-1 engine validation.

They are not deleted.

## Current first-level terrace path

The current binding must follow:

`physical first-level terrace -> correct source sheet/level -> original frame node -> anchorage/interface -> added beam -> terrace node -> added column/support`

and must satisfy `FRAME_WELL_FORMEDNESS_GATE`.

## Residuals

- `ETW-TERR-R01`: exact mapping of physical "first level" to canonical G-level/source sheet remains to be closed from documentary evidence; do not infer from naming alone.
- `ETW-TERR-R02`: added terrace beam/column persistent IDs and original receiving node IDs remain unresolved.
- `ETW-TERR-R03`: legacy N039 coordinate identity conflict must be reconciled before N039 is used outside its proven TAV-05S evidence chain.
- `ETW-TERR-R04`: anchorage/monconi geometry, reinforcement quantity and development lengths remain ND until a documentary detail is bound.
