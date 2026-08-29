from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "docs" / "FOGLIO_LAVORO" / "M0_ROOF_B_SMOKE_CORE_v1.csv"
SKELETON = ROOT / "docs" / "FOGLIO_LAVORO" / "ETW_G5_ROOF_ANALYTICAL_SKELETON_RELEASE_v1.csv"
OUT = ROOT / "data" / "generated" / "roof_b_opensees_smoke_v1.json"

E = 30.0e9
NU = 0.20
G = E / (2.0 * (1.0 + NU))
LOAD_N = -1000.0


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def section_props(section_cm: str) -> tuple[float, float, float, float]:
    b_cm, h_cm = [float(v) for v in section_cm.lower().split("x")]
    b = b_cm / 100.0
    h = h_cm / 100.0
    area = b * h
    iy = b * h**3 / 12.0
    iz = h * b**3 / 12.0
    # Deliberately simple Saint-Venant torsion approximation for smoke only.
    a, t = max(b, h), min(b, h)
    j = a * t**3 * (1.0 / 3.0 - 0.21 * (t / a) * (1.0 - t**4 / (12.0 * a**4)))
    return area, iy, iz, j


def main() -> None:
    try:
        import openseespy.opensees as ops
    except Exception as exc:  # pragma: no cover - CI diagnostic
        raise SystemExit(f"OPENSEES_IMPORT_FAILED: {exc}")

    core = rows(CORE)
    node_rows = {r["entity_ref"]: r for r in core if r["entity_kind"] == "NODE"}
    beam_ids = {r["entity_ref"] for r in core if r["entity_kind"] == "BEAM"}
    skel = {r["analytical_id"]: r for r in rows(SKELETON)}

    expected_nodes = {"P05", "P06", "P07", "P13", "P14", "P15", "P22", "P23"}
    expected_beams = {"AG5-009", "AG5-010", "AG5-012", "AG5-013", "AG5-014", "AG5-015", "AG5-017", "AG5-018"}
    assert set(node_rows) == expected_nodes
    assert beam_ids == expected_beams

    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    ids = {p: i + 1 for i, p in enumerate(sorted(node_rows))}
    base_ids = {p: 100 + i for p, i in ids.items()}
    top_ids = {p: 200 + i for p, i in ids.items()}

    for p, r in node_rows.items():
        x = float(r["x_m"])
        y = float(r["y_m"])
        z = float(r["z_rel_m"])
        ops.node(base_ids[p], x, y, 0.0)
        ops.node(top_ids[p], x, y, z)
        ops.fix(base_ids[p], 1, 1, 1, 1, 1, 1)

    # Local-axis reference vectors: columns use global X, roof beams use global Z.
    ops.geomTransf("Linear", 1, 1.0, 0.0, 0.0)
    ops.geomTransf("Linear", 2, 0.0, 0.0, 1.0)

    ele_tag = 1
    for p, r in node_rows.items():
        a, iy, iz, j = section_props(r["section_cm"])
        ops.element("elasticBeamColumn", ele_tag, base_ids[p], top_ids[p], a, E, G, j, iy, iz, 1)
        ele_tag += 1

    beam_tag_map: dict[str, int] = {}
    for eid in sorted(beam_ids):
        r = skel[eid]
        pi = r["node_i"].removeprefix("AX-")
        pj = r["node_j"].removeprefix("AX-")
        assert pi in top_ids and pj in top_ids, (eid, pi, pj)
        a, iy, iz, j = section_props("30x50")
        ops.element("elasticBeamColumn", ele_tag, top_ids[pi], top_ids[pj], a, E, G, j, iy, iz, 2)
        beam_tag_map[eid] = ele_tag
        ele_tag += 1

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    ops.load(top_ids["P14"], 0.0, 0.0, LOAD_N, 0.0, 0.0, 0.0)

    ops.system("UmfPack")
    ops.numberer("RCM")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    rc = ops.analyze(1)
    if rc != 0:
        raise SystemExit(f"OPENSEES_ANALYZE_FAILED rc={rc}")

    disp = [float(v) for v in ops.nodeDisp(top_ids["P14"])]
    if not all(math.isfinite(v) for v in disp):
        raise SystemExit(f"NONFINITE_DISPLACEMENT: {disp}")

    result = {
        "schema": "n12.roof_b.opensees_smoke.v1",
        "status": "PASS",
        "assessment_grade": False,
        "purpose": "software/adapter smoke only",
        "scenario": {
            "v_order_local_datum_m": 0.0,
            "eave_relative_z_m": 2.4,
            "ridge_relative_z_m": 3.4,
            "concrete_E_Pa": E,
            "concrete_nu": NU,
            "base_condition": "FIXED_LOCAL_SMOKE_ONLY",
            "load_at_P14_N": [0.0, 0.0, LOAD_N],
        },
        "counts": {
            "base_nodes": len(base_ids),
            "roof_nodes": len(top_ids),
            "columns": len(node_rows),
            "beams": len(beam_ids),
        },
        "p14_displacement_m": disp,
        "source_core": str(CORE.relative_to(ROOT)),
        "source_skeleton": str(SKELETON.relative_to(ROOT)),
        "warnings": [
            "All Z are local/scenario values, not canonical global building elevations.",
            "Material and fixed-base assumptions are smoke-only and must not enter assessment calculations.",
            "Only the source-bound WING-B known-section core is included."
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
