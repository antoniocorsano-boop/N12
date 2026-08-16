"""
N12 — M0-OS-0002
Modello geometrico 3D preliminare per OpenSeesPy.

Questo script costruisce una geometria FEM derivata dai dati canonici N12:
- data/canonical/nodes.csv: 27 fili verticali/pilastri;
- data/canonical/storey_height_status.csv: altezza interpiano estradosso-estradosso = 3.20 m;
- data/canonical/telaio5_tav5_candidate_matrix_v1.csv: percorso candidato Telaio 5;
- data/canonical/telaio_5.csv: livelli/campate/sezioni del Telaio 5;
- data/canonical/fem_section_placeholders.csv: sezioni provvisorie/documentali geometriche.

Il modello NON è ancora una verifica strutturale:
- materiali, masse e carichi sono placeholder;
- il raccordo Telaio 5 ↔ TAV.5 usa la sola ipotesi HYP_A_METRICA e resta non verificato;
- nessun risultato di analisi deve essere usato per diagnosi o progetto.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import openseespy.opensees as ops
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "OpenSeesPy non è installato. Esegui: "
        "pip install -r model/open_source_fem/requirements.txt"
    ) from exc

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "canonical"
EXPORTS = Path(__file__).resolve().parent / "exports"

N_LEVELS = 5
DEFAULT_STOREY_HEIGHT_M = 3.20
ACTIVE_TELAIO5_HYPOTHESIS = "HYP_A_METRICA"


@dataclass(frozen=True)
class PlanNode:
    node_id: str
    x_m: float
    y_m: float
    chain_id: str
    status: str


@dataclass(frozen=True)
class BeamCandidate:
    segment: str
    letter_from: str
    letter_to: str
    target_m: float
    node_i: str
    node_j: str
    measured_m: float
    delta_m: float
    status: str
    reason: str


def read_storey_height_m() -> float:
    path = DATA / "storey_height_status.csv"
    if not path.exists():
        return DEFAULT_STOREY_HEIGHT_M

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            value = (
                row.get("height_m")
                or row.get("altezza_m")
                or row.get("storey_height_m")
                or row.get("height_extradosso_extradosso_m")
            )
            if value:
                return float(value.replace(",", "."))
    return DEFAULT_STOREY_HEIGHT_M


def read_plan_nodes() -> list[PlanNode]:
    path = DATA / "nodes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Dataset canonico mancante: {path}")

    nodes: list[PlanNode] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nodes.append(
                PlanNode(
                    node_id=row["node_id"],
                    x_m=float(row["x_mm"]) / 1000.0,
                    y_m=float(row["y_mm"]) / 1000.0,
                    chain_id=row.get("chain_id", "ND"),
                    status=row.get("evidence_status", "ND"),
                )
            )
    return nodes


def read_telaio5_candidates() -> list[BeamCandidate]:
    path = DATA / "telaio5_tav5_candidate_matrix_v1.csv"
    if not path.exists():
        return []

    out: list[BeamCandidate] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("hypothesis") != ACTIVE_TELAIO5_HYPOTHESIS:
                continue
            out.append(
                BeamCandidate(
                    segment=row["segment"],
                    letter_from=row["letter_from"],
                    letter_to=row["letter_to"],
                    target_m=float(row["target_m"]),
                    node_i=row["candidate_from"],
                    node_j=row["candidate_to"],
                    measured_m=float(row["measured_m"]),
                    delta_m=float(row["delta_m"]),
                    status=row["evidence_status"],
                    reason=row.get("reason", ""),
                )
            )
    return out


def numeric_id(node_id: str) -> int:
    return int("".join(ch for ch in node_id if ch.isdigit()))


def tag(level_index: int, node_id: str) -> int:
    return level_index * 1000 + numeric_id(node_id)


def column_element_tag(level_index: int, node_id: str) -> int:
    return 100000 + level_index * 1000 + numeric_id(node_id)


def beam_element_tag(level_index: int, segment: str) -> int:
    segment_number = int("".join(ch for ch in segment if ch.isdigit()))
    return 200000 + level_index * 1000 + segment_number


def elastic_section(b: float, h: float) -> tuple[float, float, float, float, float, float]:
    area = b * h
    e_mod = 30_000_000.0  # kN/m2 placeholder ~30 GPa
    g_mod = e_mod / (2.0 * (1.0 + 0.20))
    iy = b * h**3 / 12.0
    iz = h * b**3 / 12.0
    j = iy + iz
    return area, e_mod, g_mod, j, iy, iz


def column_section() -> tuple[float, float, float, float, float, float]:
    return elastic_section(0.40, 0.40)


def beam_section_for(level_index: int, segment: str) -> tuple[str, tuple[float, float, float, float, float, float]]:
    """Return section id + elastic properties for preliminary Telaio 5 beams.

    Levels: 0=G1, 1=G2, 2=G3, 3=G4, 4=G5.
    G5 uses C2-C7 and 20x45. G1-G4 use 25x70 except C3-C5 = 140x20.
    """
    segment_no = int(segment[1:])
    if level_index == 4:
        return "BEAM_T5_20x45_DOC_GEOM", elastic_section(0.20, 0.45)
    if segment_no in (3, 4, 5):
        return "BEAM_T5_140x20_DOC_GEOM", elastic_section(1.40, 0.20)
    return "BEAM_T5_25x70_DOC_GEOM", elastic_section(0.25, 0.70)


def build_model(plan_nodes: Iterable[PlanNode], beams: Iterable[BeamCandidate], storey_height_m: float) -> tuple[int, int, int]:
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    levels = [i * storey_height_m for i in range(N_LEVELS)]

    node_count = 0
    plan_nodes = list(plan_nodes)
    plan_node_ids = {n.node_id for n in plan_nodes}
    for i, z in enumerate(levels):
        for n in plan_nodes:
            ops.node(tag(i, n.node_id), n.x_m, n.y_m, z)
            node_count += 1
            if i == 0:
                ops.fix(tag(i, n.node_id), 1, 1, 1, 1, 1, 1)

    column_transf = 1
    beam_transf = 2
    ops.geomTransf("PDelta", column_transf, 0.0, 1.0, 0.0)
    ops.geomTransf("Linear", beam_transf, 0.0, 0.0, 1.0)

    area, e_mod, g_mod, j, iy, iz = column_section()

    column_count = 0
    for i in range(N_LEVELS - 1):
        for n in plan_nodes:
            ops.element(
                "elasticBeamColumn",
                column_element_tag(i, n.node_id),
                tag(i, n.node_id),
                tag(i + 1, n.node_id),
                area,
                e_mod,
                g_mod,
                j,
                iy,
                iz,
                column_transf,
            )
            column_count += 1

    beam_count = 0
    for b in beams:
        if b.node_i not in plan_node_ids or b.node_j not in plan_node_ids:
            continue
        for i in range(N_LEVELS):
            # Telaio 5 G5 is documented as C2-C7 only.
            if i == 4 and b.segment in {"C1", "C8"}:
                continue
            section_id, props = beam_section_for(i, b.segment)
            area, e_mod, g_mod, j, iy, iz = props
            ops.element(
                "elasticBeamColumn",
                beam_element_tag(i, b.segment),
                tag(i, b.node_i),
                tag(i, b.node_j),
                area,
                e_mod,
                g_mod,
                j,
                iy,
                iz,
                beam_transf,
            )
            beam_count += 1

    return node_count, column_count, beam_count


def export_nodes(plan_nodes: list[PlanNode], storey_height_m: float) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    path = EXPORTS / "m0_nodes_3d.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["opensees_node", "source_node", "level", "x_m", "y_m", "z_m", "chain_id", "status"])
        for i in range(N_LEVELS):
            z = i * storey_height_m
            for n in plan_nodes:
                writer.writerow([tag(i, n.node_id), n.node_id, i, n.x_m, n.y_m, z, n.chain_id, n.status])


def export_column_elements(plan_nodes: list[PlanNode]) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    path = EXPORTS / "m0_column_elements.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "opensees_element",
            "source_node",
            "level_from",
            "node_i",
            "node_j",
            "element_type",
            "section_status",
        ])
        for i in range(N_LEVELS - 1):
            for n in plan_nodes:
                writer.writerow([
                    column_element_tag(i, n.node_id),
                    n.node_id,
                    i,
                    tag(i, n.node_id),
                    tag(i + 1, n.node_id),
                    "elasticBeamColumn",
                    "PLACEHOLDER_GEOMETRY_ONLY",
                ])


def export_telaio5_beams(beams: list[BeamCandidate]) -> None:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    path = EXPORTS / "m0_telaio5_beam_elements.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "opensees_element",
            "level",
            "segment",
            "letter_from",
            "letter_to",
            "source_i",
            "source_j",
            "node_i",
            "node_j",
            "section_id",
            "candidate_status",
            "target_m",
            "measured_m",
            "delta_m",
        ])
        for b in beams:
            for i in range(N_LEVELS):
                if i == 4 and b.segment in {"C1", "C8"}:
                    continue
                section_id, _ = beam_section_for(i, b.segment)
                writer.writerow([
                    beam_element_tag(i, b.segment),
                    i,
                    b.segment,
                    b.letter_from,
                    b.letter_to,
                    b.node_i,
                    b.node_j,
                    tag(i, b.node_i),
                    tag(i, b.node_j),
                    section_id,
                    b.status,
                    b.target_m,
                    b.measured_m,
                    b.delta_m,
                ])


def main() -> None:
    plan_nodes = read_plan_nodes()
    telaio5_beams = read_telaio5_candidates()
    storey_height_m = read_storey_height_m()
    node_count, column_count, beam_count = build_model(plan_nodes, telaio5_beams, storey_height_m)
    export_nodes(plan_nodes, storey_height_m)
    export_column_elements(plan_nodes)
    export_telaio5_beams(telaio5_beams)

    print("N12 M0-OS-0002")
    print(f"Storey height: {storey_height_m:.2f} m")
    print(f"OpenSees nodes: {node_count}")
    print(f"Column elements: {column_count}")
    print(f"Telaio 5 beam elements: {beam_count}")
    print(f"Telaio 5 hypothesis: {ACTIVE_TELAIO5_HYPOTHESIS}")
    print("Status: GEOMETRY_PLUS_T5_CANDIDATE / NOT_FOR_VERIFICATION")


if __name__ == "__main__":
    main()
