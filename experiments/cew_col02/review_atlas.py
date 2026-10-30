from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def _pad_panel_to_width(panel: np.ndarray, width: int) -> np.ndarray:
    if panel.shape[1] >= width:
        return panel
    channels = 1 if panel.ndim == 2 else panel.shape[2]
    value: Any = 255 if channels == 1 else tuple([255] * channels)
    return cv2.copyMakeBorder(
        panel,
        0,
        0,
        0,
        width - panel.shape[1],
        cv2.BORDER_CONSTANT,
        value=value,
    )


def rebuild_target_explicit_atlas(audit_json: Path | str) -> Path:
    audit_path = Path(audit_json)
    root = audit_path.parent
    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    panels: list[np.ndarray] = []

    for entry in payload.get("review_panels", []):
        source = cv2.imread(str(root / entry["source_only_crop"]), cv2.IMREAD_GRAYSCALE)
        overlay = cv2.imread(str(root / entry["overlay_crop"]), cv2.IMREAD_COLOR)
        if source is None or overlay is None:
            raise RuntimeError(f"missing review image for {entry.get('panel_id')}")
        source_bgr = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
        if source_bgr.shape[:2] != overlay.shape[:2]:
            raise RuntimeError(f"source/overlay shape mismatch for {entry.get('panel_id')}")

        pair = cv2.hconcat([source_bgr, overlay])
        header = np.full((74, pair.shape[1], 3), 255, dtype=np.uint8)
        cv2.putText(
            header,
            f"{entry['panel_id']} | {entry['candidate_id']} | {entry['binding_state']}",
            (12, 29),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            header,
            "LEFT=source only | RIGHT=machine footprint + exact OCR targets | choose prototype only if whole footprint is correct",
            (12, 56),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
        panels.append(cv2.vconcat([header, pair]))

    if panels:
        max_width = max(panel.shape[1] for panel in panels)
        atlas = cv2.vconcat([_pad_panel_to_width(panel, max_width) for panel in panels])
    else:
        atlas = np.full((180, 1200, 3), 255, dtype=np.uint8)
        cv2.putText(
            atlas,
            "CEW-COL-02: no neutral footprint proposals available for prototype selection",
            (25, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )

    output = root / "col02-prototype-selection-atlas.png"
    if not cv2.imwrite(str(output), atlas):
        raise RuntimeError(f"cannot write {output}")
    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("audit_json")
    args = parser.parse_args()
    print(rebuild_target_explicit_atlas(args.audit_json))
