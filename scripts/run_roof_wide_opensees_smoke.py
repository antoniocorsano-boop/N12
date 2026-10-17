from __future__ import annotations

import json
import math
from pathlib import Path

from build_solver_neutral_frame_package import build_package

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generated" / "roof_wide_opensees_smoke_v1.json"

E = 30.0e9
NU = 0.20
G = E / (2.0 * (1.0 + NU))
DEFAULT_ND_SECTION = "30x45"
LOAD_N = -1000.0
TARGETS = ("P11", "P14", "P26")
EXPECTED_COMPONENTS = {
    frozenset({"P02", "P03", "P04", "P10", "P11", "P12", "P18", "P19", "P20", "P25", "P26", "P27", "P28", "P29", "P30"}),
    frozenset({"P05", "P06", "P07", "P13", "P14", "P15", "P22", "P22P", "P23", "P24"}),
}


def section_props(section_cm: str) -> tuple[float, float, float, float]:
    raw = section_cm.replace("_DOC", "").replace("DOC_", "")
    b_cm, h_cm = [float(v) for v in raw.lower().split("x")[:2]]
    b = b_cm / 100.0
    h = h_cm / 100.0
    area = b * h
    iy = b * h**3 / 12.0
    iz = h * b**3 / 12.0
    a, t = max(b, h), min(b, h)
    j = a * t**3 * (1.0 / 3.0 - 0.21 * (t / a) * (1.0 - t**4 / (12.0 * a**4)))
    return area, iy, iz, j


def z_local(node: dict) -> float:
    expr = node.get("z_expression")
    if expr:
        assert expr["base_parameter"] == "Z-V-ORDER"
        return float(expr["offset_m"])
    if "z_m" in node:
        return float(node["z_m"])
    raise AssertionError(f"unresolved roof-wide Z for {node['id']}")


def graph_components(adjacency: dict[str, set[str]]) -> list[set[str]]:
    unseen = set(adjacency)
    components: list[set[str]] = []
    while unseen:
        start = next(iter(unseen))
        comp: set[str] = set()
        stack = [start]
        while stack:
            p = stack.pop()
            if p in comp:
                continue
            comp.add(p)
            stack.extend(adjacency[p] - comp)
        unseen -= comp
        components.append(comp)
    return sorted(components, key=lambda c: (-len(c), sorted(c)))


