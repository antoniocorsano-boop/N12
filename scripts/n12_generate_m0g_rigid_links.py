#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "data/canonical/M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv"
OUT = ROOT / "data/canonical/M0G_RIGID_JOINT_LINKS_CURRENT_v1.csv"
AUDIT = ROOT / "analysis/automation/M0G_BUILD_RIGID_JOINT_LINKS_AUDIT_v1.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def f4(v: float) -> str:
    return f"{v:.4f}"


def main() -> None:
    rows = read_csv(NODES)
    cores: dict[tuple[str, str], dict[str, str]] = {}
    faces: list[dict[str, str]] = []

    for row in rows:
        key = (row["level_id"], row["support_id"])
        if row["node_role"] == "SUPPORT_CORE":
            if key in cores:
                raise SystemExit(f"duplicate support core for {key}")
            cores[key] = row
        elif row.get("beam_id") and row.get("support_id"):
            faces.append(row)

    out_rows: list[dict[str, str]] = []
    orphan_core = 0
    nonzero_fail = 0
    z_mismatch = 0
    section_envelope_fail = 0
    seen_face_nodes: set[str] = set()

    for face in faces:
        key = (face["level_id"], face["support_id"])
        core = cores.get(key)
        if core is None:
            orphan_core += 1
            continue

        if face["node_id"] in seen_face_nodes:
            raise SystemExit(f"duplicate face-node rigid-link target: {face['node_id']}")
        seen_face_nodes.add(face["node_id"])

        cx, cy, cz = float(core["x_m"]), float(core["y_m"]), float(core["z_m"])
        fx, fy, fz = float(face["x_m"]), float(face["y_m"]), float(face["z_m"])
        dx, dy, dz = fx - cx, fy - cy, fz - cz
        length = math.sqrt(dx * dx + dy * dy + dz * dz)

        if length <= 1e-9:
            nonzero_fail += 1
        if abs(dz) > 1e-9:
            z_mismatch += 1

        sx = float(face["section_x_cm"]) / 100.0 if face.get("section_x_cm") else 0.0
        sy = float(face["section_y_cm"]) / 100.0 if face.get("section_y_cm") else 0.0
        half_diag = math.hypot(sx / 2.0, sy / 2.0) if sx and sy else 0.0
        if half_diag and length > half_diag + 0.002:
            section_envelope_fail += 1

        source_prov = face.get("coordinate_evidence_state", "INF")
        out_rows.append({
            "link_id": f"M0G-RL-{face['node_id']}",
            "level_id": face["level_id"],
            "support_id": face["support_id"],
            "core_node_id": core["node_id"],
            "face_node_id": face["node_id"],
            "beam_id": face["beam_id"],
            "beam_end": face["beam_end"],
            "face_ref": face["face_ref"],
            "dx_m": f4(dx),
            "dy_m": f4(dy),
            "dz_m": f4(dz),
            "offset_length_m": f4(length),
            "link_role": "RIGID_JOINT_OFFSET",
            "source_face_coordinate_state": source_prov,
            "link_evidence_state": "INF",
            "validation_state": "CURRENT_DERIVED_WITH_PROVENANCE_WATCH",
            "usage_rule": "ANALYTICAL_CONSTRAINT_NOT_ORDINARY_STRUCTURAL_MEMBER",
            "note": "Rigid analytical offset from support/column core to the distinct beam-support face incidence; same physical support and level; never merge face incidences by support_id."
        })

    out_rows.sort(key=lambda r: (int(r["level_id"][1:]), r["support_id"], r["beam_id"], r["beam_end"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "link_id","level_id","support_id","core_node_id","face_node_id","beam_id","beam_end","face_ref",
        "dx_m","dy_m","dz_m","offset_length_m","link_role","source_face_coordinate_state","link_evidence_state",
        "validation_state","usage_rule","note"
    ]
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(out_rows)

    by_level = {g: sum(1 for r in out_rows if r["level_id"] == g) for g in ["G1","G2","G3","G4","G5"]}
    unique_links = len({r["link_id"] for r in out_rows})
    unique_faces = len({r["face_node_id"] for r in out_rows})
    same_support = sum(1 for r in out_rows if cores[(r["level_id"], r["support_id"])]["support_id"] == r["support_id"])
    same_level = sum(1 for r in out_rows if cores[(r["level_id"], r["support_id"])]["level_id"] == r["level_id"])

    checks = [
        ("TOTAL_RIGID_LINK_ROWS", 464, len(out_rows), "One link for every beam-support face node."),
        ("G1_RIGID_LINK_ROWS", 104, by_level["G1"], "Reused PT face incidences."),
        ("G2_RIGID_LINK_ROWS", 96, by_level["G2"], "48 beams x 2 ends."),
        ("G3_RIGID_LINK_ROWS", 96, by_level["G3"], "48 beams x 2 ends."),
        ("G4_RIGID_LINK_ROWS", 96, by_level["G4"], "48 beams x 2 ends."),
        ("G5_RIGID_LINK_ROWS", 72, by_level["G5"], "36 beams x 2 ends."),
        ("UNIQUE_LINK_IDS", 464, unique_links, "No duplicate rigid links."),
        ("UNIQUE_FACE_NODE_TARGETS", 464, unique_faces, "Each face incidence is linked exactly once."),
        ("ORPHAN_CORE_NODES", 0, orphan_core, "Every face node must find the core of the same support and level."),
        ("SAME_SUPPORT_LINKS", 464, same_support, "Rigid offset never crosses physical supports."),
        ("SAME_LEVEL_LINKS", 464, same_level, "Rigid offset never crosses storeys."),
        ("ZERO_LENGTH_LINKS", 0, nonzero_fail, "No beam-face incidence may be collapsed to the support core."),
        ("NONZERO_DZ_LINKS", 0, z_mismatch, "Core and face incidence lie on the same structural plane."),
        ("OUTSIDE_SUPPORT_HALF_DIAGONAL", 0, section_envelope_fail, "Face point must remain on/within the rectangular support envelope within tolerance."),
    ]

    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["check_id","expected","actual","status","note"])
        failed = False
        for cid, expected, actual, note in checks:
            ok = str(expected) == str(actual)
            failed = failed or not ok
            w.writerow([cid, expected, actual, "PASS" if ok else "FAIL", note])

    if failed:
        raise SystemExit("M0G rigid-link audit failed; inspect audit CSV")
    print(f"M0G_RIGID_LINKS = PASS rows={len(out_rows)}")


if __name__ == "__main__":
    main()
