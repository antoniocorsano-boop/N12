# M1-A reinforcement final gate audit

## Scope and decision

Work item: `M1A-REINFORCEMENT-EVIDENCE`.

Decision: `PASS_WITH_WATCH`. The reinforcement evidence inventory is complete at the currently authorized resolution and all bindings are either direct/compatible with the frozen M0-G identities or explicitly residual. This gate does not assign missing reinforcement by analogy and does not declare the calculation model ready.

## Immutable primary sources

| Source | Primary path | Git blob | SHA-256 | Use |
|---|---|---|---|---|
| TAV-01A | `archive/documentazione_originaria/tavola1-3.pdf` | `9ad6bda28495fc08379bbe4bc82b23d27145534e` | `bba85f508f31cb09b1278f317036debea2a22c0e9858bb8c4b1d4fcab855daeb` | foundation reinforcement, governed by M1-F |
| TAV-02A | `archive/documentazione_originaria/tavola 2-3.pdf` | `99eb8e6a7a19655398d783cc650ca903667a7ec4` | `fbdb88b2d6906572591c67c8724248902a817a220129cff0c2723a6828627b8a` | G1 beam reinforcement |
| TAV-034A | `archive/documentazione_originaria/tavola3a-4a.pdf` | `f50a035f585b9d622f2571542569470ead01c989` | `8f2ee5acc5df6f152d7bbb750a27a6435e3533c9548453a52e2dd69d56abc1e7` | G2/G3 beam reinforcement |
| TAV-05A | `archive/documentazione_originaria/tavola 5-3.pdf` | `111542c26192dac0a3a801eb5f2e5d5cdbffe3d3` | `17dec414f0f0505e2cd2acb519029afba7672df1793a580badb8b59b6214f325` | G4 beam reinforcement |
| TAV-06A | `archive/documentazione_originaria/tavola 6.pdf` | `c3048472adfdaa5b1e902f84c20ccfb20d679b1f` | `3f2d557fe6d3c65eb0891b1fd4f0f6f2a0a4b6cd0efe22a06604a5c341fc9c6d` | G5 roof reinforcement |
| TAV-07A | `archive/documentazione_originaria/tavola7.pdf` | `bf92501e723843fd912976b1b711285a61c548d3` | `38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b` | column-family schedules |

The latest GitHub Actions artifact `n12-analysis-cycle-report` from run `32687954937` supplied the 300 dpi renders solely for visual reading. The artifact digest is `sha256:8bc816264a2ef40ba69486c4b74913041542e56e5cc9195902e2c5b7fff54a05`; it does not replace the primary-source identities above.

## Consolidated evidence state

- `DOC`: direct source schedules, sections, diameters, quantities, explicit dimensions, group identities and compatible carpenteria bindings.
- `MIS`: none promoted by this gate.
- `RIF`: the reported 1.50 m G5 overhang length remains a downstream geometry/load watch and is not reinforcement `DOC`.
- `INF`: none promoted by this gate.
- `INC/ND`: unreadable bar labels or unlabelled diagonal dimensions, G5-B017 impluvio reinforcement, generic balcony/slab/perimeter reinforcement without a dedicated detail, and the seven unbound column rows remain explicit.

## Residuals retained

1. Column bindings: G1 supports `3,a,b,c,d`; G3 supports `9,16`.
2. Source conflicts retained without geometry changes: G2 `32`; G4 `9,16,22`; G5 source-only `24`.
3. Stair/torrino: exact 3D path and member role of the recurring `20-21` schedule and exact torrino footprint.
4. Roof: `G5-B017` reinforcement; exact occurrence/extent of gronda/cornice detail; unproven generic perimeter extension.
5. Ground-floor additions: `a-d` reinforcement and separate E03 anchorage/detail.
6. Readability: source-unlabelled diagonals, two TAV-05A UNKNOWN labels and one partial sagomato.

These residuals do not block independent M1-L load-model work. They remain binding watches before affected element checks and before `CALCULATION_MODEL_READY`.
