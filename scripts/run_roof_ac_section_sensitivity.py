from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "docs" / "FOGLIO_LAVORO" / "M0_ROOF_AC_SENSITIVITY_CORE_v1.csv"
SKELETON = ROOT / "docs" / "FOGLIO_LAVORO" / "ETW_G5_ROOF_ANALYTICAL_SKELETON_RELEASE_v1.csv"
OUT = ROOT / "data" / "generated" / "roof_ac_section_sensitivity_v1.json"

E = 30.0e9
NU = 0.20
G = E / (2.0 * (1.0 + NU))
LOAD_N = -1000.0
CANDIDATES = ("20x45", "30x45", "30x50")


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
    a, t = max(b, h), min(b, h)
    j = a * t**3 * (1.0 / 3.0 - 0.21 * (t / a) * (1.0 - t**4 / (12.0 * a**4)))
    return area, iy, iz, j


def scenario_section(row: dict[str, str], scenario: str) -> str:
    if row["section_state"] == "DOC":
        return row["section_cm"]
    if scenario.startswith("UNIFORM_"):
        return scenario.removeprefix("UNIFORM_")
    if scenario == "RIDGE_LOW":
        return "20x45" if row["role"] == "RIDGE_UNKNOWN" else "30x45"
    if scenario == "RIDGE_HIGH":
        return "30x50" if row["role"] == "RIDGE_UNKNOWN" else "30x45"
    if scenario == "NONRIDGE_LOW":
        return "30x45" if row["role"] == "RIDGE_UNKNOWN" else "20x45"
    if scenario == "NONRIDGE_HIGH":
        return "30x45" if row["role"] == "RIDGE_UNKNOWN" else "30x50"
    raise ValueError(scenario)


def analyze_wing(wing: str, scenario: str, core: list[dict[str, str]], skel: dict[str, dict[str, str]]) -> dict:
    try:
        import openseespy.opensees as ops
    except Exception as exc:
        raise SystemExit(f"OPENSEES_IMPORT_FAILED: {exc}")

    node_rows = {r["entity_ref"]: r for r in core if r["wing"] == wing and r["entity_kind"] == "NODE"}
    beam_rows = {r["entity_ref"]: r for r in core if r["wing"] == wing and r["entity_kind"] == "BEAM"}
    target = "P11" if wing == "A" else "P26"

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

    ops.geomTransf("Linear", 1, 1.0, 0.0, 0.0)
    ops.geomTransf("Linear", 2, 0.0, 0.0, 1.0)

    ele_tag = 1
    for p, r in node_rows.items():
        a, iy, iz, j = section_props(r["section_cm"])
        ops.element("elasticBeamColumn", ele_tag, base_ids[p], top_ids[p], a, E, G, j, iy, iz, 1)
        ele_tag += 1

    applied_sections: dict[str, str] = {}
    for eid, r in sorted(beam_rows.items()):
        s = skel[eid]
        pi = s["node_i"].removeprefix("AX-")
        pj = s["node_j"].removeprefix("AX-")
        assert pi in top_ids and pj in top_ids, (wing, eid, pi, pj)
        sec = scenario_section(r, scenario)
        applied_sections[eid] = sec
        a, iy, iz, j = section_props(sec)
        ops.element("elasticBeamColumn", ele_tag, top_ids[pi], top_ids[pj], a, E, G, j, iy, iz, 2)
        ele_tag += 1

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    ops.load(top_ids[target], 0.0, 0.0, LOAD_N, 0.0, 0.0, 0.0)
    ops.system("UmfPack")
    ops.numberer("RCM")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    rc = ops.analyze(1)
    if rc != 0:
        raise SystemExit(f"OPENSEES_ANALYZE_FAILED wing={wing} scenario={scenario} rc={rc}")

    disp = [float(v) for v in ops.nodeDisp(top_ids[target])]
    if not all(math.isfinite(v) for v in disp):
        raise SystemExit(f"NONFINITE_DISPLACEMENT wing={wing} scenario={scenario}: {disp}")

    return {
        "wing": wing,
        "scenario": scenario,
        "target_node": target,
        "target_uz_m": disp[2],
        "target_displacement_m": disp,
        "applied_unknown_sections": {
            eid: sec for eid, sec in applied_sections.items() if beam_rows[eid]["section_state"] != "DOC"
        },
        "counts": {"nodes": len(node_rows), "beams": len(beam_rows)},
    }


def main() -> None:
    core = rows(CORE)
    skel = {r["analytical_id"]: r for r in rows(SKELETON)}
    scenarios = [
        "UNIFORM_20x45",
        "UNIFORM_30x45",
        "UNIFORM_30x50",
        "RIDGE_LOW",
        "RIDGE_HIGH",
        "NONRIDGE_LOW",
        "NONRIDGE_HIGH",
    ]

    results = [analyze_wing(wing, scenario, core, skel) for wing in ("A", "C") for scenario in scenarios]

    summary: dict[str, dict] = {}
    for wing in ("A", "C"):
        wr = [r for r in results if r["wing"] == wing]
        mid = next(r for r in wr if r["scenario"] == "UNIFORM_30x45")
        base = abs(mid["target_uz_m"])
        summary[wing] = {
            "reference_scenario": "UNIFORM_30x45",
            "reference_abs_uz_m": base,
            "uniform_section_envelope_abs_uz_m": [
                min(abs(r["target_uz_m"]) for r in wr if r["scenario"].startswith("UNIFORM_")),
                max(abs(r["target_uz_m"]) for r in wr if r["scenario"].startswith("UNIFORM_")),
            ],
            "ridge_only_relative_change_pct": {
                r["scenario"]: (abs(r["target_uz_m"]) / base - 1.0) * 100.0
                for r in wr if r["scenario"] in {"RIDGE_LOW", "RIDGE_HIGH"}
            },
            "nonridge_relative_change_pct": {
                r["scenario"]: (abs(r["target_uz_m"]) / base - 1.0) * 100.0
                for r in wr if r["scenario"] in {"NONRIDGE_LOW", "NONRIDGE_HIGH"}
            },
        }

    result = {
        "schema": "n12.roof_ac.section_sensitivity.v1",
        "status": "PASS",
        "assessment_grade": False,
        "purpose": "prioritize closure of PARAMETRIC_ND roof sections; not structural verification",
        "scenario_basis": {
            "candidate_sections_cm": list(CANDIDATES),
            "candidate_origin": "documented project roof/upper-beam section families used only as sensitivity values",
            "v_order_local_datum_m": 0.0,
            "eave_relative_z_m": 2.4,
            "ridge_relative_z_m": 3.4,
            "concrete_E_Pa": E,
            "concrete_nu": NU,
            "base_condition": "FIXED_LOCAL_SENSITIVITY_ONLY",
            "unit_load_N": LOAD_N,
        },
        "summary": summary,
        "runs": results,
        "warnings": [
            "No scenario section is promoted to a canonical member section.",
            "Absolute displacement values depend on smoke-only material/base assumptions and are not assessment results.",
            "Sensitivity ranking is valid only for these isolated local roof submodels and the stated unit load."
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
