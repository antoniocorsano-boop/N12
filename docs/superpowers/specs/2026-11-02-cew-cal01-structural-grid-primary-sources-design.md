# CEW-CAL-01 — Structural Grid Primary Sources Design

## Objective

Extend CEW-CAL-01 from TAV.5-local evidence to the primary structural-grid sources that actually document the building metric mesh:

1. `TAV-01S` — `archive/documentazione_originaria/tavola1-2.pdf` — foundations / structural carpentry.
2. `TAV-02S` — `archive/documentazione_originaria/tavola2-2.pdf` — first-floor structural carpentry.

The goal is to discover replayable external dimension-chain candidates for column grid spacing, fixed lines, spans and overall structural-grid dimensions, without using historical geometry as fit authority.

## Frozen primary sources

Repository: `antoniocorsano-boop/N12`

Frozen source commit: `78c20a52db4f391ce0d13b9705b9f04737e218c9`

| Source ID | Path | Functional role | SHA-256 |
|---|---|---|---|
| `TAV-01S` | `archive/documentazione_originaria/tavola1-2.pdf` | structural carpentry; grid, columns, beams, fixed lines | `abd6061c305f2e7222f04659f519d7ee73ed0759b815ac994ff66215f060fec8` |
| `TAV-02S` | `archive/documentazione_originaria/tavola2-2.pdf` | structural carpentry; grid, columns, beams, fixed lines | `cd03839589e60ee46b3fd398d6a9fabca1a446859e6693a47d0f83d0e930520f` |

These are primary documentary sources. Architectural drawings are secondary cross-checks and cannot supersede the structural-grid sources for metric fitting.

## Source hierarchy

`TAV-01S → TAV-02S → other structural carpentry sheets → TAV-05S local sections/identifiers → historical M0-G comparator only after primary freeze`.

TAV.5 remains authoritative for what it directly documents, especially section properties and local relations. It is not required to contain the complete inter-axis dimension network.

## Discovery pipeline

For each primary source independently:

1. fetch the frozen source commit;
2. verify exact PDF SHA-256;
3. render page 0 at 300 dpi from the original PDF;
4. detect the structural-plan envelope;
5. construct external perimeter bands around that envelope;
6. OCR numeric tokens in multiple orientations and preprocessing families;
7. bind a token only when local graphics support a dimension line with two geometric references;
8. emit source-bound candidates with the original source bbox and provenance;
9. render a review overlay for human validation.

No cross-sheet coordinate transform is fitted during discovery.

## Candidate semantics

A discovered value can be classified only as:

- `STRUCTURAL_GRID_LINEAR_DIMENSION_CANDIDATE` — numeric value plus geometrically bound dimension line and two references;
- `REJECTED_NUMERIC_OBSERVATION` — numeric OCR without sufficient geometric binding.

Every candidate requires `PRIMARY_VISUAL_VALIDATED` before it can enter a metric relation network.

A validated relation must eventually name both referenced grid objects/fixed lines/column axes. A number alone is never a metric anchor.

## Cross-sheet comparison

After discovery, TAV-01S and TAV-02S remain separate evidence sets. A deterministic cross-sheet summary may compare counts, normalized values and source locations, but must not infer that equal numbers represent the same grid relation.

Matching or propagation between levels requires human/source-geometric validation.

## Authority and exclusions

During this stage:

- `primary_anchor_count = 0`;
- `fit_eligible = false` for every machine-discovered candidate;
- canonical geometry writes are forbidden;
- M0-G nodes are forbidden as discovery or fitting inputs;
- historical affine coefficients are forbidden;
- historical S-* annotations are forbidden as primary anchors;
- architectural internal room dimensions are not fitting authority for the structural grid;
- OCR repairs or guessed digits are forbidden.

Zero candidates is a valid closed result and must not trigger inferred dimensions.

## Required outputs

A governed artifact must contain:

- exact source manifest for TAV-01S and TAV-02S;
- 300 dpi raster for each source;
- per-source perimeter-band definitions;
- raw numeric observation counts;
- bound candidate list and rejected observation count;
- candidate source bboxes and two-reference geometry evidence;
- review overlay for each source;
- cross-sheet summary with authority closed;
- deterministic digests for per-source discovery and cross-sheet summary.

## Qualification gate

Qualification requires:

- both source SHA-256 values match the frozen registry;
- both rasters are produced from the frozen source commit;
- every candidate is source-bound and requires human visual validation;
- no primary anchor is emitted;
- no historical comparator/affine input is loaded;
- the full CEW-CAL-01 contract suite remains green;
- the exact-source multi-sheet workflow completes and uploads the governed artifact.
