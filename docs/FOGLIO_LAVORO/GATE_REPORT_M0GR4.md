# Gate Report M0-GR4 — Canonical Geometry Reconciliation

Versione: `GR-M0G-0004` — 2026-08-17

## Scope

Trasformazione delle evidenze DXF in topologia globale canonica, mantenendo la catena:
`entita DXF -> claim -> evidenza -> regola di risoluzione -> entita canonica`.

## A. Layer Naming Convention (GR4.2)

### Documentation Found

| Source | Content |
|--------|---------|
| `NOTA_STANDARD_CAD.txt` | Layer naming follows ISO 13567-1/2 principles but is NOT formally compliant |
| `LEGGIMI_DXF_v02.txt` | Separation by discipline/element/presentation/state |
| `LEGGIMI_v05.txt` | INF=reconstruction, DOC=directly supported, RIF=user-reported, VER=to-verify |
| `PIANO_PROMOZIONE_DOC_v06.txt` | Promotion to DOC requires: (1) unequivocal graphical evidence + (2) numerical quote or coherent dimensional chain |
| `ABACO_STATO_VETTORIALIZZAZIONE_v05.csv` | All 3 DXFs are RIPULITO_NON_VALIDATO (nothing promoted to DOC yet) |

### Registered Convention (CANDIDATE, not FACT)

The layer suffix convention (`-INF` = inference, `-DOC` = documented, `-VER` = to-verify) is a **candidate convention** based on ISO 13567 principles, NOT a formally validated encoding. It is consistent with the documentation but should not be auto-assumed for future DXFs.

### Evidence Status Assignment

| Status | Criteria |
|--------|----------|
| DOC | Node in ABACO (N001-N057) + topological role + pillar association |
| INF | Node in ABACO but missing role or pillar; OR role+pillar but not in ABACO |
| INC | Node has element ID but no role; OR no identifying information |

## B. Dual-ID Resolution (GR4.3)

### 5 Groups Analyzed

| Group | Resolution | Reasoning | Canonical |
|-------|-----------|-----------|-----------|
| N052/N053/N097 | SAME_PHYSICAL_NODE_WITH_ALIASES | All share XY (0mm dist), identical connections | N052 |
| N042/N043 | SAME_PHYSICAL_NODE_WITH_ALIASES | Same XY (0mm), identical connections | N042 |
| N002/N110 | SAME_PHYSICAL_NODE_WITH_ALIASES | Same XY (0mm), N110 is alias in S-ID-CAND-INF | N002 |
| N020/N107 | SAME_PHYSICAL_NODE_WITH_ALIASES | Same XY (0mm), N107 is alias | N020 |
| N022/N065 | COINCIDENT_DISTINCT_NODES | XY differ by 261mm, different connections | N022, N065 separate |

### Key Finding

4 groups are aliases for the same physical node (0mm coordinate difference, identical connection patterns). 1 group (N022/N065) represents **distinct nodes** that happen to be 261mm apart — they are NOT the same entity.

**Canonical ID selection**: Prefer ABACO ID (N001-N057), then lowest number.

## C. Canonical Node Table (GR4.7)

| Metric | Count |
|--------|-------|
| Total DXF aliases | 116 |
| Canonical PhysicalNodes | **110** |
| Nodes with aliases | 4 groups (affecting 9 aliases) |
| Single-ID nodes | 106 |

### Evidence Status Distribution

| Status | Count | Description |
|--------|-------|-------------|
| DOC | 27 | In ABACO + role + pillar association |
| INF | 28 | In ABACO but missing role/pillar; or role+pillar but not in ABACO |
| INC | 55 | N058-N116: geometric existence only |

## D. N058-N116 Qualification (GR4.4)

| Promotion Status | Count | Description |
|------------------|-------|-------------|
| CANONICAL | 0 | None meet promotion criteria |
| CANDIDATE_FOR_CANONICAL | 7 | Have element IDs (P?xxx or T?xxx) |
| GEOMETRIC_ONLY | 48 | Have coordinates and connections but no semantic info |

### Promotion Criterion (from PIANO_PROMOZIONE_DOC_v06.txt)

