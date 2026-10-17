#!/usr/bin/env python3
from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "data" / "canonical"

REQUIRED = [
    "PT_PIXEL_SUPPORT_REGISTRY_v1.csv",
    "PT_GCP_METRIC_NETWORK_v1.csv",
    "PT_METRIC_SUPPORT_CENTERS_v1.csv",
    "PT_METRIC_NETWORK_RESIDUALS_v1.csv",
    "PT_RASTER_TO_METRIC_DIAGNOSTIC_v1.csv",
    "PT_VECTOR_SUPPORTS_v1.csv",
    "PT_VECTOR_BEAMS_v1.csv",
    "PT_ANALYTICAL_NODES_v1.csv",
    "PT_OVERLAY_QA_v1.csv",
]

PHASES = [
    ("G1", "PT_PIXEL_SUPPORT_REGISTRY_v1.csv"),
    ("G2", "PT_GCP_METRIC_NETWORK_v1.csv"),
    ("G3a", "PT_METRIC_SUPPORT_CENTERS_v1.csv"),
    ("G3b", "PT_METRIC_NETWORK_RESIDUALS_v1.csv"),
    ("G4", "PT_RASTER_TO_METRIC_DIAGNOSTIC_v1.csv"),
    ("G5", "PT_VECTOR_SUPPORTS_v1.csv"),
    ("G6", "PT_VECTOR_BEAMS_v1.csv"),
    ("G7", "PT_ANALYTICAL_NODES_v1.csv"),
    ("G9", "PT_OVERLAY_QA_v1.csv"),
]

EXPECTED_SUPPORT_IDS = {str(i) for i in range(1, 34)} | {"22'", "a", "b", "c", "d"}
PIXEL_REQUIRED_FIELDS = {
    "support_id",
    "u_native_px",
    "v_native_px",
    "registration_state",
    "canonical_status",
    "may_feed_metric_network",
}


def existing(name):
    return (CANON / name).exists()


def read_csv(path):
    try:
        with path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def nonempty_csv(path):
    return bool(read_csv(path))


def pixel_registry_state():
    path = CANON / "PT_PIXEL_SUPPORT_REGISTRY_v1.csv"
    if not path.exists():
        return False, "missing", set(), EXPECTED_SUPPORT_IDS
    rows = read_csv(path)
    if not rows:
        return False, "empty_or_invalid", set(), EXPECTED_SUPPORT_IDS
    if not PIXEL_REQUIRED_FIELDS.issubset(rows[0].keys()):
        missing_fields = PIXEL_REQUIRED_FIELDS - set(rows[0].keys())
        return False, f"schema_missing:{','.join(sorted(missing_fields))}", set(), EXPECTED_SUPPORT_IDS

    valid = set()
    for row in rows:
        sid = (row.get("support_id") or "").strip()
        try:
            float(row.get("u_native_px", ""))
            float(row.get("v_native_px", ""))
        except (TypeError, ValueError):
            continue
        if (
            sid in EXPECTED_SUPPORT_IDS
            and (row.get("canonical_status") or "").strip() == "CURRENT"
            and (row.get("may_feed_metric_network") or "").strip().upper() == "YES"
        ):
            valid.add(sid)

    missing = EXPECTED_SUPPORT_IDS - valid
    if missing:
        return False, f"partial:{len(valid)}/{len(EXPECTED_SUPPORT_IDS)}", valid, missing
    return True, "complete", valid, set()


def phase_ok(phase, name):
    if phase == "G1":
        ok, _, _, _ = pixel_registry_state()
        return ok
    return existing(name) and nonempty_csv(CANON / name)


def status():
    print("PT Raster Grid Reconstructor")
    print("Master geometry authority: SUSPENDED until gate PASS\n")
    next_phase = None
    for phase, name in PHASES:
        ok = phase_ok(phase, name)
        extra = ""
        if phase == "G1":
            _, detail, valid, missing = pixel_registry_state()
            extra = f" [{detail}]"
            if missing:
                extra += f" missing={','.join(sorted(missing, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x)))}"
        print(f"{phase:>3}  {'PASS' if ok else 'OPEN':<4}  {name}{extra}")
        if not ok and next_phase is None:
            next_phase = (phase, name)
    if next_phase:
        print(f"\nNEXT: {next_phase[0]} -> complete/validate {next_phase[1]}")
    else:
        print("\nAll minimum artifacts exist and G1 coverage is complete. Run validate before Master promotion.")


def validate():
    errors = []

    pixel_ok, pixel_detail, valid_supports, missing_supports = pixel_registry_state()
    if not pixel_ok:
        errors.append(f"PIXEL_REGISTRY_INCOMPLETE {pixel_detail}")
        if missing_supports:
            errors.append("PIXEL_REGISTRY missing supports: " + ",".join(sorted(missing_supports, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))))

    for name in REQUIRED[1:]:
        p = CANON / name
        if not p.exists():
            errors.append(f"MISSING {name}")
        elif not nonempty_csv(p):
            errors.append(f"EMPTY_OR_INVALID {name}")

    analytical = CANON / "PT_ANALYTICAL_NODES_v1.csv"
    if analytical.exists() and nonempty_csv(analytical):
        rows = read_csv(analytical)
        required_fields = {"analytical_node_id", "support_id", "beam_id", "x_m", "y_m"}
        if not required_fields.issubset(rows[0].keys()):
            errors.append("ANALYTICAL_NODES missing required node/support/beam coordinates")

    if errors:
        print("PT_MASTER_GEOMETRY_GATE = FAIL")
        for e in errors:
            print("-", e)
        return 1

    print("PT_MASTER_GEOMETRY_GATE = READY_FOR_SEMANTIC_QA")
    print(f"G1 supports complete: {len(valid_supports)}/{len(EXPECTED_SUPPORT_IDS)}")
    print("Automatic validation checks artifact presence/shape and full support coverage.")
    print("Final PASS still requires semantic raster overlay review per SKILL.md.")
    return 0


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        status()
        return 0
    if cmd == "validate":
        return validate()
    print("Usage: runner.py [status|validate]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
