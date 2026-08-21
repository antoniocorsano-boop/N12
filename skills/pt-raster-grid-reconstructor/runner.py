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


def existing(name):
    return (CANON / name).exists()


def nonempty_csv(path):
    try:
        with path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        return bool(rows)
    except Exception:
        return False


def status():
    print("PT Raster Grid Reconstructor")
    print("Master geometry authority: SUSPENDED until gate PASS\n")
    next_phase = None
    for phase, name in PHASES:
        ok = existing(name) and nonempty_csv(CANON / name)
        print(f"{phase:>3}  {'PASS' if ok else 'OPEN':<4}  {name}")
        if not ok and next_phase is None:
            next_phase = (phase, name)
    if next_phase:
        print(f"\nNEXT: {next_phase[0]} -> create/validate {next_phase[1]}")
    else:
        print("\nAll minimum artifacts exist. Run validate before Master promotion.")


def validate():
    errors = []
    for name in REQUIRED:
        p = CANON / name
        if not p.exists():
            errors.append(f"MISSING {name}")
        elif not nonempty_csv(p):
            errors.append(f"EMPTY_OR_INVALID {name}")

    pixel = CANON / "PT_PIXEL_SUPPORT_REGISTRY_v1.csv"
    if pixel.exists() and nonempty_csv(pixel):
        with pixel.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        required_fields = {"support_id", "u_center_px", "v_center_px"}
        if not required_fields.issubset(rows[0].keys()):
            errors.append("PIXEL_REGISTRY missing support_id/u_center_px/v_center_px")

    analytical = CANON / "PT_ANALYTICAL_NODES_v1.csv"
    if analytical.exists() and nonempty_csv(analytical):
        with analytical.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        required_fields = {"analytical_node_id", "support_id", "beam_id", "x_m", "y_m"}
        if not required_fields.issubset(rows[0].keys()):
            errors.append("ANALYTICAL_NODES missing required node/support/beam coordinates")

    if errors:
        print("PT_MASTER_GEOMETRY_GATE = FAIL")
        for e in errors:
            print("-", e)
        return 1

    print("PT_MASTER_GEOMETRY_GATE = READY_FOR_SEMANTIC_QA")
    print("Automatic validation checks artifact presence/shape only.")
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