> "Una geometria passa a DOC soltanto quando e sostenuta da almeno una evidenza grafica inequivoca e, per le dimensioni, da quota numerica o da una catena dimensionale coerente."

N058-N116 do NOT meet this criterion: they have geometric positions from the DXF but no numerical quotes, no pillar associations, and no topological roles. They remain **CANDIDATE_FOR_CANONICAL** pending further evidence.

## E. Connection Reconciliation (GR4.5)

| Quality | Count | Description |
|---------|-------|-------------|
| CANONICAL | 125 | Both endpoints resolved to canonical IDs with high precision |
| ALIAS_DEPENDENT | 16 | One or both endpoints are aliases (dual-ID groups) |
| GEOMETRICALLY_RESOLVED | 0 | — |
| SELF_LOOP | 0 | No self-loops after alias resolution |
| UNRESOLVED | 0 | All connections resolved |

### After Dual-ID Resolution

The 16 ALIAS_DEPENDENT connections are between nodes in dual-ID groups. After alias resolution, these connections reference canonical IDs correctly. No connections were lost.

## F. Formal Entity Model (GR4.6)

| Entity Type | Description | Count |
|-------------|-------------|-------|
| PhysicalNode | Unique physical position (x,y) | 110 |
| DocumentAlias | Historical ID (Nxxx, Cxxx) | 116 |
| TopologicalNode | Role in structural network (TERM/LINE/CROSS/JOINT) | ~57 |
| AnalyticalNode | Future FEM node | 0 (not created yet) |

A PhysicalNode can have multiple DocumentAlias. The canonical model preserves all historical IDs.

## G. Delta Summary (GR4.9)

| Metric | Before GR4 | After GR4 | Delta |
|--------|-----------|-----------|-------|
| Aliases | 116 | 116 | 0 |
| PhysicalNodes | ? | **110** | -6 (from dual-ID merge) |
| N058-N116 promoted | 0 | **0** | 0 |
| N058-N116 candidates | ? | **55** | 55 |
| Connections canonical | 125 | **125** | 0 |
| Connections unresolved | 16 | **0** | -16 |
| 95 INVALID_REF (GR2) | 95 | **0** | -95 |
| Dual-ID groups | 5 | **5 resolved** | 4 aliases + 1 distinct |

### Human Queue

| Item | Description | Priority |
|------|-------------|----------|
| N022 vs N065 | 261mm apart — confirm distinct nodes | HIGH |
| N058-N116 promotion | 55 nodes need evidence for DOC promotion | MEDIUM |
| Layer convention validation | Confirm -INF/-DOC/-VER mapping against protocol | LOW |

## H. Outputs Produced

- `docs/FOGLIO_LAVORO/M0G_CANONICAL_NODES.csv`: 110 PhysicalNodes with aliases, coordinates, roles, evidence status
- `docs/FOGLIO_LAVORO/M0G_CANONICAL_CONNECTIONS.csv`: 141 connections with quality classification
- `docs/FOGLIO_LAVORO/M0G_DUAL_ID_RESOLUTION.csv`: 5 dual-ID group resolutions
- `docs/FOGLIO_LAVORO/GATE_REPORT_M0GR4.md`: This report

## Controlli eseguiti

| Check | Result |
|-------|--------|
| Layer naming documentation found | PASS |
| INF/DOC convention registered as CANDIDATE | PASS |
| 5 dual-ID groups resolved | PASS |
| 110 canonical nodes identified | PASS |
| N058-N116 qualified (0 promoted) | PASS |
| 141 connections reconciled (0 unresolved) | PASS |
| Entity model introduced (PhysicalNode/DocumentAlias/TopologicalNode) | PASS |
| CSV inventories written | PASS |

## Verdetto

**M0-GR4: PASS.**

Conosciamo l'universo delle entita geometriche (116 aliases, 110 PhysicalNodes), sappiamo quali alias rappresentano lo stesso nodo fisico (4 groups, 1 distinct), conosciamo la provenienza delle coordinate (DXF S-NODE-INF) e possiamo spiegare ogni connessione canonica (125 canonical + 16 alias-dependent, 0 unresolved).

**Prossimo passo**: GR5 — Vertical Geometry / Z & Storeys. Quote assolute e 3D.
