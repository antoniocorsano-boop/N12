from __future__ import annotations

import csv
import io
import re
from typing import Any

_SUPPORT_RE = re.compile(r"^([1-9][0-9]?)(?:')?$")
_APOSTROPHES = {"’", "‘", "`", "´"}


def normalize_support_identifier(text: str) -> str | None:
    value = str(text).strip()
    for mark in _APOSTROPHES:
        value = value.replace(mark, "'")
    match = _SUPPORT_RE.fullmatch(value)
    if match is None:
        return None
    number = match.group(1)
    suffix = "'" if value.endswith("'") else ""
    return f"{number}{suffix}"


def parse_support_like_tsv(
    tsv_text: str, *, min_confidence: float = 25.0
) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
    required = {"text", "conf", "left", "top", "width", "height"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise ValueError("COL01_TESSERACT_TSV_SCHEMA_INVALID")

    observations: list[dict[str, Any]] = []
    for row in reader:
        raw_text = str(row.get("text") or "").strip()
        normalized = normalize_support_identifier(raw_text)
        if normalized is None:
            continue
        try:
            confidence = float(row["conf"])
            left = int(row["left"])
            top = int(row["top"])
            width = int(row["width"])
            height = int(row["height"])
        except (TypeError, ValueError, KeyError):
            continue
        if confidence < float(min_confidence):
            continue
        if width <= 0 or height <= 0:
            continue
        observations.append(
            {
                "normalized_id": normalized,
                "text": raw_text,
                "confidence": confidence,
                "bbox": {
                    "x": left,
                    "y": top,
                    "width": width,
                    "height": height,
                },
            }
        )

    observations.sort(
        key=lambda item: (
            int(item["bbox"]["y"]),
            int(item["bbox"]["x"]),
            str(item["normalized_id"]),
            str(item["text"]),
        )
    )
    return observations
