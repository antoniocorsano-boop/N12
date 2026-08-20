from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FL = ROOT / "docs" / "FOGLIO_LAVORO"

G23 = FL / "ETW2_G2_G3_SOURCE_BOUND_CHAIN_BRIDGE_v1.csv"
G5_COL = FL / "ETW_G5_ANALYTICAL_COLUMN_RELEASE_v1.csv"
G5_BEAM = FL / "ETW_G5_ROOF_ANALYTICAL_SKELETON_RELEASE_v1.csv"
TERRACE = FL / "ETW_FIRST_LEVEL_TERRACE_LOCAL_SUBGRAPH_v1.csv"
ENTITY_RELEASE = FL / "M0_STRUCTURAL_ENTITY_RELEASE_v1.csv"

READY_G23 = {
    "G23-BRIDGE-P13",
    "G23-BRIDGE-P20",
    "G23-BRIDGE-P22",
    "G23-BRIDGE-P26",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def add_node(nodes: dict[str, dict], node_id: str, **attrs) -> None:
    current = nodes.setdefault(node_id, {"id": node_id})
    for key, value in attrs.items():
        if value not in (None, "", "NA", "ND"):
            current.setdefault(key, value)


def parse_xy(value: str) -> tuple[float, float]:
    x, y = value.split("/")
    return float(x), float(y)


def section_param(section_release: str, element_id: str) -> dict:
    if section_release and section_release not in {"ND", "PARTIAL_DOC"}:
        return {"status": "READY", "value": section_release}
    return {
        "status": "PARAMETRIC_ND",
        "parameter": f"SECTION_{element_id}",
    }


def build() -> dict:
    nodes: dict[str, dict] = {}
    elements: list[dict] = []

    # 1) Four source-bound G2 -> G3 verticals.
    for row in read_csv(G23):
        if row["bridge_id"] not in READY_G23:
            continue
        p = row["persistent_support_id"]
        x, y = parse_xy(row["xy_m"])
        n2 = f"G2:{p}"
        n3 = f"G3:{p}"
        add_node(nodes, n2, support_id=p, x_m=x, y_m=y, z_m=float(row["z_from_m"]), coord_state="SOURCE_BOUND")
        add_node(nodes, n3, support_id=p, x_m=x, y_m=y, z_m=float(row["z_to_m"]), coord_state="SOURCE_BOUND")
        elements.append(
            {
                "id": row["bridge_id"],
                "kind": "COLUMN_VERTICAL",
                "scope": "G2_G3",
                "node_i": n2,
                "node_j": n3,
                "section_i_cm": row["g2_section_cm"],
                "section_j_cm": row["g3_section_cm"],
                "release_class": "READY",
                "source": G23.relative_to(ROOT).as_posix(),
                "evidence_state": row["evidence_state"],
            }
        )

    # 2) Twenty-five numbered roof-support columns. Z is intentionally symbolic.
    for row in read_csv(G5_COL):
        eid = row["analytical_column_id"]
        if not eid.startswith("AC-G5-") or eid in {"AC-G5-X01", "AC-G5-GATE"}:
            continue
        p = row["support_id"]
        n0 = f"V_ORDER:{p}"
        n1 = f"ROOF:{p}"
        add_node(nodes, n0, support_id=p, z_ref=f"Z_V_ORDER_{p}", coord_state="XY_AXIS_REF_Z_PARAMETRIC")
        add_node(nodes, n1, support_id=p, z_ref=f"Z_ROOF_{p}", coord_state="XY_AXIS_REF_Z_PARAMETRIC")
        elements.append(
            {
                "id": eid,
                "kind": "ROOF_SUPPORT_COLUMN",
                "scope": "G5",
                "node_i": n0,
                "node_j": n1,
                "axis_ref": row["axis_ref"],
                "section": {"status": "READY", "value": row["section_cm"]},
                "release_class": "READY",
                "z_policy": "PARAMETRIC_UPPER_LEVEL_Z",
                "source": G5_COL.relative_to(ROOT).as_posix(),
            }
        )

    # 3) Thirty-one roof beams. Endpoint topology is source-bound; 16 sections stay parametric.
    for row in read_csv(G5_BEAM):
        eid = row["analytical_id"]
        if not re.fullmatch(r"AG5-\d{3}", eid):
            continue
        pi = row["node_i"].removeprefix("AX-")
        pj = row["node_j"].removeprefix("AX-")
        ni = f"ROOF:{pi}"
        nj = f"ROOF:{pj}"
        add_node(nodes, ni, support_id=pi, z_ref=f"Z_ROOF_{pi}", coord_state="XY_AXIS_REF_Z_PARAMETRIC")
        add_node(nodes, nj, support_id=pj, z_ref=f"Z_ROOF_{pj}", coord_state="XY_AXIS_REF_Z_PARAMETRIC")
        sec = section_param(row["section_release"], eid)
        release_class = "READY" if sec["status"] == "READY" else "PARAMETRIC_ND"
        elements.append(
            {
                "id": eid,
                "kind": "ROOF_BEAM",
                "scope": "G5",
                "node_i": ni,
                "node_j": nj,
                "section": sec,
                "release_class": release_class,
                "z_policy": "PARAMETRIC_ROOF_NODE_Z",
                "source": G5_BEAM.relative_to(ROOT).as_posix(),
                "source_edge_ref": row["source_edge_ref"],
            }
        )

    # 4) First-level terrace receiver split + documentary 1.50 m branch.
    terrace_rows = {r["entity_id"]: r for r in read_csv(TERRACE)}
    for eid in ("ETW-FLT-E01", "ETW-FLT-E02", "ETW-FLT-E03"):
        row = terrace_rows[eid]
        def terrace_node(ref: str) -> str:
            if ref.startswith("ETW-FLT-"):
                return f"G1:{ref}"
            return f"G1:{ref}"
        ni = terrace_node(row["node_i"])
        nj = terrace_node(row["node_j"])
        add_node(nodes, ni, z_ref="Z_G1", coord_state="LOCAL_SOURCE_BOUND")
        add_node(nodes, nj, z_ref="Z_G1", coord_state="LOCAL_SOURCE_BOUND")
        sec_ready = row["section_status"].endswith("_DOC")
        sec = (
            {"status": "READY", "value": row["section_status"]}
            if sec_ready
            else {"status": "PARAMETRIC_ND", "parameter": f"SECTION_{eid}"}
        )
        elements.append(
            {
                "id": eid,
                "kind": row["entity_kind"],
                "scope": "G1_TERRACE",
                "node_i": ni,
                "node_j": nj,
                "length_m": None if row["length_m"] in {"", "NA", "ND"} else float(row["length_m"]),
                "section": sec,
                "release_class": "READY" if sec_ready else "PARAMETRIC_ND",
                "source": TERRACE.relative_to(ROOT).as_posix(),
                "support_status": row["support_status"],
            }
        )

    blocked = [
        {
            "release_id": row["release_id"],
            "scope": row["level_scope"],
            "entity_ref": row["entity_ref"],
            "kind": row["entity_kind"],
            "reason": row["notes"],
        }
        for row in read_csv(ENTITY_RELEASE)
        if row["release_class"] == "BLOCKED_LOCAL"
    ]

    graph = {
        "schema": "n12.m0.analytical_graph.v1",
        "release": "M0_STRUCTURAL_MODEL_RELEASE_v1",
        "policy": {
            "include": ["READY", "PARAMETRIC_ND"],
            "exclude": ["BLOCKED_LOCAL"],
            "typical_floor_extrusion": False,
            "automatic_p_to_n_crosswalk": False,
            "assessment_grade": False,
        },
        "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
        "elements": elements,
        "blocked_local": blocked,
    }
    validate(graph)
    return graph


def validate(graph: dict) -> None:
    elements = graph["elements"]
    verticals = [e for e in elements if e["scope"] == "G2_G3"]
    roof_columns = [e for e in elements if e["kind"] == "ROOF_SUPPORT_COLUMN"]
    roof_beams = [e for e in elements if e["kind"] == "ROOF_BEAM"]
    terrace = [e for e in elements if e["scope"] == "G1_TERRACE"]

    assert len(verticals) == 4, f"expected 4 G2-G3 verticals, got {len(verticals)}"
    assert len(roof_columns) == 25, f"expected 25 roof columns, got {len(roof_columns)}"
    assert len(roof_beams) == 31, f"expected 31 roof beams, got {len(roof_beams)}"
    assert len(terrace) == 3, f"expected 3 terrace beam segments, got {len(terrace)}"

    assert all(e.get("node_i") != "ROOF:P21" and e.get("node_j") != "ROOF:P21" for e in roof_columns), "P21 must not be extruded as roof column"
    assert all(not re.fullmatch(r"N\d{3}", n["id"].split(":")[-1]) for n in graph["nodes"]), "legacy N-ID leaked into M0 node identity"
    assert graph["policy"]["typical_floor_extrusion"] is False
    assert graph["policy"]["automatic_p_to_n_crosswalk"] is False

    ready_roof_sections = sum(1 for e in roof_beams if e["section"]["status"] == "READY")
    param_roof_sections = sum(1 for e in roof_beams if e["section"]["status"] == "PARAMETRIC_ND")
    assert ready_roof_sections == 15, ready_roof_sections
    assert param_roof_sections == 16, param_roof_sections

    graph["validation"] = {
        "status": "PASS",
        "counts": {
            "g2_g3_verticals": len(verticals),
            "roof_columns": len(roof_columns),
            "roof_beams": len(roof_beams),
            "roof_beams_section_ready": ready_roof_sections,
            "roof_beams_section_parametric": param_roof_sections,
            "terrace_segments": len(terrace),
            "blocked_local_records": len(graph["blocked_local"]),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/generated/m0_analytical_graph_v1.json")
    parser.add_argument("--check", action="store_true", help="validate without writing output")
    args = parser.parse_args()

    graph = build()
    print(json.dumps(graph["validation"], indent=2))
    if args.check:
        return

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(graph, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"WROTE {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
