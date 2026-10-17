# AGENTS.md

N12 — existing RC building (Ariano Irpino) reconstruction for EdiLus-EE. Evidence-based structural data repo, not a typical software project. Docs and commits are in **Italian**; commit messages use conventional prefixes (`docs:`, `model:`, `data:`, `archive:`).

## Cardinal rule: evidence status

Every structural datum carries a status: `DOC` / `MIS` / `RIF` / `INF` / `INC` / `ND`. Never promote `ND`/`INC`/`INF` to `DOC` for convenience. Placeholders may generate geometry for smoke tests but **never** verification, diagnosis, or intervention design.

## Workflow before editing data

1. New info first updates the canonical datasets + provenance + evidence status, or `docs/REGISTRO_MASTER.md` (versioned `RM-xxxx`) / a linked dataset.
2. Decisions go in `docs/DECISIONI/<GATE>_<TOPIC>_v1.md` (e.g. `M0G_FILI_FISSI_v1.md`), following the existing format.
3. Historical ZIPs/DXF are immutable evidence (`archive/ARTEFATTI_STORICI.md`). Git is the source of truth for current state.

## Current state (2026-08)

- Gate: **M0-G** (global 3D geometry), then M0-S → M0-A → M0-M → M0-L → M0-V → M1 → M2.
- Read `docs/STATO_RIPRESA.md`, `model/M0-G/STATUS.md`, `model/open_source_fem/README.md` (`M0-OS-0002`) before working.
- 27 vertical pillar chains (`data/canonical/nodes.csv`), 5 levels, storey height 3.20 m extradosso-extradosso (`storey_height_status.csv`).
- Telaio 5 alignment is under hypothesis `HYP_A_METRICA` (`telaio5_tav5_candidate_matrix_v1.csv`), NOT verified — no promotion without overlay against TAV.5.
- `nodes.csv` is the 27-chain geometric reference, **not** the full TAV.5 topology (57 nodes / 141 candidate connections are separate files).

## CSV conventions (`data/canonical/`)

- Encoded `utf-8-sig` (BOM); delimiter may be comma **or** semicolon — use `csv.Sniffer`/`utf-8-sig` when reading, as `opensees_m0_geometry.py` does.
- Plan coordinates are in **mm** (`x_mm`, `y_mm`); convert to m with `/1000.0`.
- Required columns: provenance (`source`/`provenienza`) + evidence status (`evidence_status`/`stato`).

## FEM model (OpenSeesPy)

- Generator: `model/open_source_fem/opensees_m0_geometry.py`; run from repo root with `.venv\Scripts\python.exe` (Windows venv).
- **Gotcha:** on this machine `import openseespy.opensees` fails (`openseespywin` DLL load error), so the script exits with "OpenSeesPy non è installato" and `exports/` cannot be regenerated locally. Don't treat stale `exports/` CSVs as fresh output; the Python file remains the reference implementation.
- Node/element tagging in the script: node = `level*1000+num`, column = `100000+...`, beam = `200000+...`.

## Verification

No tests, linter, CI, or `.gitignore` exist. Verification is manual: run the generator and diff against the expected console output in `model/open_source_fem/README.md`, or cross-check CSV columns/statuses with `grep`/`rg`.

## Do not assume

`README.md` lists `cad/`, `scripts/`, `evidence/`, `model/edilus/` as planned — these directories do not exist yet.
