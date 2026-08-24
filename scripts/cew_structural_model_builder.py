#!/usr/bin/env python3
"""CEW Canonical Structural Model Builder v0.

Builds a solver-independent structural graph from already-promoted canonical
sources. It does not extract geometry from drawings and does not infer
connectivity from geometric proximity.

N12 reference implementation:
- M0G analytical 3D nodes
- M0G rigid offsets
- M0G ordinary member connectivity
- FPEP/P07 foundation model
- admitted M1E foundation XY solver-placement rule

Foundation Z remains symbolic/ND until a separate evidentiary or admitted
modeling rule defines it.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class BuildError(ValueError):
    pass


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def num(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if text in {"", "ND", "N/A", "NA", "null", "None"}:
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise BuildError(f"Expected numeric value or ND, got {value!r}") from exc


def ensure_unique(rows: Iterable[Dict[str, str]], key: str, label: str) -> None:
    seen = set()
    for row in rows:
        value = row.get(key)
        if not value:
            raise BuildError(f"{label}: missing {key}")
        if value in seen:
            raise BuildError(f"{label}: duplicate {key}={value}")
        seen.add(value)


def resolve_handoff_counts(handoff: Dict[str, Any]) -> Dict[str, int]:
    inv = handoff["frozen_inventory"]
    return {
        "superstructure_nodes": int(inv["analytical_nodes_total"]),
        "support_core_nodes": int(inv["support_core_nodes"]),
        "beam_face_nodes": int(inv["beam_face_nodes"]),
        "rigid_offsets": int(inv["rigid_joint_links"]),
        "ordinary_members": int(inv["ordinary_structural_members"]),
    }


def build_model(
    handoff_path: Path,
    nodes_path: Path,
    rigid_path: Path,
    members_path: Path,
    foundation_path: Path,
    foundation_xy_rule_path: Path,
) -> Dict[str, Any]:
    handoff = load_json(handoff_path)
    nodes = load_csv(nodes_path)
    rigid = load_csv(rigid_path)
    members = load_csv(members_path)
    foundation = load_csv(foundation_path)
    fxy = load_json(foundation_xy_rule_path)

    ensure_unique(nodes, "node_id", "nodes")
    ensure_unique(rigid, "link_id", "rigid offsets")
    ensure_unique(members, "member_id", "ordinary members")
    ensure_unique(foundation, "entity_id", "foundation entities")

    expected = resolve_handoff_counts(handoff)
    if len(nodes) != expected["superstructure_nodes"]:
        raise BuildError(f"M0G node count mismatch: {len(nodes)} != {expected['superstructure_nodes']}")
    if len(rigid) != expected["rigid_offsets"]:
        raise BuildError(f"M0G rigid-offset count mismatch: {len(rigid)} != {expected['rigid_offsets']}")
    if len(members) != expected["ordinary_members"]:
        raise BuildError(f"M0G member count mismatch: {len(members)} != {expected['ordinary_members']}")

    node_by_id = {r["node_id"]: r for r in nodes}
    core_count = sum(1 for r in nodes if r.get("node_role") == "SUPPORT_CORE")
    face_count = sum(1 for r in nodes if r.get("node_role") != "SUPPORT_CORE")
    if core_count != expected["support_core_nodes"] or face_count != expected["beam_face_nodes"]:
        raise BuildError(
            f"M0G node-role count mismatch: cores={core_count}/{expected['support_core_nodes']}, "
            f"faces={face_count}/{expected['beam_face_nodes']}"
        )

    # Validate topology by explicit IDs only. No geometric proximity is used.
    for r in rigid:
        if r["core_node_id"] not in node_by_id:
            raise BuildError(f"Rigid link {r['link_id']} missing core node {r['core_node_id']}")
        if r["face_node_id"] not in node_by_id:
            raise BuildError(f"Rigid link {r['link_id']} missing face node {r['face_node_id']}")
    for r in members:
        if r["node_i"] not in node_by_id or r["node_j"] not in node_by_id:
            raise BuildError(f"Member {r['member_id']} references unknown node")

    f_support_rows = [r for r in foundation if r.get("entity_kind") == "SUPPORT"]
    f_member_rows = [r for r in foundation if r.get("entity_kind") != "SUPPORT"]
    if len(f_support_rows) != 38:
        raise BuildError(f"Foundation support count mismatch: {len(f_support_rows)} != 38")
    if len(f_member_rows) != 55:
        raise BuildError(f"Foundation member count mismatch: {len(f_member_rows)} != 55")

    fxy_map = {str(r["foundation_support_id"]): r for r in fxy.get("mapping", [])}
    if len(fxy_map) != 38:
        raise BuildError(f"Foundation XY mapping count mismatch: {len(fxy_map)} != 38")

    f_support_ids = {str(r["support_id"]) for r in f_support_rows}
    if set(fxy_map) != f_support_ids:
        raise BuildError("Foundation XY mapping identities do not match P07 support identities exactly")

    # Stable superstructure node entities.
    cew_nodes: List[Dict[str, Any]] = []
    for r in nodes:
        role = r.get("node_role") or "NODE"
        entity_type = "SUPPORT_CORE" if role == "SUPPORT_CORE" else "FACE_NODE"
        x, y, z = num(r.get("x_m")), num(r.get("y_m")), num(r.get("z_m"))
        if x is None or y is None or z is None:
            raise BuildError(f"Promoted M0G node {r['node_id']} lacks numeric XYZ")
        cew_nodes.append({
            "entity_id": r["node_id"],
            "entity_type": entity_type,
            "generation_id": "N12-M0G-CURRENT",
            "status": r.get("validation_state") or "CURRENT",
            "evidence_state": r.get("coordinate_evidence_state") or "ND",
            "source_claim_refs": [nodes_path.as_posix()],
            "level_id": r.get("level_id"),
            "support_id": r.get("support_id") or None,
            "point3d": {
                "x": x,
                "y": y,
                "z": z,
                "unit": "m",
                "coordinate_system": "N12_M0G_RELATIVE_STRUCTURAL",
                "state": r.get("coordinate_evidence_state") or "ND",
                "xy_input_provenance": r.get("xy_input_provenance") or None,
                "z_input_provenance": r.get("z_input_provenance") or None,
            },
        })

    cew_rigid: List[Dict[str, Any]] = []
    for r in rigid:
        cew_rigid.append({
            "entity_id": r["link_id"],
            "entity_type": "RIGID_OFFSET",
            "generation_id": "N12-M0G-CURRENT",
            "status": r.get("validation_state") or "CURRENT",
            "evidence_state": r.get("link_evidence_state") or "INF",
            "source_claim_refs": [rigid_path.as_posix()],
            "core_node_id": r["core_node_id"],
            "face_node_id": r["face_node_id"],
            "offset_vector_m": [num(r.get("dx_m")), num(r.get("dy_m")), num(r.get("dz_m"))],
            "structural_member": False,
            "usage_rule": r.get("usage_rule"),
        })

    cew_members: List[Dict[str, Any]] = []
    for r in members:
        member_class = r.get("member_class") or "STRUCTURAL_MEMBER"
        if "BEAM" in member_class:
            entity_type = "BEAM"
        elif "COLUMN" in member_class:
            entity_type = "COLUMN"
        else:
            entity_type = member_class
        cew_members.append({
            "entity_id": r["member_id"],
            "entity_type": entity_type,
            "generation_id": "N12-M0G-CURRENT",
            "status": r.get("validation_state") or "CURRENT",
            "evidence_state": r.get("topology_evidence") or r.get("connectivity_evidence") or "ND",
            "source_claim_refs": [members_path.as_posix(), r.get("source_ledger")],
            "member_axis": {
                "start_node_id": r["node_i"],
                "end_node_id": r["node_j"],
                "local_axis_definition": "DERIVE_FROM_ORDERED_NODE_AXIS_AT_SOLVER_ADAPTER",
                "topology_claim_ref": r.get("source_ledger") or members_path.as_posix(),
            },
            "support_i": r.get("support_i"),
            "support_j": r.get("support_j"),
            "storey_id": r.get("storey_id"),
            "section_ref_or_value": r.get("section_cm") or None,
            "section_evidence_state": r.get("section_evidence") or "ND",
            "geometric_length_m": num(r.get("geometric_length_m")),
        })

    cew_fsupports: List[Dict[str, Any]] = []
    fnode_id_by_support: Dict[str, str] = {}
    for r in f_support_rows:
        sid = str(r["support_id"])
        mapping = fxy_map[sid]
        fid = r["entity_id"]
        fnode_id_by_support[sid] = fid
        cew_fsupports.append({
            "entity_id": fid,
            "entity_type": "FOUNDATION_SUPPORT",
            "generation_id": "N12-FPEP-P07-CURRENT",
            "status": r.get("validation_state") or "CURRENT_WITH_WATCH",
            "evidence_state": "MOD",
            "source_claim_refs": [foundation_path.as_posix(), foundation_xy_rule_path.as_posix()],
            "support_id": sid,
            "point3d": {
                "x": float(mapping["solver_x_m"]),
                "y": float(mapping["solver_y_m"]),
                "z": None,
                "z_symbol": r.get("z_symbol") or "ZF_COMMON",
                "unit": "m",
                "coordinate_system": "N12_M0G_XY_PLUS_SYMBOLIC_FOUNDATION_Z",
                "state": "MOD",
                "model_rule_id": fxy["rule_id"],
                "underlying_xy_evidence_state": mapping.get("coordinate_evidence_state"),
                "underlying_xy_provenance": mapping.get("xy_input_provenance"),
            },
            "geometry_status": "PARTIAL_XY_NUMERIC_Z_SYMBOLIC",
        })

    cew_fmembers: List[Dict[str, Any]] = []
    for r in f_member_rows:
        a, b = str(r["from_support_id"]), str(r["to_support_id"])
        if a not in fnode_id_by_support or b not in fnode_id_by_support:
            raise BuildError(f"Foundation member {r['entity_id']} references unknown support {a}-{b}")
        prop_state = r.get("property_binding_class") or "ND"
        cew_fmembers.append({
            "entity_id": r["entity_id"],
            "entity_type": "FOUNDATION_MEMBER",
            "generation_id": "N12-FPEP-P07-CURRENT",
            "status": r.get("validation_state") or "CURRENT_WITH_WATCH",
            "evidence_state": r.get("topology_authority") or "P07_PRIMARY",
            "source_claim_refs": [foundation_path.as_posix()],
            "member_axis": {
                "start_node_id": fnode_id_by_support[a],
                "end_node_id": fnode_id_by_support[b],
                "local_axis_definition": "DERIVE_WHEN_FOUNDATION_Z_IS_NUMERIC",
                "topology_claim_ref": r.get("topology_authority") or "P07_PRIMARY",
            },
            "from_support_id": a,
            "to_support_id": b,
            "section_family": r.get("section_family") or None,
            "property_binding_class": prop_state,
            "geometry_status": "TOPOLOGY_READY_XY_READY_Z_SYMBOLIC",
        })

    now = datetime.now(timezone.utc).isoformat()
    model = {
        "schema_version": "0.1",
        "builder": "CEW_STRUCTURAL_MODEL_BUILDER_v0",
        "project_id": "N12",
        "generation_id": "N12-CEW-CSM-v0",
        "generated_at": now,
        "model_status": "CANONICAL_GRAPH_BUILT_WITH_FOUNDATION_Z_RESIDUAL",
        "solver_independent": True,
        "geometry_created_by_proximity": False,
        "canonical_sources": {
            "m0g_handoff": {"path": handoff_path.as_posix(), "sha256": sha256_file(handoff_path)},
            "nodes": {"path": nodes_path.as_posix(), "sha256": sha256_file(nodes_path)},
            "rigid_offsets": {"path": rigid_path.as_posix(), "sha256": sha256_file(rigid_path)},
            "members": {"path": members_path.as_posix(), "sha256": sha256_file(members_path)},
            "foundation": {"path": foundation_path.as_posix(), "sha256": sha256_file(foundation_path)},
            "foundation_xy_rule": {"path": foundation_xy_rule_path.as_posix(), "sha256": sha256_file(foundation_xy_rule_path)},
        },
        "coordinate_systems": {
            "superstructure": handoff["coordinate_frame"],
            "foundation": {
                "xy": "M1E admitted solver-placement projection from G1 SUPPORT_CORE",
                "z": "ZF_COMMON symbolic; numeric value ND",
            },
        },
        "inventory": {
            "superstructure_nodes": len(cew_nodes),
            "support_core_nodes": core_count,
            "beam_face_nodes": face_count,
            "rigid_offsets": len(cew_rigid),
            "ordinary_members": len(cew_members),
            "foundation_supports": len(cew_fsupports),
            "foundation_members": len(cew_fmembers),
            "roof_special_geometry_ref": handoff["canonical_references"].get("roof_special_geometry_3d", {}).get("path"),
            "roof_special_geometry_count": handoff["frozen_inventory"]["roof_special_nonordinary_geometry"]["total"],
        },
        "nodes": cew_nodes,
        "rigid_offsets": cew_rigid,
        "members": cew_members,
        "foundation_supports": cew_fsupports,
        "foundation_members": cew_fmembers,
        "unresolved_geometry": [
            {
                "id": "N12-CSM-RES-FND-Z",
                "domain": "FOUNDATION_NUMERIC_Z",
                "state": "ND",
                "effect": "Foundation topology and XY are queryable, but foundation members are not full numeric 3D axes until ZF_COMMON is resolved by evidence or admitted modeling rule."
            }
        ],
        "authorized_uses": [
            "3D graph visualization of superstructure",
            "identity/topology queries across superstructure and foundation",
            "evidence-state and residual overlays",
            "scenario overlay preparation",
            "solver-adapter preparation without numerical foundation Z"
        ],
        "not_authorized": [
            "current-state solver execution merely because the graph exists",
            "inventing numeric foundation Z",
            "using geometric proximity to modify connectivity",
            "promoting foundation solver XY from MOD to source evidence",
            "treating roof special geometry as ordinary structural members without a separate gate"
        ]
    }
    return model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff", required=True, type=Path)
    parser.add_argument("--nodes", required=True, type=Path)
    parser.add_argument("--rigid-offsets", required=True, type=Path)
    parser.add_argument("--members", required=True, type=Path)
    parser.add_argument("--foundation", required=True, type=Path)
    parser.add_argument("--foundation-xy-rule", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    try:
        model = build_model(
            args.handoff,
            args.nodes,
            args.rigid_offsets,
            args.members,
            args.foundation,
            args.foundation_xy_rule,
        )
    except (OSError, json.JSONDecodeError, BuildError) as exc:
        print(f"CEW STRUCTURAL MODEL BUILDER: FAIL: {exc}")
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    inv = model["inventory"]
    print(
        "CEW STRUCTURAL MODEL BUILDER: PASS | "
        f"nodes={inv['superstructure_nodes']} | rigid={inv['rigid_offsets']} | "
        f"members={inv['ordinary_members']} | foundation={inv['foundation_supports']}+{inv['foundation_members']} | "
        f"status={model['model_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
