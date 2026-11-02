from __future__ import annotations

import argparse
import csv
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Callable, Iterable

from experiments.cew_cal01.interval_ocr_compare import build_interval_ocr_comparison


LOCAL_OCR_FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "family_id": "GRAY_PSM7",
        "preprocess": "NORMALIZED_GRAY",
        "psm": 7,
        "scale": 1.0,
        "whitelist": "0123456789.,",
    },
    {
        "family_id": "LINE_SUPPRESSED_PSM7",
        "preprocess": "THRESHOLD_LINE_SUPPRESSED",
        "psm": 7,
        "scale": 1.0,
        "whitelist": "0123456789.,",
    },
    {
        "family_id": "ENLARGED_PSM13",
        "preprocess": "ENLARGED_THRESHOLD",
        "psm": 13,
        "scale": 2.0,
        "whitelist": "0123456789.,",
    },
)

OcrRunner = Callable[[Path, dict[str, Any]], dict[str, Any]]


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _tesseract_version() -> str:
    proc = subprocess.run(
        ["tesseract", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"CAL01_INTERVAL_OCR_TESSERACT_VERSION_FAILED:{proc.stderr.strip()}")
    first_line = next((line.strip() for line in proc.stdout.splitlines() if line.strip()), "")
    if not first_line:
        raise RuntimeError("CAL01_INTERVAL_OCR_TESSERACT_VERSION_EMPTY")
    return first_line


def _prepare_crop(crop_path: Path, family: dict[str, Any]) -> Any:
    import cv2

    gray = cv2.imread(str(crop_path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise RuntimeError("CAL01_INTERVAL_OCR_CROP_UNREADABLE")

    preprocess = str(family["preprocess"])
    if preprocess == "NORMALIZED_GRAY":
        return cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if preprocess == "THRESHOLD_LINE_SUPPRESSED":
        horizontal = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1)),
        )
        vertical = cv2.morphologyEx(
            binary,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35)),
        )
        line_mask = cv2.bitwise_or(horizontal, vertical)
        text_mask = cv2.subtract(binary, line_mask)
        return 255 - text_mask

    if preprocess == "ENLARGED_THRESHOLD":
        prepared = 255 - binary
        scale = float(family.get("scale", 2.0))
        if scale <= 0:
            raise ValueError("CAL01_INTERVAL_OCR_SCALE_INVALID")
        return cv2.resize(
            prepared,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC,
        )

    raise ValueError("CAL01_INTERVAL_OCR_PREPROCESS_UNKNOWN")


def _best_tesseract_token(tsv: str) -> tuple[str, float | None]:
    reader = csv.DictReader(tsv.splitlines(), delimiter="\t")
    candidates: list[tuple[float, str]] = []
    for row in reader:
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        try:
            confidence = float(row.get("conf") or -1)
        except (TypeError, ValueError):
            confidence = -1.0
        candidates.append((confidence, text))
    if not candidates:
        return "", None
    confidence, text = max(candidates, key=lambda item: (item[0], item[1]))
    normalized_confidence = None if confidence < 0 else min(1.0, max(0.0, confidence / 100.0))
    return text, normalized_confidence


def _run_tesseract_family(crop_path: Path, family: dict[str, Any]) -> dict[str, Any]:
    import cv2

    image = _prepare_crop(crop_path, family)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        temp_path = Path(handle.name)
    try:
        if not cv2.imwrite(str(temp_path), image):
            raise RuntimeError("CAL01_INTERVAL_OCR_PREPARED_CROP_WRITE_FAILED")
        command = [
            "tesseract",
            str(temp_path),
            "stdout",
            "--psm",
            str(int(family["psm"])),
            "-c",
            f"tessedit_char_whitelist={family['whitelist']}",
            "tsv",
        ]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"CAL01_INTERVAL_OCR_TESSERACT_FAILED:{proc.stderr.strip()}")
        raw_text, confidence = _best_tesseract_token(proc.stdout)
        return {
            "raw_text": raw_text,
            "confidence": confidence,
            "provider_version": _tesseract_version(),
        }
    finally:
        temp_path.unlink(missing_ok=True)


def _load_manifest(review_dir: Path) -> dict[str, Any]:
    path = review_dir / "interval-text-review-manifest.json"
    if not path.is_file():
        raise ValueError("CAL01_INTERVAL_OCR_MANIFEST_MISSING")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("CAL01_INTERVAL_OCR_MANIFEST_INVALID")
    return manifest


def run_local_interval_ocr(
    review_dir: Path,
    *,
    ocr_runner: OcrRunner | None = None,
    external_observations: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest = _load_manifest(review_dir)
    runner = ocr_runner or _run_tesseract_family
    observations: list[dict[str, Any]] = []

    requests = sorted(
        [dict(row) for row in manifest.get("review_requests", [])],
        key=lambda row: str(row.get("review_id") or ""),
    )
    for request in requests:
        review_id = str(request.get("review_id") or "")
        crop_rel = str(request.get("crop_file") or "")
        expected_digest = str(request.get("crop_sha256") or "")
        if not review_id or not crop_rel or not expected_digest.startswith("sha256:"):
            raise ValueError("CAL01_INTERVAL_OCR_REVIEW_REQUEST_INVALID")
        crop_path = review_dir / crop_rel
        if not crop_path.is_file():
            raise ValueError("CAL01_INTERVAL_OCR_CROP_FILE_MISSING")
        actual_digest = _sha256_file(crop_path)
        if actual_digest != expected_digest:
            raise ValueError("CAL01_INTERVAL_OCR_CROP_FILE_DIGEST_MISMATCH")

        for family in LOCAL_OCR_FAMILIES:
            response = dict(runner(crop_path, dict(family)) or {})
            observations.append(
                {
                    "review_id": review_id,
                    "crop_sha256": expected_digest,
                    "provider_id": "TESSERACT",
                    "family_id": str(family["family_id"]),
                    "model_id": "tesseract-system",
                    "provider_version": str(response.get("provider_version") or "UNKNOWN"),
                    "raw_text": str(response.get("raw_text") or "").strip(),
                    "confidence": response.get("confidence"),
                }
            )

    if external_observations:
        raise ValueError("CAL01_INTERVAL_OCR_EXTERNAL_PROVIDER_NOT_YET_BOUND")

    result = build_interval_ocr_comparison(manifest, observations)
    result["local_recognizer"] = {
        "provider_id": "TESSERACT",
        "family_count": len(LOCAL_OCR_FAMILIES),
        "families": [dict(row) for row in LOCAL_OCR_FAMILIES],
    }
    payload = {key: value for key, value in result.items() if key != "comparison_digest"}
    result["comparison_digest"] = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    (review_dir / "interval-ocr-comparison.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic comparative OCR on CEW-CAL-01 exact interval review crops"
    )
    parser.add_argument("--review-dir", required=True)
    args = parser.parse_args()
    result = run_local_interval_ocr(Path(args.review_dir))
    print(
        json.dumps(
            {
                "source_id": result["source"]["source_id"],
                "review_count": result["review_count"],
                "comparison_digest": result["comparison_digest"],
                "primary_anchor_count": result["primary_anchor_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
