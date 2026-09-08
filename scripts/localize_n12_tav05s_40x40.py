#!/usr/bin/env python3
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"
SOURCE_PATH = "archive/documentazione_originaria/tavola 5.pdf"
EXPECTED_SHA256 = "2143dbcfb101c7a83d0c5c7a59a11ceabdaf7d8b2568a7aeeae61fa60e66f580"
OUT = ROOT / "artifacts" / "n12_tav05s_40x40_native_text_locator.json"
TARGET = "40x40"


def fail(msg: str) -> None:
    print(f"N12_TAV05S_40X40_LOCALIZATION_FAIL: {msg}")
    raise SystemExit(1)


def materialize_source(dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    spec = f"{SOURCE_COMMIT}:{SOURCE_PATH}"
    proc = subprocess.run(["git", "show", spec], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        fail(f"cannot materialize immutable source {spec}: {proc.stderr.decode('utf-8', errors='replace')}")
    dst.write_bytes(proc.stdout)


def normalize(text: str) -> str:
    s = text.replace("×", "x").replace("X", "x")
    s = re.sub(r"\s+", "", s)
    return s


def bbox_norm(rect, page_rect):
    return [
        round(rect.x0 / page_rect.width, 9),
        round(rect.y0 / page_rect.height, 9),
        round(rect.x1 / page_rect.width, 9),
        round(rect.y1 / page_rect.height, 9),
    ]


def main() -> int:
    temp_pdf = ROOT / ".tmp" / "n12_tav05s_source.pdf"
    materialize_source(temp_pdf)
    digest = hashlib.sha256(temp_pdf.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(f"source digest mismatch: {digest}")

    doc = fitz.open(temp_pdf)
    if len(doc) != 1:
        fail(f"expected one-page TAV-05S, found {len(doc)}")
    page = doc[0]
    words = page.get_text("words", sort=True)

    hits = []
    for word in words:
        x0, y0, x1, y1, text, block_no, line_no, word_no = word[:8]
        if normalize(str(text)) == TARGET:
            r = fitz.Rect(x0, y0, x1, y1)
            hits.append({
                "hit_index": len(hits),
                "raw_text": str(text),
                "normalized_text": TARGET,
                "bbox_pdf_points": [round(x0, 6), round(y0, 6), round(x1, 6), round(y1, 6)],
                "bbox_normalized_0_1": bbox_norm(r, page.rect),
                "block_no": int(block_no),
                "line_no": int(line_no),
                "word_no": int(word_no),
            })

    result = {
        "schema": "N12_TAV05S_NATIVE_TOKEN_LOCATOR_v1",
        "source_version_id": "CEW-N12-SRC-TAV05S-V2143DBCF",
        "source_commit": SOURCE_COMMIT,
        "source_path": SOURCE_PATH,
        "source_sha256": digest,
        "page_id": "CEW-N12-PAGE-TAV05S-P001",
        "page_index": 0,
        "page_rect_pdf_points": [round(page.rect.x0, 6), round(page.rect.y0, 6), round(page.rect.x1, 6), round(page.rect.y1, 6)],
        "extractor": "PyMuPDF-native-text",
        "extractor_version": fitz.VersionBind,
        "target": TARGET,
        "hit_count": len(hits),
        "hits": hits,
        "semantic_authority": "NONE",
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not hits:
        print("N12_TAV05S_40X40_NATIVE_TEXT_NOT_FOUND")
        return 2
    print(f"N12_TAV05S_40X40_NATIVE_TEXT_FOUND count={len(hits)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
