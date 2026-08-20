from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from build_m0_analytical_graph import build as build_m0

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "docs" / "FOGLIO_LAVORO" / "M0_3D_PARAMETER_PACK_v1.csv"


def read_params() -> dict[str, dict[str, str]]:
    with PARAMS.open(newline="", encoding="utf-8") as f:
        return {row["parameter_id"]: row for row in csv.DictReader(f)}


def unresolved_numeric_requirements(graph: dict, params: dict[str, dict[str, str]]) -> list[str]:
    required: set[str] = set()

    # Global numeric requirements.
    for pid, row in params.items():
        if row["solver_policy"] == "REQUIRE_FOR_NUMERIC" and row["status"] in {"PARAMETRIC_ND", "BLOCKED_LOCAL"}:
            required.add(pid)

    # Resolve section parameters actually referenced by M0 elements.
    for element in graph["elements"]:
        section = element.get("section") or {}
        if section.get("status") == "PARAMETRIC_ND":
            raw = section["parameter"]
            pid = raw.replace("SECTION_", "SECTION-")
            if pid in params:
                required.add(pid)
            else:
                required.add(raw)

    # Any symbolic Z blocks numeric export.
    if any("z_ref" in node and "z_m" not in node for node in graph["nodes"]):
        required.add("Z-UPPER-SYMBOLIC-NODES")

    return sorted(required)


def build_package() -> dict:
    graph = build_m0()
    params = read_params()
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
        },
        "nodes": graph["nodes"],
        "frame_elements": graph["elements"],
        "excluded_local": graph["blocked_local"],
        "parameters": list(params.values()),
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
    assert len(package["frame_elements"]) == 63
    assert len(package["excluded_local"]) == 7
    assert package["preflight"]["counts"]["roof_columns"] == 25
    assert package["preflight"]["counts"]["roof_beams"] == 31


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
