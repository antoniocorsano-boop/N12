from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.cew_cal01.external_chain_postprocess import _normalize_raster
from experiments.cew_cal01.interval_text_exact import materialize_interval_text_review_assets


def run_exact_interval_text_review(
    *,
    discovery_path: Path,
    refined_path: Path,
    image_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    import cv2

    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    refined = json.loads(refined_path.read_text(encoding="utf-8"))
    discovery_source = dict(discovery.get("source") or {})
    refined_source = dict(refined.get("source") or {})
    if discovery_source.get("source_id") != refined_source.get("source_id"):
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_SOURCE_ID_MISMATCH")
    if discovery_source.get("sha256") != refined_source.get("sha256"):
        raise ValueError("CAL01_INTERVAL_TEXT_EXACT_SOURCE_DIGEST_MISMATCH")

    source_gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if source_gray is None:
        raise RuntimeError("CAL01_INTERVAL_TEXT_EXACT_RASTER_UNREADABLE")
    transform = str(
        ((discovery.get("plan_envelope") or {}).get("normalization") or {}).get("transform")
        or "IDENTITY"
    )
    normalized = _normalize_raster(source_gray, transform)
    manifest = materialize_interval_text_review_assets(
        refined=refined,
        normalized_gray=normalized,
        output_dir=output_dir,
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize deterministic interval-level text review assets from qualified external chains"
    )
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--refined", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    manifest = run_exact_interval_text_review(
        discovery_path=Path(args.discovery),
        refined_path=Path(args.refined),
        image_path=Path(args.image),
        output_dir=Path(args.output_dir),
    )
    print(
        json.dumps(
            {
                "source_id": manifest["source"]["source_id"],
                "review_request_count": manifest["review_request_count"],
                "review_digest": manifest["review_digest"],
                "recognizer_binding_status": manifest["recognizer_binding_status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
