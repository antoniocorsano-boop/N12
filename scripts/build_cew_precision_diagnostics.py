#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data/canonical/STOREY_SUPPORT_XY_REGISTRATION_v1.csv"
SUPPORTS = ROOT / "data/canonical/VERTICAL_SUPPORT_LINES_CURRENT_v1.csv"
OUT_DIR = ROOT / "artifacts/cew_precision_registration"
OUT_CSV = OUT_DIR / "TAV05S_G4_GLOBAL_PREDICTIONS_v1.csv"
OUT_JSON = OUT_DIR / "TAV05S_G4_PRECISION_DIAGNOSTICS_v1.json"


def load_registration() -> dict[str, str]:
    with REG.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    row = next((r for r in rows if r.get("sheet_id") == "TAV-05S" and r.get("level_id") == "G4"), None)
    if not row:
        raise SystemExit("missing TAV-05S/G4 registration")
    if row.get("validation_state") != "CROSS_VALIDATED":
        raise SystemExit("TAV-05S/G4 registration must be CROSS_VALIDATED")
    if row.get("source_frame") != "ROT90_CCW_300DPI":
        raise SystemExit("unexpected source frame")
    return row


def inverse_affine(row: dict[str, str], x: float, y: float) -> tuple[float, float]:
    a1 = float(row["metric_x_from_u"])
    a2 = float(row["metric_x_from_v"])
    a0 = float(row["metric_x_offset"])
    b1 = float(row["metric_y_from_u"])
    b2 = float(row["metric_y_from_v"])
    b0 = float(row["metric_y_offset"])
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-12:
        raise SystemExit("non-invertible registration")
    dx, dy = x - a0, y - b0
    u = (dx * b2 - a2 * dy) / det
    v = (a1 * dy - dx * b1) / det
    return u, v


def registration_to_native(row: dict[str, str], u: float, v: float) -> tuple[float, float, int, int]:
    reg_w = int(row["frame_width_px"])
    reg_h = int(row["frame_height_px"])
    native_w, native_h = reg_h, reg_w
    x_native = native_w - v
    y_native = u
    if not (0 <= x_native <= native_w and 0 <= y_native <= native_h):
        raise SystemExit(f"mapped point outside native DZI: {(x_native, y_native)}")
    return x_native, y_native, native_w, native_h


def main() -> int:
    reg = load_registration()
    with SUPPORTS.open(newline="", encoding="utf-8") as fh:
        supports = [r for r in csv.DictReader(fh) if r.get("g4_present") == "PRESENT"]
    if len(supports) != 34:
        raise SystemExit(f"expected 34 G4 supports, got {len(supports)}")

    rows: list[dict[str, object]] = []
    for s in supports:
        x = float(s["x_global_m"])
        y = float(s["y_global_m"])
        u, v = inverse_affine(reg, x, y)
        xn, yn, nw, nh = registration_to_native(reg, u, v)
        rows.append({
            "support_id": s["support_id"],
            "sheet_id": "TAV-05S",
            "level_id": "G4",
            "common_x_m": f"{x:.4f}",
            "common_y_m": f"{y:.4f}",
            "global_predicted_native_x_px": f"{xn:.3f}",
            "global_predicted_native_y_px": f"{yn:.3f}",
            "snapped_native_x_px": "",
            "snapped_native_y_px": "",
            "residual_dx_px": "",
            "residual_dy_px": "",
            "residual_norm_px": "",
            "nearest_structural_gcp_distance_px": "",
            "local_registration_id": "",
            "document_snap_method": "",
            "locator_state": "REGISTERED_GLOBAL_NEEDS_LOCAL_QA",
            "global_registration_state": reg["validation_state"],
            "global_registration_method": reg["registration_method"],
            "navigation_only": "true",
            "structural_identity_authorized": "false",
            "canonical_geometry_authorized": "false",
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "schema_version": "1.0",
        "source": "TAV-05S",
        "level": "G4",
        "global_registration_state": reg["validation_state"],
        "source_frame": reg["source_frame"],
        "native_dzi_frame_px": [int(reg["frame_height_px"]), int(reg["frame_width_px"])],
        "global_registration_inlier_count": int(reg["inlier_count"]),
        "global_registration_preview_rms_px": float(reg["qa_rms_px_preview"]),
        "support_count": len(rows),
        "structural_gcp_count": 0,
        "snapped_locator_count": 0,
        "human_verified_locator_count": 0,
        "residual_distribution_available": False,
        "residual_threshold_frozen": False,
        "current_locator_state": "REGISTERED_GLOBAL_NEEDS_LOCAL_QA",
        "next_required_action": "CAPTURE_STRUCTURAL_GCP_AND_DOCUMENT_SNAPS",
        "authority_effect": "NONE",
        "canonical_write_authorized": False,
        "project_material_ready": False,
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("CEW_PR0_PRECISION_DIAGNOSTICS = BUILT")
    print(f"GLOBAL_PREDICTIONS = {len(rows)}/34")
    print("STRUCTURAL_GCP = 0")
    print("RESIDUAL_DISTRIBUTION = NOT_YET_AVAILABLE")
    print("LOCATOR_STATE = REGISTERED_GLOBAL_NEEDS_LOCAL_QA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
