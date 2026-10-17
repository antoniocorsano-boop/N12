"""
N12 — M0-G geometry export fallback.

Genera gli stessi output geometrici principali del modello M0-OS senza importare
OpenSeesPy. Serve quando il wheel nativo OpenSeesPy non carica le DLL su Windows.

Output:
- exports/m0_nodes_3d.csv
- exports/m0_column_elements.csv
- exports/m0_telaio5_beam_elements.csv
- exports/m0_model_summary.txt

Stato: GEOMETRY_EXPORT_ONLY / NOT_FOR_VERIFICATION.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "canonical"
EXPORTS = Path(__file__).resolve().parent / "exports"

N_LEVELS = 5
DEFAULT_STOREY_HEIGHT_M = 3.20
TELAIO5_HYPOTHESIS = "HYP_A_METRICA"


@dataclass(frozen=True)
class PlanNode:
    node_id: str
    x_m: float
    y_m: float
    chain_id: str
    status: str


@dataclass(frozen=True)
class T5Segment:
    segment: str
    letter_from: str
    letter_to: str
    target_m: float
    candidate_from: str
    candidate_to: str
    measured_m: float
    delta_m: float
    evidence_status: str


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


def read_telaio5_segments() -> list[T5Segment]:
    path = DATA / "telaio5_tav5_candidate_matrix_v1.csv"
    if not path.exists():
        return []

    segments: list[T5Segment] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("hypothesis") != TELAIO5_HYPOTHESIS:
                continue
            segments.append(
                T5Segment(
                    segment=row["segment"],
                    letter_from=row["letter_from"],
                    letter_to=row["letter_to"],
                    target_m=float(row["target_m"].replace(",", ".")),
                    candidate_from=row["candidate_from"],
                    candidate_to=row["candidate_to"],
                    measured_m=float(row["measured_m"].replace(",", ".")),
                    delta_m=float(row["delta_m"].replace(",", ".")),
                    evidence_status=row.get("evidence_status", "ND"),
                )
            )
    return segments


def numeric_id(node_id: str) -> int:
    return int("".join(ch for ch in node_id if ch.isdigit()))


def node_tag(level_index: int, node_id: str) -> int:
    return level_index * 1000 + numeric_id(node_id)


def column_element_tag(level_index: int, node_id: str) -> int:
    return 100000 + level_index * 1000 + numeric_id(node_id)


def t5_beam_element_tag(level_index: int, segment_index: int) -> int:
    return 200000 + level_index * 1000 + segment_index


def t5_section_for_level_segment(level_index: int, segment: str) -> str:
    """Return geometric section label for Telaio 5 candidate beams.

    Level index 0..3 correspond to G1..G4. Level index 4 corresponds to G5.
    G5 uses C2-C7 only and section 20x45. G1-G4 use 25x70 except C3-C5
    where the historical/documentary family is 140x20.
    """
    if level_index == 4:
        return "T5_BEAM_20x45_DOC_G5"
    if segment in {"C3", "C4", "C5"}:
        return "T5_BEAM_140x20_DOC_G1_G4_C3_C5"
    return "T5_BEAM_25x70_DOC_G1_G4"


def export_nodes(plan_nodes: Iterable[PlanNode], storey_height_m: float) -> int:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    path = EXPORTS / "m0_nodes_3d.csv"
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["opensees_node", "source_node", "level", "x_m", "y_m", "z_m", "chain_id", "status"])
        for i in range(N_LEVELS):
            z = i * storey_height_m
            for n in plan_nodes:
                writer.writerow([node_tag(i, n.node_id), n.node_id, i, n.x_m, n.y_m, z, n.chain_id, n.status])
                count += 1
    return count


def export_column_elements(plan_nodes: Iterable[PlanNode]) -> int:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    path = EXPORTS / "m0_column_elements.csv"
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "opensees_element",
            "source_node",
            "level_from",
            "node_i",
            "node_j",
            "element_type",
            "section_ref",
            "section_status",
        ])
        for i in range(N_LEVELS - 1):
            for n in plan_nodes:
                writer.writerow([
                    column_element_tag(i, n.node_id),
                    n.node_id,
                    i,
                    node_tag(i, n.node_id),
                    node_tag(i + 1, n.node_id),
                    "elasticBeamColumn",
                    "COLUMN_40x40_PLACEHOLDER",
                    "PLACEHOLDER_GEOMETRY_ONLY",
                ])
                count += 1
    return count


def export_telaio5_beams(segments: list[T5Segment]) -> int:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    path = EXPORTS / "m0_telaio5_beam_elements.csv"
    count = 0
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "opensees_element",
            "hypothesis",
            "storey_label",
            "level_index",
            "segment",
            "letter_from",
            "letter_to",
            "node_i",
            "node_j",
            "candidate_from",
            "candidate_to",
            "target_m",
            "measured_m",
            "delta_m",
            "section_ref",
            "evidence_status",
            "model_status",
        ])
        for level_index in range(N_LEVELS):
            storey_label = f"G{level_index + 1}"
            for idx, segment in enumerate(segments, start=1):
                if level_index == 4 and segment.segment in {"C1", "C8"}:
                    # G5 is documented as C2-C7 only.
                    continue
                writer.writerow([
                    t5_beam_element_tag(level_index, idx),
                    TELAIO5_HYPOTHESIS,
                    storey_label,
                    level_index,
                    segment.segment,
                    segment.letter_from,
                    segment.letter_to,
                    node_tag(level_index, segment.candidate_from),
                    node_tag(level_index, segment.candidate_to),
                    segment.candidate_from,
                    segment.candidate_to,
                    segment.target_m,
                    segment.measured_m,
                    segment.delta_m,
                    t5_section_for_level_segment(level_index, segment.segment),
                    segment.evidence_status,
                    "CANDIDATE_GEOMETRY_ONLY",
                ])
                count += 1
    return count


def export_summary(storey_height_m: float, node_count: int, column_count: int, t5_count: int) -> None:
    path = EXPORTS / "m0_model_summary.txt"
    with path.open("w", encoding="utf-8") as f:
        f.write("N12 M0-G export fallback\n")
        f.write(f"Storey height: {storey_height_m:.2f} m\n")
        f.write(f"3D nodes: {node_count}\n")
        f.write(f"Column elements: {column_count}\n")
        f.write(f"Telaio 5 candidate beam elements: {t5_count}\n")
        f.write(f"Telaio 5 hypothesis: {TELAIO5_HYPOTHESIS}\n")
        f.write("Status: GEOMETRY_EXPORT_ONLY / NOT_FOR_VERIFICATION\n")


def main() -> None:
    plan_nodes = read_plan_nodes()
    segments = read_telaio5_segments()
    storey_height_m = read_storey_height_m()

    node_count = export_nodes(plan_nodes, storey_height_m)
    column_count = export_column_elements(plan_nodes)
    t5_count = export_telaio5_beams(segments)
    export_summary(storey_height_m, node_count, column_count, t5_count)

    print("N12 M0-G export fallback")
    print(f"Storey height: {storey_height_m:.2f} m")
    print(f"3D nodes: {node_count}")
    print(f"Column elements: {column_count}")
    print(f"Telaio 5 candidate beam elements: {t5_count}")
    print(f"Telaio 5 hypothesis: {TELAIO5_HYPOTHESIS}")
    print("Status: GEOMETRY_EXPORT_ONLY / NOT_FOR_VERIFICATION")


if __name__ == "__main__":
    main()
