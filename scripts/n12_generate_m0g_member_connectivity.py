#!/usr/bin/env python3
from __future__ import annotations

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAN = ROOT / "data" / "canonical"
AUD = ROOT / "analysis" / "automation"
OUT = CAN / "M0G_MEMBER_CONNECTIVITY_CURRENT_v1.csv"
AUDIT = AUD / "M0G_ASSEMBLE_MEMBER_CONNECTIVITY_AUDIT_v1.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def f4(value: float) -> str:
    return f"{value:.4f}"


nodes = read_csv(CAN / "M0G_ANALYTICAL_NODES_3D_CURRENT_v1.csv")
node_by_id = {r["node_id"]: r for r in nodes}
core: dict[tuple[str, str], str] = {}
face_by_beam_support: dict[tuple[str, str, str], list[str]] = {}
face_by_beam_end: dict[tuple[str, str, str], list[str]] = {}

for r in nodes:
    role = r["node_role"]
    if role == "SUPPORT_CORE":
        key = (r["level_id"], r["support_id"])
        if key in core:
            raise SystemExit(f"duplicate core node {key}")
        core[key] = r["node_id"]
    elif role == "BEAM_SUPPORT_FACE":
        face_by_beam_support.setdefault((r["level_id"], r["beam_id"], r["support_id"]), []).append(r["node_id"])
        face_by_beam_end.setdefault((r["level_id"], r["beam_id"], r["beam_end"]), []).append(r["node_id"])


def one(mapping: dict[tuple[str, str, str], list[str]], key: tuple[str, str, str]) -> str:
    vals = mapping.get(key, [])
    if len(vals) != 1:
        raise SystemExit(f"expected exactly one node for {key}, got {vals}")
    return vals[0]


def node_distance(a: str, b: str) -> float:
    ra, rb = node_by_id[a], node_by_id[b]
    dx = float(rb["x_m"]) - float(ra["x_m"])
    dy = float(rb["y_m"]) - float(ra["y_m"])
    dz = float(rb["z_m"]) - float(ra["z_m"])
    return math.sqrt(dx * dx + dy * dy + dz * dz)


members: list[dict[str, object]] = []

# --- G1 effective beams: current base + explicit G6 patch semantics.
pt_base = read_csv(CAN / "PT_VECTOR_BEAMS_v2.csv")
pt_patch = read_csv(CAN / "PT_VECTOR_BEAMS_G6_PATCH_v1.csv")
reopen_rows = read_csv(CAN / "M0G_REOPEN_PT_BEAM_EVIDENCE_v1.csv")
reopen_sections = {r["beam_id"]: r for r in reopen_rows}
revoked = {r["beam_id"] for r in pt_patch if r["action"] == "REVOKE"}
pt_effective = [
    r for r in pt_base
    if r["beam_id"] not in revoked and r.get("vector_status") != "PROVENANCE_ONLY"
]
for p in pt_patch:
    if p["action"] == "ADD":
        pt_effective.append({
            "beam_id": p["beam_id"],
            "support_i": p["support_i"],
            "support_j": p["support_j"],
            "geometry_role": "PATCH_DIRECT_SOURCE",
            "section_hint": reopen_sections.get(p["beam_id"], {}).get("section_cm", ""),
            "evidence_basis": "DOC_DIRECT_SOURCE_PATCH",
            "orientation": p["orientation"],
            "vector_status": p["vector_status"],
            "note": p["note"],
        })

if len(pt_effective) != 51:
    raise SystemExit(f"PT effective beam count != 51: {len(pt_effective)}")

for b in pt_effective:
    bid = b["beam_id"]
    si, sj = b["support_i"], b["support_j"]
    ni = one(face_by_beam_support, ("G1", bid, si))
    nj = one(face_by_beam_support, ("G1", bid, sj))
    members.append({
        "member_id": f"M0G-M-G1-{bid}",
        "member_class": "ORDINARY_BEAM",
        "source_member_id": bid,
        "storey_id": "G1",
        "from_level": "G1",
        "to_level": "G1",
        "support_i": si,
        "support_j": sj,
        "node_i": ni,
        "node_j": nj,
        "geometric_length_m": f4(node_distance(ni, nj)),
        "section_i_cm": "",
        "section_j_cm": "",
        "section_cm": b.get("section_hint", ""),
        "section_evidence_i": "",
        "section_evidence_j": "",
        "section_evidence": "DOC" if b.get("section_hint") else "ND",
        "topology_evidence": b.get("evidence_basis", "DOC_EFFECTIVE_PT_TOPOLOGY"),
        "source_ledger": "data/canonical/PT_VECTOR_BEAMS_v2.csv+data/canonical/PT_VECTOR_BEAMS_G6_PATCH_v1.csv",
        "source_record_class": "EFFECTIVE_PT_BEAM",
        "connectivity_evidence": "INF_FROM_CANONICAL_FACE_NODES",
        "validation_state": "CURRENT_WITH_PROVENANCE",
        "usage_rule": "ORDINARY_STRUCTURAL_MEMBER",
        "note": b.get("note", ""),
    })

