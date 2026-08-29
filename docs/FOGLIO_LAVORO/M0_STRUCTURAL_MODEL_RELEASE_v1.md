# M0 STRUCTURAL MODEL RELEASE v1

## Scope

This release converts the current evidence-controlled eTwin reconstruction into an explicit analytical-model gate.

It does **not** claim that the entire building is fully verified for final structural assessment. It defines which entities may already be generated, which may be generated with explicit parameters, and which local subsystems must remain excluded until identity/support evidence is closed.

Canonical entity matrix: `docs/FOGLIO_LAVORO/M0_STRUCTURAL_ENTITY_RELEASE_v1.csv`.

## Release classes

### READY
Entity may be emitted into the analytical graph without inventing geometry, connectivity or section identity.

A `READY` entity may still depend on a global material model that is supplied separately. Material uncertainty does not erase a source-bound geometric/section identity.

### PARAMETRIC_ND
Entity existence/topology is sufficiently established for M0, but one or more properties remain `ND` or scenario-dependent.

Allowed treatment:
- emit the entity with a named parameter;
- preserve the evidence state on the parameter;
- run sensitivity envelopes where appropriate;
- prohibit promotion of the chosen parameter value to DOC/VER unless independently evidenced.

### BLOCKED_LOCAL
Entity/subsystem is not emitted into the base M0 graph because a local identity, support path, endpoint or genealogy is unresolved.

`BLOCKED_LOCAL` never blocks unrelated domains. It remains an explicit residual record.

## Base M0 generation rule

`M0_BASE = READY + PARAMETRIC_ND - BLOCKED_LOCAL`

with the following hard constraints:

1. no typical-floor extrusion;
2. no automatic P-ID <-> legacy N-ID crosswalk;
3. no automatic upper-floor column extrusion where a documented termination exists;
4. no current mansarda edge used as original 1978-80 cantilever free edge;
5. no terrace outer column, footing or anchorage invented from geometric closure;
6. no section family transferred across semantic levels without member-level evidence;
7. all generated parametric values remain tagged `PARAMETRIC_ND`, never DOC.

## Level/domain release

| Domain | M0 state | Model consequence |
|---|---|---|
| Main foundations | `READY / PARAMETRIC_ND` | Emit verified foundation topology subset; constitutive/support parameters remain separate |
| G1 ordinary frame | `PARAMETRIC_ND` | Emit only source-bound subset; no regular-floor completion |
| G1 terrace receiver | `READY` | Split original P16-P08 beam at local node J1 |
| G1 terrace projection | `PARAMETRIC_ND` | Emit 1.50 m J1-J2 member with section/support parameters |
| G1 terrace added columns/foundations | `BLOCKED_LOCAL` | Exclude until current-state/intervention evidence resolves location/base genealogy |
| G2/G3 ordinary frames | `PARAMETRIC_ND` | Preserve source-bound subsets and differential claims |
| G2->G3 P13/P20/P22/P26 verticals | `READY` | Emit four persistent vertical members |
| G4 frame / P-axis system | `PARAMETRIC_ND` | Use P-space as current analytical identity system; do not substitute legacy N-space |
| G4->upper terminations | `READY` | Nine documented termination positions; no upward extrusion |
| Upper original cantilevers WING-A/B | `PARAMETRIC_ND` | Preserve original-vs-later genealogy; symbolic/parameterized free-edge length |
| Upper WING-C cantilever transition | `BLOCKED_LOCAL` | Composite geometry remains unresolved; no manufactured member line |
| G5 roof columns | `READY` | 25/25 numbered roof-support columns emitted with documentary section |
| G5 roof beams | `READY + PARAMETRIC_ND` | 31/31 topology members emitted; 15 section-ready, 16 parameterized |
| Three ridge beams | `READY + PARAMETRIC_ND` | WING-B section-ready; WING-A/WING-C section parameters |
| Stair-tower roof subsystem | `BLOCKED_LOCAL` | Kept separate from 25-support main roof system |
| Concrete/steel/LC-FC | `PARAMETRIC_ND` | Required before assessment-grade solver results; no era-based strength inference |

## Roof release

The roof is the most mature complete local analytical subsystem:

- 25 numbered support columns: topology + section released;
- 31 beam members: topology released;
- 15 beam members: documentary 30x50 section released;
- 16 beam members: section remains parameterized;
- ridge topology:
  - WING-A `P10-P11-P12`;
  - WING-B `P13-P14-P15`;
  - WING-C `P26-P29`;
- documented eave/member systems retained as explicit frame entities;
- P21 is retained as a termination case and is not extruded into the roof support set.

## First-level terrace release

Safe analytical topology:

`P16 --3.20m-- J1 --1.45m-- P08`

with local projection:

`J1 --1.50m-- J2`

where:
- P16-P08 is original 25x70 documentary beam;
- J1 is a local analytical split node measured on the documentary span;
- J2 is a documentary geometric endpoint of the 1.50 m projection;
- J2 support/base is not resolved;
- added column/foundation/anchorage geometry remains excluded from base M0.

## Upper mansarda release

Two analytical states must remain separate:

1. `AS_DESIGNED_1978_80`: original documentary cantilever only;
2. `AS_BUILT_ALTERED_CURRENT`: original cantilever + distinct later prolongation.

For sensitivity work only, later extension may use a symbolic `L_ext >= 0`. No nominal extension length is frozen.

## Legacy v25 role

The recovered `Ariano_Irpino_DXF_strutturale_v25.zip` restores historical abaci, DXFs and TAV5<->TAV6 association artifacts.

It is an audit/recovery layer, not a blanket identity authority:
- v25 geometric associations do not automatically become documentary member identities;
- legacy N-ID is a mixed topological namespace and must not be globally equated to P-ID;
- v25 can be used as a second discriminator element-by-element.

## FEM/solver gate

M0 geometry generation is authorized under this release.

Assessment-grade solver execution remains gated by:
- explicit material parameter set;
- support/boundary-condition policy;
- load model for the selected verification case;
- parameter set for `PARAMETRIC_ND` members;
- exclusion/masking of `BLOCKED_LOCAL` subsystems.

Every solver model generated from M0 must export a machine-readable list of:
- included READY entities;
- included PARAMETRIC_ND entities and parameter values used;
- excluded BLOCKED_LOCAL entities;
- source/evidence refs for each entity.

## Release verdict

`M0_STRUCTURAL_MODEL_RELEASE = AUTHORIZED_WITH_PARAMETERS_AND_LOCAL_EXCLUSIONS`

The next implementation slice is no longer source exploration. It is generation of the first machine-readable analytical graph from `M0_STRUCTURAL_ENTITY_RELEASE_v1.csv`, followed by topology validation and solver-adapter preparation.