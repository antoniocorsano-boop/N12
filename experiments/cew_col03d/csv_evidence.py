from __future__ import annotations

import csv
import hashlib
import io
from typing import Any


def parse_csv_member(artifact_name: str, data: bytes) -> dict[str, Any]:
    try:
        text = data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"CSV_ENCODING_INVALID:{artifact_name}") from exc

    reader = csv.reader(io.StringIO(text, newline=""), delimiter=";")
    try:
        rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"CSV_PARSE_FAILED:{artifact_name}") from exc

    if not rows or not rows[0]:
        raise ValueError(f"CSV_HEADER_MISSING:{artifact_name}")
    headers = list(rows[0])
    if any(header == "" for header in headers) or len(set(headers)) != len(headers):
        raise ValueError(f"CSV_HEADER_INVALID:{artifact_name}")

    records: list[dict[str, Any]] = []
    for source_row_number, row in enumerate(rows[1:], start=2):
        if not row or (len(row) == 1 and row[0] == ""):
            continue
        if len(row) != len(headers):
            raise ValueError(f"CSV_ROW_WIDTH_MISMATCH:{artifact_name}:row={source_row_number}")
        records.append(
            {
                "source_row_number": source_row_number,
                "values": dict(zip(headers, row, strict=True)),
            }
        )

    return {
        "artifact_name": artifact_name,
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "encoding": "utf-8-sig",
        "delimiter": ";",
        "headers": headers,
        "row_count": len(records),
        "records": records,
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "promotion_authorized": False,
        "structural_identity_authorized": False,
    }