# --- G2-G5 ordinary beams: topology index selects records; source ledger remains field authority.
index_rows = read_csv(CAN / "STOREY_BEAM_TOPOLOGY_CURRENT_v1.csv")
if len(index_rows) != 180:
    raise SystemExit(f"upper ordinary beam index count != 180: {len(index_rows)}")
ledger_cache: dict[str, dict[str, dict[str, str]]] = {}
for idx in index_rows:
    rel = idx["source_ledger"]
    if rel not in ledger_cache:
        rows = read_csv(ROOT / rel)
        ledger_cache[rel] = {r["beam_id"]: r for r in rows}
    src = ledger_cache[rel].get(idx["beam_id"])
    if not src:
        raise SystemExit(f"missing source beam {idx['beam_id']} in {rel}")
    level, bid = idx["storey_id"], idx["beam_id"]
    ni = one(face_by_beam_end, (level, bid, "FROM"))
    nj = one(face_by_beam_end, (level, bid, "TO"))
    members.append({
        "member_id": f"M0G-M-{bid}",
        "member_class": "ORDINARY_BEAM",
        "source_member_id": bid,
        "storey_id": level,
        "from_level": level,
        "to_level": level,
        "support_i": src["from_support_id"],
        "support_j": src["to_support_id"],
        "node_i": ni,
        "node_j": nj,
        "geometric_length_m": f4(node_distance(ni, nj)),
        "section_i_cm": "",
        "section_j_cm": "",
        "section_cm": src.get("section_cm", ""),
        "section_evidence_i": "",
        "section_evidence_j": "",
        "section_evidence": src.get("section_evidence_status", "ND"),
        "topology_evidence": src.get("topology_evidence_status", "DOC"),
        "source_ledger": rel,
        "source_record_class": idx["record_class"],
        "connectivity_evidence": "INF_FROM_CANONICAL_FACE_NODES",
        "validation_state": "CURRENT_WITH_SECTION_WATCH" if src.get("section_evidence_status") == "ND" else "CURRENT_WITH_PROVENANCE",
        "usage_rule": "ORDINARY_STRUCTURAL_MEMBER",
        "note": src.get("note", ""),
    })

# --- Vertical columns: endpoints are support-core nodes on adjacent structural planes.
columns = read_csv(CAN / "VERTICAL_COLUMN_SEGMENTS_CURRENT_v1.csv")
if len(columns) != 127:
    raise SystemExit(f"vertical column segment count != 127: {len(columns)}")
for c in columns:
    sid = c["support_id"]
    fl, tl = c["from_level"], c["to_level"]
    ni = core.get((fl, sid))
    nj = core.get((tl, sid))
    if not ni or not nj:
        raise SystemExit(f"missing core endpoint for {c['segment_id']} support={sid} {fl}->{tl}")
    members.append({
        "member_id": f"M0G-M-{c['segment_id']}",
        "member_class": "COLUMN_SEGMENT",
        "source_member_id": c["segment_id"],
        "storey_id": f"{fl}-{tl}",
        "from_level": fl,
        "to_level": tl,
        "support_i": sid,
        "support_j": sid,
        "node_i": ni,
        "node_j": nj,
        "geometric_length_m": f4(node_distance(ni, nj)),
        "section_i_cm": c["from_section_cm"],
        "section_j_cm": c["to_section_cm"],
        "section_cm": "",
        "section_evidence_i": c["from_section_evidence"],
        "section_evidence_j": c["to_section_evidence"],
        "section_evidence": c["section_transition_class"],
        "topology_evidence": c["continuity_evidence"],
        "source_ledger": "data/canonical/VERTICAL_COLUMN_SEGMENTS_CURRENT_v1.csv",
        "source_record_class": "VERTICAL_COLUMN_SEGMENT",
        "connectivity_evidence": "DOC_CONTINUITY_PLUS_INF_CORE_NODE_BINDING",
        "validation_state": c["validation_state"],
        "usage_rule": "ORDINARY_STRUCTURAL_MEMBER",
        "note": c.get("note", ""),
    })

fields = [
    "member_id", "member_class", "source_member_id", "storey_id", "from_level", "to_level",
    "support_i", "support_j", "node_i", "node_j", "geometric_length_m",
    "section_i_cm", "section_j_cm", "section_cm", "section_evidence_i", "section_evidence_j",
    "section_evidence", "topology_evidence", "source_ledger", "source_record_class",
    "connectivity_evidence", "validation_state", "usage_rule", "note",
]
write_csv(OUT, members, fields)

