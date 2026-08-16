"""
N12 — M0-OS-0001
Modello geometrico 3D preliminare per OpenSeesPy.

Questo script costruisce una geometria FEM derivata dai dati canonici N12:
- data/canonical/nodes.csv: 27 fili verticali/pilastri;
- data/canonical/storey_height_status.csv: altezza interpiano estradosso-estradosso = 3.20 m, se disponibile;
- default prudenziale: 3.20 m.

Il modello NON è ancora una verifica strutturale:
- materiali, masse, carichi e sezioni puntuali sono placeholder;
- travi e fondazioni saranno aggiunte solo dopo allineamento geometrico completo;
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


@dataclass(frozen=True)
class PlanNode:
    node_id: str
    x_m: float
    y_m: float
    chain_id: str
    status: str


def read_storey_height_m() -> float:
    """Read corrected storey height when the canonical file exists."""
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


def numeric_id(node_id: str) -> int:
    return int("".join(ch for ch in node_id if ch.isdigit()))


def tag(level_index: int, node_id: str) -> int:
    """Stable OpenSees node tag: level*1000 + numeric node id."""
    return level_index * 1000 + numeric_id(node_id)


def element_tag(level_index: int, node_id: str) -> int:
    """Stable OpenSees column element tag."""
    return 100000 + level_index * 1000 + numeric_id(node_id)


def define_placeholder_column_section() -> tuple[float, float, float, float, float, float]:
    """
    Elastic placeholder section for geometric smoke-test only.

    Units: kN, m.
    Concrete elastic modulus is a placeholder and must be replaced after M0-M.
    """
    b = 0.40
    h = 0.40
    area = b * h
    e_mod = 30_000_000.0  # kN/m2 placeholder ~30 GPa
    g_mod = e_mod / (2.0 * (1.0 + 0.20))
    iy = b * h**3 / 12.0
    iz = h * b**3 / 12.0
    j = iy + iz
    return area, e_mod, g_mod, j, iy, iz


def build_model(plan_nodes: Iterable[PlanNode], storey_height_m: float) -> tuple[int, int]:
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    levels = [i * storey_height_m for i in range(N_LEVELS)]

    node_count = 0
    for i, z in enumerate(levels):
        for n in plan_nodes:
            ops.node(tag(i, n.node_id), n.x_m, n.y_m, z)
            node_count += 1
            if i == 0:
                ops.fix(tag(i, n.node_id), 1, 1, 1, 1, 1, 1)

    # Local x axis for a column is vertical; vecxz uses global Y as reference.
    transf_tag = 1
    ops.geomTransf("PDelta", transf_tag, 0.0, 1.0, 0.0)

    area, e_mod, g_mod, j, iy, iz = define_placeholder_column_section()

    element_count = 0
    for i in range(N_LEVELS - 1):
        for n in plan_nodes:
            ops.element(
                "elasticBeamColumn",
                element_tag(i, n.node_id),
                tag(i, n.node_id),
                tag(i + 1, n.node_id),
                area,
                e_mod,
                g_mod,
                j,
                iy,
                iz,
                transf_tag,
            )
            element_count += 1

    return node_count, element_count


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
                    element_tag(i, n.node_id),
                    n.node_id,
                    i,
                    tag(i, n.node_id),
                    tag(i + 1, n.node_id),
                    "elasticBeamColumn",
                    "PLACEHOLDER_GEOMETRY_ONLY",
                ])


def main() -> None:
    plan_nodes = read_plan_nodes()
    storey_height_m = read_storey_height_m()
    node_count, element_count = build_model(plan_nodes, storey_height_m)
    export_nodes(plan_nodes, storey_height_m)
    export_column_elements(plan_nodes)

    print("N12 M0-OS-0001")
    print(f"Storey height: {storey_height_m:.2f} m")
    print(f"OpenSees nodes: {node_count}")
    print(f"Column elements: {element_count}")
    print("Status: GEOMETRY_ONLY / NOT_FOR_VERIFICATION")


if __name__ == "__main__":
    main()
