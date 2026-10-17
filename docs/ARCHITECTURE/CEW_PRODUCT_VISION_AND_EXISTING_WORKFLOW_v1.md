# CEW Product Vision and Civil Existing Workflow Architecture v1

Status: CANONICAL PRODUCT DIRECTION
Date: 2026-08-24
Reference implementation: N12

## 1. Product identity

**CEW — Civil Engineering Workflow** is the product family.

CEW is conceived as an engineering workflow platform whose core responsibility is not a single solver, CAD editor or document reader, but the controlled transformation of heterogeneous engineering evidence into traceable canonical models, alternative assessment scenarios, solver inputs, decisions and subsequent model generations.

**Civil Existing Workflow (CEW-EX)** is the CEW vertical dedicated to existing structures, particularly projects where the available knowledge may derive from aged drawings, historical calculation reports, photographs, partial surveys, inspections, tests and later modifications.

N12 is the first reference implementation and validation project. N12-specific counts, identities and evidence remain project data and are never extraction targets for future CEW projects.

## 2. Core product principle

CEW must keep separate:

1. what the source explicitly documents;
2. what is measured or observed;
3. what is inferred under an admitted rule;
4. what is model-derived;
5. what is updated statistically from evidence;
6. what remains unknown;
7. what is changed by an intervention.

A canonical model may be incomplete. Missing information must be represented explicitly rather than completed silently.

The stable epistemic vocabulary remains `DOC / MIS / RIF / INF / INC / ND`, extended in scenario space by:

- `MOD`: model-derived, not a measurement;
- `POST`: posterior/model state updated by measurements or inspections.

`MOD` and `POST` never become `MIS` merely because they are numerically precise.

## 3. CEW system map

```text
                     CEW
           Civil Engineering Workflow
                        |
        +---------------+----------------+
        |                                |
      CEW Core                       Technical verticals
        |                                |
        |                        +-------+-------+
        |                        |               |
 Evidence / Claims          Civil Existing   future domains
 Provenance / Lineage       Workflow         new structures
 Residuals / Conflicts          |             bridges
 Orchestration / Gates          |             geotechnics
 Human Validation               |             monitoring
 Model Registry                 |
        |                       |
        +-----------+-----------+
                    |
          Canonical Engineering Model
```

The CEW Core owns source identity, claim identity, provenance, conflicts, residuals, generations, audit receipts, human decisions and canonical model serialization.

CEW-EX adds existing-structure semantics: historical baseline, as-built reconstruction, current condition, degradation, inspections/tests, knowledge level, confidence, repair/strengthening and post-intervention generations.

## 4. CEW-EX workflow

```text
DOCUMENTS / PHOTOS / SURVEYS / TESTS
                 |
                 v
         Evidence Reconstruction
                 |
                 v
       Canonical Structural Model
                 |
        +--------+---------+
        |                  |
        v                  v
  3D Model Builder    Knowledge Model
        |                  |
        +--------+---------+
                 v
       Existing Assessment Engine
                 |
     +-----------+-------------+
     |           |             |
 Historical  Conservative  Probabilistic
                 |
                 v
        Investigation Planner
                 |
          Value of Information
                 |
                 v
           selected tests
                 |
                 v
          Bayesian updating
                 |
                 v
            Solver adapters
        EdiLus / FEM / others
                 |
                 v
        Structural Assessment
                 |
                 v
 Repair / Strengthening Design
                 |
                 v
        New model generation
```

## 5. Canonical Structural Model

The 3D model is not a rendered picture and is not a solver file. It is a solver-independent structural graph composed of separate layers:

- identity graph;
- geometric kernel;
- structural topology graph;
- property graph;
- evidence lineage;
- scenario overlays.

The canonical structural graph must support stable IDs, explicit node/member connectivity, rigid offsets, incomplete/symbolic coordinates, property bindings and source lineage.

Connectivity may never be created from geometric proximity alone.

### N12 current reference

The current M0-G B055 handoff contains:

- 629 analytical superstructure nodes;
- 165 support-core nodes;
- 464 beam-face nodes;
- 464 rigid offsets;
- 359 ordinary members;
- 38 foundation supports;
- 55 FPEP/P07 primary foundation members.

Foundation XY is available to the solver shell through an explicit modeling rule and retains its underlying evidence state. Numeric foundation Z is still unresolved and remains the symbolic common plane `ZF_COMMON`.

## 6. Structural Viewer

The viewer is a query interface over the canonical model, not its authority.

The viewer must allow the engineer to:

- navigate the structural graph in 3D;
- select members, supports and nodes;
- filter by storey and entity type;
- distinguish ordinary members, rigid offsets and foundations;
- color by epistemic state;
- inspect source references and residuals;
- switch between base model and assessment overlays;
- preserve entity identity while scenarios change properties;
- expose ND/INC instead of hiding them.

A selected element should eventually expose a panel such as:

```text
P22 · G2-G3
Geometry        DOC
Position XY     MIS
Section         DOC 40x50
Concrete        historical DOC
Current fc      ND
Reinforcement   DOC / WATCH
Degradation     MOD-P50
Calculation     not yet eligible
```

