from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from build_m0_analytical_graph import build as build_m0

ROOT = Path(__file__).resolve().parents[1]
FL = ROOT / "docs" / "FOGLIO_LAVORO"
PARAMS = FL / "M0_3D_PARAMETER_PACK_v1.csv"
UPPER_Z = FL / "M0_UPPER_Z_SCENARIO_v1.csv"


def read_params() -> dict[str, dict[str, str]]:
    with PARAMS.open(newline="", encoding="utf-8") as f:
        return {row["parameter_id"]: row for row in csv.DictReader(f)}


def read_upper_z_rules() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    with UPPER_Z.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_roof_support: dict[str, dict[str, str]] = {}
    for row in rows:
        if not row["z_rule_id"].startswith("UZ-00"):
            continue
        if row["node_scope"] == "ROOF_RIDGE" or row["node_scope"] == "ROOF_EAVE_OR_PERIMETER":
            for support_id in row["node_ids"].split(";"):
                by_roof_support[support_id] = row
    return rows, by_roof_support


def numeric_param(params: dict[str, dict[str, str]], parameter_id: str) -> float | None:
    row = params.get(parameter_id)
    if not row:
        return None
    if not row["status"].startswith("READY"):
        return None
    try:
        return float(row["value"])
    except (TypeError, ValueError):
        return None


def apply_z_resolution(graph: dict, params: dict[str, dict[str, str]], roof_rules: dict[str, dict[str, str]]) -> None:
    """Map every symbolic z_ref to a numeric value or explicit base+offset expression."""
    z_g1 = numeric_param(params, "Z-G1")
    for node in graph["nodes"]:
        if "z_m" in node:
            continue
        ref = node.get("z_ref")
        if not ref:
            continue

        if ref == "Z_G1":
            if z_g1 is None:
                node["z_expression"] = {"base_parameter": "Z-G1", "offset_m": 0.0}
            else:
                node["z_m"] = z_g1
                node["z_resolved_from"] = "Z-G1"
            continue

        if node["id"].startswith("V_ORDER:"):
            support_id = node["id"].split(":", 1)[1]
            node["z_expression"] = {
                "base_parameter": "Z-V-ORDER",
                "offset_m": 0.0,
                "rule": "UZ-001",
                "support_id": support_id,
            }
            continue

        if node["id"].startswith("ROOF:"):
            support_id = node["id"].split(":", 1)[1]
            rule = roof_rules.get(support_id)
            if rule is None:
                node["z_unmapped_ref"] = ref
                continue
            node["z_expression"] = {
                "base_parameter": rule["base_parameter"],
                "offset_m": float(rule["offset_m"]),
                "rule": rule["z_rule_id"],
                "support_id": support_id,
                "scenario_status": rule["status"],
            }
            continue

        node["z_unmapped_ref"] = ref


def unresolved_numeric_requirements(graph: dict, params: dict[str, dict[str, str]]) -> list[str]:
    required: set[str] = set()

    for pid, row in params.items():
        if row["solver_policy"] == "REQUIRE_FOR_NUMERIC" and row["status"] in {"PARAMETRIC_ND", "BLOCKED_LOCAL"}:
            required.add(pid)

    for element in graph["elements"]:
        section = element.get("section") or {}
        if section.get("status") == "PARAMETRIC_ND":
            raw = section["parameter"]
            pid = raw.replace("SECTION_", "SECTION-")
            if pid in params:
                required.add(pid)
            else:
                required.add(raw)

    for node in graph["nodes"]:
        expr = node.get("z_expression")
        if expr:
            base = expr["base_parameter"]
            if numeric_param(params, base) is None:
                required.add(base)
        if "z_unmapped_ref" in node:
            required.add("Z-UNMAPPED:" + node["z_unmapped_ref"])

    return sorted(required)


def build_package() -> dict:
    graph = build_m0()
    params = read_params()
    z_rows, roof_rules = read_upper_z_rules()
    apply_z_resolution(graph, params, roof_rules)
    unresolved = unresolved_numeric_requirements(graph, params)

    package = {
        "schema": "n12.solver_neutral_frame_package.v1",
        "source_graph_schema": graph["schema"],
        "source_release": graph["release"],
        "adapter_policy": {
            "blocked_local_excluded": True,
            "symbolic_parameters_allowed": True,
            "numeric_export_requires_zero_unresolved": True,
            "automatic_material_defaults": False,
            "automatic_fixed_base": False,
            "automatic_section_inheritance": False,
            "upper_z_single_base_parameter": "Z-V-ORDER",
        },
        "nodes": graph["nodes"],
        "frame_elements": graph["elements"],
        "excluded_local": graph["blocked_local"],
        "parameters": list(params.values()),
        "upper_z_rules": z_rows,
        "preflight": {
            "symbolic_status": "PASS",
            "numeric_status": "READY" if not unresolved else "BLOCKED_EXPECTED",
            "numeric_unresolved": unresolved,
            "counts": graph["validation"]["counts"],
        },
    }
    validate(package)
    return package


def validate(package: dict) -> None:
    assert package["preflight"]["symbolic_status"] == "PASS"
    assert package["adapter_policy"]["blocked_local_excluded"] is True
    assert package["adapter_policy"]["automatic_fixed_base"] is False
    assert package["adapter_policy"]["automatic_material_defaults"] is False
    assert len(package["frame_elements"]) == 69
    assert len(package["excluded_local"]) == 7
    assert package["preflight"]["counts"]["v_order_t5_beams"] == 6
    assert package["preflight"]["counts"]["roof_columns"] == 25
    assert package["preflight"]["counts"]["roof_beams"] == 31
    assert not any("z_unmapped_ref" in n for n in package["nodes"]), "unmapped symbolic Z reference"
    roof_nodes = [n for n in package["nodes"] if n["id"].startswith("ROOF:")]
    v_order_nodes = [n for n in package["nodes"] if n["id"].startswith("V_ORDER:")]
    assert len(roof_nodes) == 25
    assert len(v_order_nodes) == 26
    assert all(n.get("z_expression", {}).get("base_parameter") == "Z-V-ORDER" for n in roof_nodes + v_order_nodes)
    assert all(n.get("z_expression", {}).get("offset_m") in {2.4, 3.4} for n in roof_nodes)
    assert all(n.get("z_expression", {}).get("offset_m") == 0.0 for n in v_order_nodes)
    assert any(n["id"] == "V_ORDER:P21" for n in v_order_nodes)
    assert not any(n["id"] == "ROOF:P21" for n in roof_nodes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/generated/m0_solver_neutral_frame_package_v1.json")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-numeric", action="store_true")
    args = parser.parse_args()

    package = build_package()
    print(json.dumps(package["preflight"], indent=2))

    if args.require_numeric and package["preflight"]["numeric_unresolved"]:
        raise SystemExit("NUMERIC_EXPORT_BLOCKED: " + ", ".join(package["preflight"]["numeric_unresolved"]))

    if args.check:
        return

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
