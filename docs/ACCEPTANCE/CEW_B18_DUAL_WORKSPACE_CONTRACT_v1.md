# CEW B1.8 — Dual Workspace Contract v1

**Status:** `IMPLEMENTED_CANDIDATE_HVA_PENDING`  
**Scope:** CEW B1 human-centred document/evidence work  
**Baseline observed before implementation:** `44ac390ec221f2426ea518f37b9e803f6691e75a`  
**Authority effect:** `NONE`  
**Canonical write:** `false`

## 1. Purpose

B1.8 introduces a professional comparison workspace with two coordinated surfaces:

1. **Source Panel** — verified primary source / reproducible EvidenceRegion.
2. **Technical Representation Panel** — read-only projection of CEW records already persisted and traceable to that source.

The purpose is to let a professional compare source and technical reading without confusing a derived representation with source authority or structural identity.

This contract does **not** authorize a reconstructed structural drawing when the repository does not contain traceable structural geometry for the selected evidence.

## 2. Governing rule

Every object shown as technical information must have a reproducible chain:

`dato → registro/fonte → rappresentazione`

For the first real case (`ERW-N12-001`) the supported chain is:

`TAV-05A / SourceVersion → Page → PageTransform → EvidenceRegion G01-R06 → Observation G01-R06-LENGTH → Technical Panel`

Current documented literal:

`length=1040; quantity=UNREADABLE; diameter=UNREADABLE`

Therefore:

- length `1040` may be displayed as documented reading;
- quantity remains `OPEN/ND`;
- diameter remains `OPEN/ND`;
- no quantity or diameter may be completed by analogy;
- no beam/member identity is asserted by the EvidenceRegion;
- no structural geometry is generated from page coordinates.

## 3. Source Panel contract

The Source Panel may expose:

- verified immutable PDF;
- full drawing view;
- verified EvidenceRegion view;
- existing CEW zoom/pan/scale controls;
- navigation between local evidence and full source context.

The primary PDF remains the source authority. Renders and crops are reading aids only.

## 4. Technical Representation Panel contract

The Technical Panel may expose only persisted, traceable information, including:

- Observation literal/value;
- reading state;
- epistemic ceiling;
- source/page/transform/EvidenceRegion identifiers;
- DocumentMap state and unknown fields;
- explicit binding state;
- explicit uncertainty state.

The normalized EvidenceRegion may be drawn on a page-shaped map only as **document geometry**. It must be labeled as not being structural/model geometry.

### 4.1 Current structural geometry state

For the initial dual-workspace case:

`OPEN/ND — NO_TRACEABLE_STRUCTURAL_GEOMETRY_BOUND_TO_THIS_EVIDENCE_REGION`

Accordingly the implementation must not invent:

- beams;
- columns;
- grid axes;
- spans;
- node coordinates;
- member geometry;
- dimensions not present in the governed chain.

## 5. Geometry and identity boundary

Invariant:

`geometry != identity`

A page BBOX identifies a region of documentary evidence. It does not identify a structural member merely because the region is near, resembles or could correspond to a member in another representation.

A future structural geometry may be added to the Technical Panel only when it has its own persisted provenance and an explicit governed relation to the evidence object.

## 6. Proposal editing boundary

Recognized/technical text may be edited only as a **proposal**.

The B1.8 implementation stores proposal text in browser `sessionStorage` only and declares:

- `proposal_only = true`
- `canonical_write = false`
- `engineering_authority_effect = NONE`

A proposal must not modify Observation, Claim, Entity, Decision, EvidenceRegion or any canonical register.

## 7. Uncertainty taxonomy

The dual workspace supports these proposal/work states:

- `OPEN`
- `IN_REVIEW`
- `RESOLVED`
- `NOT_RESOLVABLE_FROM_CURRENT_SOURCES`

These states must remain explicit. `ND`, `UNREADABLE`, missing dimensions or unbound relations must not be silently converted to documented facts.

## 8. Source ↔ technical synchronization

The initial implementation supports a provenance-safe round trip:

- select **Regione verificata** → Source Panel opens the Evidence Workspace for the bound task;
- select **Tavola completa** → Source Panel opens the full drawing viewer for the same registered source;
- Technical Panel keeps the exact SourceVersion/Page/Transform/EvidenceRegion/Observation chain visible.

A future object-level synchronized highlight is allowed only when both sides have a governed explicit relation. Visual coincidence alone is insufficient.

## 9. Fail-closed behavior

The workspace must fail closed when:

- the task binding is absent;
- Page/Transform/EvidenceRegion provenance is incomplete;
- a required provenance object is not READY;
- no Observation is registered;
- a structural binding is absent or unresolved.

Fail-closed means showing `OPEN/ND` or an unavailable state. It never means inventing a fallback geometry or technical value.

## 10. HVA task

The supplemental HVA contract is:

`automation/CEW_B18_DUAL_WORKSPACE_HVA_CONTRACT_v1.json`

The real professional task is to compare the verified source region with the technical reading, recognize what is documented versus unresolved, and create or decline a proposal without crossing the authority boundary.

Blocking HVA failures include:

- source/derived authority confusion;
- EvidenceRegion geometry read as structural identity;
- silent completion of ND/unreadable values;
- proposal interpreted as canonical write;
- provenance chain not reachable;
- false success.

Automated checks validate only implementation invariants. They do **not** satisfy the human HVA or manual accessibility gates.

## 11. Non-scope

This tranche does not:

- promote any N12 engineering datum;
- mutate `data/canonical/*`;
- authorize CEW Level C or equivalent professional approval;
- implement eTwin A1;
- define a new platform ontology;
- create Architecture entities;
- merge the B1.8 branch.

## 12. Future extension rule

A structural/ISO representation may replace the current documentary projection only when its objects can independently satisfy:

`object → structural geometry/model record → source/evidence relationship → provenance → authority state`

Until then, `OPEN/ND` is the correct state and is part of the product behavior, not a missing UI decoration.
