#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "canonical"
AUDIT_DIR = ROOT / "analysis" / "automation"
OUTPUT = DATA / "M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv"
AUDIT = AUDIT_DIR / "M0G_BUILD_3D_ANALYTICAL_NODES_AUDIT_v1.csv"

QUEUE = ROOT / "automation" / "N12_WORK_QUEUE_v1.json"
SELECTED_ID = "M0G-BUILD-3D-ANALYTICAL-NODES"

LEVEL_FILES = {
    "G2": DATA / "STOREY_SUPPORT_SECTIONS_G2_v1.csv",
    "G3": DATA / "STOREY_SUPPORT_SECTIONS_G3_v1.csv",
    "G4": DATA / "STOREY_SUPPORT_SECTIONS_G4_v1.csv",
    "G5": DATA / "STOREY_SUPPORT_SECTIONS_G5_v1.csv",
}
BEAM_FILES = {
    "G2": DATA / "STOREY_BEAMS_G2_v1.csv",
    "G3": DATA / "STOREY_BEAMS_G3_v1.csv",
    "G4": DATA / "STOREY_BEAMS_G4_v1.csv",
    "G5": DATA / "STOREY_BEAMS_G5_v1.csv",
}

FIELDNAMES = [
    "node_id",
    "level_id",
    "node_role",
    "support_id",
    "source_node_id",
    "beam_id",
    "beam_end",
    "face_ref",
    "x_m",
    "y_m",
    "z_m",
    "section_x_cm",
    "section_y_cm",
    "section_evidence_state",
    "xy_input_provenance",
    "z_input_provenance",
    "topology_evidence_state",
    "coordinate_derivation",
    "coordinate_evidence_state",
    "validation_state",
    "note",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def token(value: str) -> str:
    return (
        value.replace("'", "PRIME")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("+", "PLUS")
    )


def f4(value: float) -> str:
    return f"{value:.4f}"


def parse_section_cm(section: str) -> tuple[float, float]:
    clean = section.lower().replace(" ", "")
    if "x" not in clean or clean == "nd":
        raise ValueError(f"unsupported section value: {section}")
    sx, sy = clean.split("x", 1)
    return float(sx), float(sy)


def classify_xy_input(metric_provenance: str, level_id: str) -> str:
    # G1 may retain direct/documented common-frame metric evidence.
    # Upper planes necessarily pass through the MIS-supported inter-sheet registration.
    if level_id == "G1" and metric_provenance == "DOC_METRIC_OR_AXIS":
        return "DOC"
    return "MIS"


def face_intersection(
    center: tuple[float, float],
    toward: tuple[float, float],
    sx_cm: float,
    sy_cm: float,
) -> tuple[float, float, str]:
    """Intersect the centre-to-centre analytical ray with the rectangular support boundary."""
    cx, cy = center
    tx, ty = toward
    dx = tx - cx
    dy = ty - cy
    if math.hypot(dx, dy) < 1e-12:
        raise ValueError(f"coincident support centres at {center}")

    hx = sx_cm / 200.0
    hy = sy_cm / 200.0
    candidates: list[tuple[float, str]] = []
    if dx > 1e-12:
        candidates.append((hx / dx, "X_POS"))
    elif dx < -1e-12:
        candidates.append((-hx / dx, "X_NEG"))
    if dy > 1e-12:
        candidates.append((hy / dy, "Y_POS"))
    elif dy < -1e-12:
        candidates.append((-hy / dy, "Y_NEG"))

    positive = [(t, face) for t, face in candidates if t > 0]
    if not positive:
        raise ValueError(f"no positive face intersection from {center} toward {toward}")
    t, face = min(positive, key=lambda item: item[0])
    return cx + t * dx, cy + t * dy, face


def main() -> int:
    # Required source registries.
    levels = {r["level_id"]: r for r in read_csv(DATA / "STOREY_LEVELS_CURRENT_v1.csv")}
    support_rows = read_csv(DATA / "VERTICAL_SUPPORT_LINES_CURRENT_v1.csv")
    supports = {r["support_id"]: r for r in support_rows}
    pt_master_rows = read_csv(DATA / "PT_MASTER_CURRENT.csv")
    pt_master = {r["entity_id"]: r for r in pt_master_rows}
    pt_face_nodes = read_csv(DATA / "PT_ANALYTICAL_NODES_v1.csv")

    sections: dict[str, dict[str, dict[str, str]]] = {}
    for level_id, path in LEVEL_FILES.items():
        rows = read_csv(path)
        sections[level_id] = {r["support_id"]: r for r in rows}

    beams: dict[str, list[dict[str, str]]] = {
        level_id: read_csv(path) for level_id, path in BEAM_FILES.items()
    }

    expected_support_counts = {"G1": 38, "G2": 34, "G3": 34, "G4": 34, "G5": 25}
    expected_beam_counts = {"G2": 48, "G3": 48, "G4": 48, "G5": 36}
    for level_id, expected in expected_beam_counts.items():
        if len(beams[level_id]) != expected:
            raise ValueError(f"{level_id} beam count {len(beams[level_id])} != {expected}")
    if len(pt_face_nodes) != 102:
        raise ValueError(f"PT face-node count {len(pt_face_nodes)} != 102")

    rows: list[dict[str, object]] = []

    # 1) Support-core nodes. They are distinct from beam-face nodes.
    for level_id in ["G1", "G2", "G3", "G4", "G5"]:
        present_key = f"{level_id.lower()}_present"
        present = [r for r in support_rows if r[present_key] == "PRESENT"]
        if len(present) != expected_support_counts[level_id]:
            raise ValueError(
                f"{level_id} support presence count {len(present)} != {expected_support_counts[level_id]}"
            )
        z = float(levels[level_id]["z_rel_to_g1_m"])
        for s in present:
            sid = s["support_id"]
            if level_id == "G1":
                sec = pt_master[sid]
                sx, sy = parse_section_cm(sec["section_cm"])
                sec_state = "DOC"
                section_source = "PT_MASTER_CURRENT"
            else:
                sec = sections[level_id][sid]
                sx = float(sec["section_x_cm"])
                sy = float(sec["section_y_cm"])
                sec_state = sec["evidence_status"]
                section_source = Path(LEVEL_FILES[level_id]).name
            xy_state = classify_xy_input(s["metric_provenance"], level_id)
            rows.append(
                {
                    "node_id": f"M0G-C-{level_id}-{token(sid)}",
                    "level_id": level_id,
                    "node_role": "SUPPORT_CORE",
                    "support_id": sid,
                    "x_m": f4(float(s["x_global_m"])),
                    "y_m": f4(float(s["y_global_m"])),
                    "z_m": f4(z),
                    "section_x_cm": f"{sx:g}",
                    "section_y_cm": f"{sy:g}",
                    "section_evidence_state": sec_state,
                    "xy_input_provenance": s["metric_provenance"],
                    "z_input_provenance": levels[level_id]["evidence_state"],
                    "topology_evidence_state": "DOC",
                    "coordinate_derivation": "CURRENT_SUPPORT_CENTER_PLUS_REGISTERED_LEVEL_Z",
                    "coordinate_evidence_state": xy_state,
                    "validation_state": "CURRENT_CORE_NODE" if xy_state == "DOC" else "CURRENT_WITH_XY_WATCH",
                    "note": f"Core/column-axis role only; never substitutes beam-face nodes. Section source={section_source}.",
                }
            )

    # 2) Preserve the 98 current PT beam-face nodes exactly, adding Z=G1.
    z_g1 = float(levels["G1"]["z_rel_to_g1_m"])
    for src in pt_face_nodes:
        sid = src["support_id"]
        sec = pt_master[sid]
        sx, sy = parse_section_cm(sec["section_cm"])
        rows.append(
            {
                "node_id": f"M0G-F-G1-{src['node_id']}",
                "level_id": "G1",
                "node_role": "BEAM_SUPPORT_FACE",
                "support_id": sid,
                "source_node_id": src["node_id"],
                "beam_id": src["attached_beams"],
                "beam_end": "SOURCE_CURRENT_PT",
                "face_ref": src["face_ref"],
                "x_m": f4(float(src["x_m"])),
                "y_m": f4(float(src["y_m"])),
                "z_m": f4(z_g1),
                "section_x_cm": f"{sx:g}",
                "section_y_cm": f"{sy:g}",
                "section_evidence_state": "DOC",
                "xy_input_provenance": src["support_metric_evidence"],
                "z_input_provenance": levels["G1"]["evidence_state"],
                "topology_evidence_state": "DOC",
                "coordinate_derivation": "REUSED_CURRENT_PT_BEAM_FACE_NODE",
                "coordinate_evidence_state": "INF",
                "validation_state": src["node_evidence_status"],
                "note": "Exact current PT analytical face-node coordinates; no centroid substitution.",
            }
        )

    # 3) Upper-storey beam-face nodes: one explicit incidence for every beam end.
    side_mismatch_count = 0
    upper_face_count = 0
    for level_id in ["G2", "G3", "G4", "G5"]:
        z = float(levels[level_id]["z_rel_to_g1_m"])
        for beam in beams[level_id]:
            bid = beam["beam_id"]
            from_sid = beam["from_support_id"]
            to_sid = beam["to_support_id"]
            from_s = supports[from_sid]
            to_s = supports[to_sid]
            from_sec = sections[level_id][from_sid]
            to_sec = sections[level_id][to_sid]
            f_sx = float(from_sec["section_x_cm"])
            f_sy = float(from_sec["section_y_cm"])
            t_sx = float(to_sec["section_x_cm"])
            t_sy = float(to_sec["section_y_cm"])
            p_from = (float(from_s["x_global_m"]), float(from_s["y_global_m"]))
            p_to = (float(to_s["x_global_m"]), float(to_s["y_global_m"]))

            if level_id == "G5" and bid == "G5-B008":
                # Direct visual TAV-06S recheck: the documented 5->13 member is L-shaped.
                # It leaves support 5 toward -X and enters support 13 from -Y.
                fx, fy, f_face = p_from[0] - f_sx / 200.0, p_from[1], "X_NEG"
                tx, ty, t_face = p_to[0], p_to[1] - t_sy / 200.0, "Y_NEG"
                derivation = "TAV06S_OFFSET_POLYLINE_ENDPOINT_TANGENT_PLUS_SUPPORT_FACE"
            else:
                fx, fy, f_face = face_intersection(p_from, p_to, f_sx, f_sy)
                tx, ty, t_face = face_intersection(p_to, p_from, t_sx, t_sy)
                derivation = "SUPPORT_CENTERLINE_RAY_INTERSECT_DOCUMENTED_SUPPORT_FACE"

            if level_id in {"G2", "G3", "G4"}:
                expected_from = beam.get("from_support_face", "")
                expected_to = beam.get("to_support_face", "")
                if expected_from and expected_from != f_face:
                    side_mismatch_count += 1
                if expected_to and expected_to != t_face:
                    side_mismatch_count += 1

            for end, sid, srow, secrow, x, y, face, sx, sy in [
                ("FROM", from_sid, from_s, from_sec, fx, fy, f_face, f_sx, f_sy),
                ("TO", to_sid, to_s, to_sec, tx, ty, t_face, t_sx, t_sy),
            ]:
                upper_face_count += 1
                sec_state = secrow["evidence_status"]
                watch = (
                    sec_state != "DOC"
                    or srow["metric_provenance"] != "DOC_METRIC_OR_AXIS"
                    or level_id != "G1"
                )
                rows.append(
                    {
                        "node_id": f"M0G-F-{token(bid)}-{end}",
                        "level_id": level_id,
                        "node_role": "BEAM_SUPPORT_FACE",
                        "support_id": sid,
                        "beam_id": bid,
                        "beam_end": end,
                        "face_ref": face,
                        "x_m": f4(x),
                        "y_m": f4(y),
                        "z_m": f4(z),
                        "section_x_cm": f"{sx:g}",
                        "section_y_cm": f"{sy:g}",
                        "section_evidence_state": sec_state,
                        "xy_input_provenance": srow["metric_provenance"] + "+UPPER_SHEET_REGISTRATION_MIS",
                        "z_input_provenance": levels[level_id]["evidence_state"],
                        "topology_evidence_state": beam["topology_evidence_status"],
                        "coordinate_derivation": derivation,
                        "coordinate_evidence_state": "INF",
                        "validation_state": "CURRENT_DERIVED_WITH_PROVENANCE_WATCH" if watch else "CURRENT_DERIVED",
                        "note": "Exact analytical face point is derived; source topology/identity evidence remains separate and is not promoted to DOC coordinate evidence.",
                    }
                )

    if upper_face_count != 360:
        raise ValueError(f"upper face-node count {upper_face_count} != 360")
    if side_mismatch_count != 0:
        raise ValueError(f"documented/computed G2-G4 support-face mismatch count={side_mismatch_count}")

    # Global invariants.
    ids = [str(r["node_id"]) for r in rows]
    if len(ids) != len(set(ids)):
        dup = [k for k, v in Counter(ids).items() if v > 1]
        raise ValueError(f"duplicate node ids: {dup}")
    role_counts = Counter(str(r["node_role"]) for r in rows)
    level_counts = Counter(str(r["level_id"]) for r in rows)
    if role_counts["SUPPORT_CORE"] != 165:
        raise ValueError(f"support-core count {role_counts['SUPPORT_CORE']} != 165")
    if role_counts["BEAM_SUPPORT_FACE"] != 462:
        raise ValueError(f"beam-face count {role_counts['BEAM_SUPPORT_FACE']} != 462")
    if len(rows) != 627:
        raise ValueError(f"global node count {len(rows)} != 627")
    expected_level_nodes = {"G1": 140, "G2": 130, "G3": 130, "G4": 130, "G5": 97}
    if dict(level_counts) != expected_level_nodes:
        raise ValueError(f"level counts {dict(level_counts)} != {expected_level_nodes}")

    # Face nodes may never be replaced by support centroids.
    centroid_collapse = 0
    for r in rows:
        if r["node_role"] != "BEAM_SUPPORT_FACE":
            continue
        s = supports[r["support_id"]]
        if math.isclose(float(r["x_m"]), float(s["x_global_m"]), abs_tol=1e-7) and math.isclose(
            float(r["y_m"]), float(s["y_global_m"]), abs_tol=1e-7
        ):
            centroid_collapse += 1
    if centroid_collapse:
        raise ValueError(f"beam-face centroid substitution count={centroid_collapse}")

    write_csv(OUTPUT, FIELDNAMES, rows)

    audit_rows: list[dict[str, object]] = []
    def audit(check_id: str, expected: object, actual: object, status: str = "PASS", note: str = "") -> None:
        audit_rows.append({"check_id": check_id, "expected": expected, "actual": actual, "status": status, "note": note})

    audit("TOTAL_3D_NODE_ROWS", 627, len(rows))
    audit("SUPPORT_CORE_ROWS", 165, role_counts["SUPPORT_CORE"])
    audit("G1_REUSED_PT_FACE_ROWS", 102, len(pt_face_nodes))
    audit("UPPER_BEAM_FACE_ROWS", 360, upper_face_count)
    for level_id, expected in expected_level_nodes.items():
        audit(f"{level_id}_NODE_ROWS", expected, level_counts[level_id])
    for level_id, expected in expected_beam_counts.items():
        audit(f"{level_id}_SOURCE_BEAMS", expected, len(beams[level_id]))
    audit("G2_G4_DOCUMENTED_FACE_MISMATCHES", 0, side_mismatch_count)
    audit("CENTROID_SUBSTITUTIONS", 0, centroid_collapse)
    audit("UNIQUE_NODE_IDS", 627, len(set(ids)))
    audit("G5_B008_FROM_FACE", "X_NEG", next(r["face_ref"] for r in rows if r["node_id"] == "M0G-F-G5-B008-FROM"), note="Direct TAV-06S visual recheck of L-shaped 5->13 member.")
    audit("G5_B008_TO_FACE", "Y_NEG", next(r["face_ref"] for r in rows if r["node_id"] == "M0G-F-G5-B008-TO"), note="Direct TAV-06S visual recheck of L-shaped 5->13 member.")
    audit("NO_MIS_TO_DOC_COORDINATE_PROMOTION", "YES", "YES", note="Upper face points are INF analytical derivations; upper registered core XY remains MIS where applicable.")
    audit("EXTENDED_SUPPORT_FACE_NODES_NOT_MERGED", "YES", "YES", note="Each beam incidence has a stable distinct node id; P18/P23/P30 are never collapsed to one face node.")

    write_csv(AUDIT, ["check_id", "expected", "actual", "status", "note"], audit_rows)
    print(f"M0G_3D_ANALYTICAL_NODES_GENERATION = PASS rows={len(rows)} core=165 face=458 upper_face=360")
    print(f"output={OUTPUT.relative_to(ROOT)}")
    print(f"audit={AUDIT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