The first viewer release may render only the canonical graph and provenance states. Materials, degradation, results and intervention overlays are layered later.

## 7. Multi-Mode Existing Assessment

CEW-EX uses one canonical identity/topology model and multiple explicitly separated assessment modes:

- MODE-1 HISTORICAL_BASELINE — the documented historical design/reference state;
- MODE-2 CONSERVATIVE_EXISTING — current-condition screening with admitted conservative assumptions;
- MODE-3 PROBABILISTIC_DEGRADATION — distributions/scenarios for deterioration and uncertain current properties;
- MODE-4 ESSENTIAL_TESTS_UPDATED — probabilistic priors updated by a small high-value investigation set;
- MODE-5 SURVEYED_EXISTING — current model primarily driven by sufficient direct survey/test evidence.

The existence of MODE-2/3/4 never promotes the regulatory knowledge level automatically. LC/FC remains a separately governed assessment fact.

## 8. Degradation Engine

The degradation engine operates above the immutable canonical model and below solver adapters.

Conceptual chain:

```text
PRIMARY EVIDENCE
      |
      v
AS-BUILT MODEL
      |
      v
EXPOSURE MODEL
      |
      v
DEGRADATION MODEL
      |
      v
STATE SAMPLER
      |
      v
STRUCTURAL PROPERTY ADAPTER
      |
      v
SOLVER
      |
      v
RESPONSE / RELIABILITY / SENSITIVITY
```

Candidate model families include carbonation, chloride ingress where relevant, corrosion initiation/propagation, reinforcement section loss, cover cracking/spalling and bond degradation.

Models are registry-controlled and cannot be used for decision-grade execution until their mathematical form, parameter sources, calibration domain, uncertainty model and validation status are registered.

## 9. Investigation Planner

The objective is not to prescribe the maximum number of tests. It is to determine which investigation most reduces decision-relevant uncertainty.

Target cycle:

```text
uncertain parameters
      -> structural sensitivity
      -> decision sensitivity
      -> candidate investigations
      -> expected information gain / Value of Information
      -> minimum useful investigation plan
      -> observations/tests
      -> posterior update
      -> reassessment
```

This creates three valid project strategies within one workflow:

1. diffuse investigations;
2. essential high-information investigations;
3. comparison/sensitivity models where new investigations are unavailable.

The third strategy is a robustness/comparison mode, not a claim that simulated values are measured facts.

## 10. Structural assessment and intervention generations

CEW-EX continues beyond a PASS/FAIL assessment.

```text
AS-IS
  -> deficiencies
  -> intervention objectives
  -> alternatives
     - repair
     - local strengthening
     - global strengthening
     - durability/protection
  -> new model generation
  -> analysis
  -> comparison
  -> design
  -> execution
  -> post-intervention as-built
  -> monitoring
```

A structural element retains its identity across generations. Its geometry, properties, damage state and intervention state may change through controlled generations, for example:

- GEN-0 historical design;
- GEN-1 reconstructed existing;
- GEN-2 surveyed existing;
- GEN-3 proposed intervention;
- GEN-4 executed intervention;
- GEN-5 monitored structure.

## 11. Solver adapters

Solver files are projections of the canonical engineering model, never the canonical authority.

Each adapter must provide round-trip identity mapping so that solver outputs can be traced back to CEW entities.

Initial targets:

- EdiLus-EE implementation checklist / mapping;
- independent open-source FEM adapter;
- future adapters without changing canonical identity or epistemic semantics.

## 12. Product development order

The product should evolve in this order:

1. evidence/claim/provenance core;
2. canonical 3D structural model builder;
3. structural viewer/query interface;
4. property and reinforcement overlays;
5. multi-mode assessment engine;
6. degradation/exposure registry and calibrated models;
7. investigation planner / Value of Information;
8. solver adapters and result round-trip;
9. intervention generations;
10. post-intervention/monitoring lifecycle.

Several components already exist in the N12 reference implementation: evidence gates, orchestration/receipts, FPEP, M0-G, foundation primary geometry, Multi-Mode Existing Assessment Engine v1 and the 3D Structural Model Builder v0.

## 13. Product safety invariants

- canonical evidence is immutable except through controlled supersession;
- model precision never upgrades evidence precision;
- missing data remains visible;
- no nearest-neighbour or analogy fill unless an explicit admitted modeling rule authorizes a scenario value;
- topology changes create a new canonical generation;
- intervention changes create a new generation;
- historical, current, simulated and post-intervention states remain distinct;
- solver output cannot silently rewrite source evidence;
- a visually complete model is not necessarily calculation-ready;
- human engineering approval remains required at promotion gates.

## 14. Immediate implementation boundary

The current development boundary is the **CEW Structural Viewer v0** built on the already validated canonical structural graph. It must make the N12 graph visible and queryable without adding engineering claims. After that, the next reusable product slices are the evidence panel, scenario overlay interface and Investigation Planner.