# --- Deterministic audit.
beam_members = [m for m in members if m["member_class"] == "ORDINARY_BEAM"]
column_members = [m for m in members if m["member_class"] == "COLUMN_SEGMENT"]
by_storey = {g: sum(1 for m in beam_members if m["storey_id"] == g) for g in ["G1", "G2", "G3", "G4", "G5"]}
member_ids = [m["member_id"] for m in members]
node_pairs = [tuple(sorted((str(m["node_i"]), str(m["node_j"])))) for m in members]
beam_face_role_fail = 0
column_core_role_fail = 0
zero_length = 0
for m in members:
    if float(m["geometric_length_m"]) <= 0.0:
        zero_length += 1
    if m["member_class"] == "ORDINARY_BEAM":
        if node_by_id[str(m["node_i"])]["node_role"] != "BEAM_SUPPORT_FACE" or node_by_id[str(m["node_j"])]["node_role"] != "BEAM_SUPPORT_FACE":
            beam_face_role_fail += 1
    else:
        if node_by_id[str(m["node_i"])]["node_role"] != "SUPPORT_CORE" or node_by_id[str(m["node_j"])]["node_role"] != "SUPPORT_CORE":
            column_core_role_fail += 1

roof_absent = {"1", "8", "9", "16", "17", "24", "31", "32", "33"}
invalid_g4g5 = sum(1 for c in columns if c["from_level"] == "G4" and c["to_level"] == "G5" and c["support_id"] in roof_absent)
terrace_vertical = sum(1 for c in columns if c["support_id"] in {"a", "b", "c", "d"})
roof_special_like = sum(1 for m in members if "RIDGE" in str(m["source_member_id"]) or "GRONDA" in str(m["source_member_id"]))
g5_b036 = sum(1 for m in members if m["source_member_id"] == "G5-B036")
revoked_pt = sum(1 for m in members if m["source_member_id"] in {"B-029", "B-037", "B-044"})
nd_g5_sections = sum(1 for m in members if m["storey_id"] == "G5" and m["member_class"] == "ORDINARY_BEAM" and m["section_evidence"] == "ND")
watched_columns = sum(1 for m in column_members if m["validation_state"] == "CURRENT_WITH_SECTION_WATCH")

checks = [
    ("TOTAL_MEMBER_ROWS", 358, len(members), ""),
    ("ORDINARY_BEAM_ROWS", 231, len(beam_members), "51 G1 + 180 G2-G5"),
    ("COLUMN_SEGMENT_ROWS", 127, len(column_members), "Exact vertical ledger"),
    ("G1_BEAMS", 51, by_storey["G1"], "Effective PT topology"),
    ("G2_BEAMS", 48, by_storey["G2"], ""),
    ("G3_BEAMS", 48, by_storey["G3"], ""),
    ("G4_BEAMS", 48, by_storey["G4"], ""),
    ("G5_BEAMS", 36, by_storey["G5"], ""),
    ("UNIQUE_MEMBER_IDS", 358, len(set(member_ids)), ""),
    ("DUPLICATE_UNDIRECTED_NODE_PAIRS", 0, len(node_pairs) - len(set(node_pairs)), "Rigid links are not structural members and are absent here."),
    ("BEAM_ENDPOINT_ROLE_FAILURES", 0, beam_face_role_fail, "Every beam terminates on a beam-support face node."),
    ("COLUMN_ENDPOINT_ROLE_FAILURES", 0, column_core_role_fail, "Every column terminates on a support-core node."),
    ("ZERO_LENGTH_MEMBERS", 0, zero_length, ""),
    ("REVOKED_OR_DUPLICATE_PT_BEAMS_PRESENT", 0, revoked_pt, "B-029, B-037, B-044 excluded."),
    ("G5_B036_COUNT", 1, g5_b036, "19-26 oblique beam counted once."),
    ("ROOF_RIDGE_GRONDA_ORDINARY_MEMBERS", 0, roof_special_like, "Roof special geometry remains separate."),
    ("TERRACE_A_D_VERTICAL_SEGMENTS", 0, terrace_vertical, "a-d terminate at G1."),
    ("ROOF_ABSENT_G4_G5_COLUMNS", 0, invalid_g4g5, "No unsupported extrusion to G5."),
    ("G5_ND_SECTION_BEAMS_RETAINED", 17, nd_g5_sections, "Connectivity does not fill missing G5 sections."),
    ("COLUMN_SECTION_WATCH_SEGMENTS_RETAINED", 4, watched_columns, "G3 support section watches propagate without repair."),
]
audit_rows: list[dict[str, object]] = []
fail = False
for cid, expected, actual, note in checks:
    ok = expected == actual
    fail = fail or not ok
    audit_rows.append({"check_id": cid, "expected": expected, "actual": actual, "status": "PASS" if ok else "FAIL", "note": note})
write_csv(AUDIT, audit_rows, ["check_id", "expected", "actual", "status", "note"])

if fail:
    raise SystemExit("M0G member connectivity audit failed")
print(f"M0G_MEMBER_CONNECTIVITY = PASS members={len(members)} beams={len(beam_members)} columns={len(column_members)}")