def main() -> None:
    try:
        import openseespy.opensees as ops
    except Exception as exc:
        raise SystemExit(f"OPENSEES_IMPORT_FAILED: {exc}")

    package = build_package()
    nodes = {n["id"]: n for n in package["nodes"]}
    cols = [e for e in package["frame_elements"] if e["kind"] == "ROOF_SUPPORT_COLUMN"]
    beams = [e for e in package["frame_elements"] if e["kind"] == "ROOF_BEAM"]
    assert len(cols) == 25
    assert len(beams) == 31

    support_ids = sorted({e["node_j"].split(":", 1)[1] for e in cols})
    assert len(support_ids) == 25 and "P21" not in support_ids
    assert all("x_m" in nodes[f"ROOF:{p}"] and "y_m" in nodes[f"ROOF:{p}"] for p in support_ids)

    adjacency = {p: set() for p in support_ids}
    for e in beams:
        pi = e["node_i"].split(":", 1)[1]
        pj = e["node_j"].split(":", 1)[1]
        adjacency[pi].add(pj)
        adjacency[pj].add(pi)
    isolated = sorted(p for p, adj in adjacency.items() if not adj)
    components = graph_components(adjacency)
    component_sets = {frozenset(c) for c in components}
    if isolated:
        raise SystemExit("ISOLATED_ROOF_NODES: " + ",".join(isolated))
    if component_sets != EXPECTED_COMPONENTS:
        raise SystemExit("UNEXPECTED_ROOF_COMPONENTS: " + json.dumps([sorted(c) for c in components]))

    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    base_tag = {p: 1000 + i for i, p in enumerate(support_ids, start=1)}
    roof_tag = {p: 2000 + i for i, p in enumerate(support_ids, start=1)}

    for p in support_ids:
        rn = nodes[f"ROOF:{p}"]
        x, y, z = float(rn["x_m"]), float(rn["y_m"]), z_local(rn)
        ops.node(base_tag[p], x, y, 0.0)
        ops.node(roof_tag[p], x, y, z)
        ops.fix(base_tag[p], 1, 1, 1, 1, 1, 1)

    ops.geomTransf("Linear", 1, 1.0, 0.0, 0.0)
    ops.geomTransf("Linear", 2, 0.0, 0.0, 1.0)

    ele_tag = 1
    for e in cols:
        p = e["node_j"].split(":", 1)[1]
        a, iy, iz, j = section_props(e["section"]["value"])
        ops.element("elasticBeamColumn", ele_tag, base_tag[p], roof_tag[p], a, E, G, j, iy, iz, 1)
        ele_tag += 1

    scenario_sections: dict[str, str] = {}
    for e in beams:
        pi = e["node_i"].split(":", 1)[1]
        pj = e["node_j"].split(":", 1)[1]
        sec_obj = e["section"]
        if sec_obj["status"] == "READY":
            sec = sec_obj["value"]
        else:
            sec = DEFAULT_ND_SECTION
            scenario_sections[e["id"]] = sec
        a, iy, iz, j = section_props(sec)
        ops.element("elasticBeamColumn", ele_tag, roof_tag[pi], roof_tag[pj], a, E, G, j, iy, iz, 2)
        ele_tag += 1

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for p in TARGETS:
        ops.load(roof_tag[p], 0.0, 0.0, LOAD_N, 0.0, 0.0, 0.0)

    ops.system("UmfPack")
    ops.numberer("RCM")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    rc = ops.analyze(1)
    if rc != 0:
        raise SystemExit(f"ROOF_WIDE_ANALYZE_FAILED rc={rc}")

    response = {}
    for p in TARGETS:
        disp = [float(v) for v in ops.nodeDisp(roof_tag[p])]
        if not all(math.isfinite(v) for v in disp):
            raise SystemExit(f"NONFINITE_DISPLACEMENT {p}: {disp}")
        response[p] = disp

    result = {
        "schema": "n12.roof_wide.opensees_smoke.v1",
        "status": "PASS",
        "assessment_grade": False,
        "purpose": "whole-roof topology/adapter integrity smoke only",
        "counts": {
            "support_columns": len(cols),
            "roof_beams": len(beams),
            "roof_nodes": len(support_ids),
            "scenario_section_beams": len(scenario_sections),
            "roof_beam_components": len(components),
            "isolated_nodes": len(isolated),
        },
        "roof_beam_components": [sorted(c) for c in components],
        "level_transition_finding": {
            "status": "V_ORDER_COUPLING_BOUND_THROUGH_P21",
            "g4_verified_links": ["P20-P21", "P26-P21", "P21-P13", "P21-P22"],
            "v_order_t5_chain": ["P18-P19", "P19-P20", "P20-P21", "P21-P22", "P22-P22P", "P22P-P23"],
            "v_order_t5_section_cm": "20x45",
            "p21_vertical_status": "PRESENT_V_ORDER_ABSENT_ROOF",
            "policy": "DO_NOT_INVENT_G5_BRIDGE",
            "source_register": "docs/FOGLIO_LAVORO/M0_G5_ROOF_COMPONENT_CONNECTIVITY_v1.csv",
            "coupling_register": "docs/FOGLIO_LAVORO/ETW_V_ORDER_T5_COUPLING_BINDING_v1.csv",
        },
        "scenario": {
            "v_order_local_datum_m": 0.0,
            "eave_relative_z_m": 2.4,
            "ridge_relative_z_m": 3.4,
            "parametric_roof_section_cm": DEFAULT_ND_SECTION,
            "concrete_E_Pa": E,
            "concrete_nu": NU,
            "base_condition": "FIXED_LOCAL_SMOKE_ONLY",
            "unit_load_nodes": list(TARGETS),
            "unit_load_each_Fz_N": LOAD_N,
        },
        "scenario_sections": scenario_sections,
        "target_displacements_m": response,
        "warnings": [
            "This is not an assessment model and does not resolve any PARAMETRIC_ND section.",
            "Fixed bases, E/nu and Z-V-ORDER=0 are smoke-only scenario assumptions.",
            "The G5 beam graph has two source-bound components; structural coupling immediately below is source-bound through the V-order T5 chain containing P21.",
            "The V-order T5 chain is not copied into TAV-06S roof topology; no fictitious G5 bridge is added.",
            "All 25 roof XY coordinates are calibrated fixed-line analytical axes, not automatic section centroids."
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
