from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


TAV07_SOURCE = {
    "catalogue_id": "TAV-07A",
    "archive_commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "path": "archive/documentazione_originaria/tavola7.pdf",
    "sha256": "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b",
    "repository_blob": "bf92501e723843fd912976b1b711285a61c548d3",
    "size_bytes": 798816,
    "class": "particolari_strutturali",
    "state": "DOC",
}

_STATIC_CONTRACT_KEYS = (
    "catalogue_id",
    "archive_commit",
    "path",
    "repository_blob",
    "class",
    "state",
)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _validate_contract(contract: dict[str, Any], *, allow_test_digest_override: bool) -> None:
    if not isinstance(contract, dict):
        raise ValueError("TAV.7 source contract drift: contract missing")
    for key in _STATIC_CONTRACT_KEYS:
        if contract.get(key) != TAV07_SOURCE[key]:
            raise ValueError(f"TAV.7 source contract drift: {key}")
    if not allow_test_digest_override and contract.get("sha256") != TAV07_SOURCE["sha256"]:
        raise ValueError("TAV.7 source contract drift: sha256")
    if not isinstance(contract.get("sha256"), str) or len(str(contract.get("sha256"))) != 64:
        raise ValueError("TAV.7 source contract drift: sha256 format")
    if not isinstance(contract.get("size_bytes"), int) or int(contract["size_bytes"]) <= 0:
        raise ValueError("TAV.7 source contract drift: size_bytes format")


def verify_materialized_source(
    path: Path,
    contract: dict[str, Any],
    *,
    allow_test_digest_override: bool = False,
) -> dict[str, Any]:
    _validate_contract(contract, allow_test_digest_override=allow_test_digest_override)
    source_path = Path(path)
    if not source_path.is_file():
        raise ValueError("PRIMARY_SOURCE_RECONSTRUCTION_FAILED: TAV.7 file missing")
    data = source_path.read_bytes()
    actual_size = len(data)
    actual_sha256 = hashlib.sha256(data).hexdigest()
    if actual_size != int(contract["size_bytes"]) or actual_sha256 != str(contract["sha256"]).lower():
        raise ValueError(
            "PROVENANCE_MISMATCH: "
            f"expected size/sha {contract['size_bytes']}/{contract['sha256']}, "
            f"got {actual_size}/{actual_sha256}"
        )
    return {
        "catalogue_id": contract["catalogue_id"],
        "archive_commit": contract["archive_commit"],
        "source_path": contract["path"],
        "repository_blob": contract["repository_blob"],
        "source_class": contract["class"],
        "documentary_state": contract["state"],
        "size_bytes": actual_size,
        "sha256": actual_sha256,
        "materialization_state": "MATERIALIZED_VERIFIED",
        "authority": "PRIMARY_DOCUMENTARY_SOURCE",
        "identity_promotion_authorized": False,
    }


def build_pdf_source_metadata(
    path: Path,
    contract: dict[str, Any],
    *,
    allow_test_digest_override: bool = False,
) -> dict[str, Any]:
    verified = verify_materialized_source(
        path,
        contract,
        allow_test_digest_override=allow_test_digest_override,
    )
    try:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(path))
        try:
            page_count = len(document)
            if page_count <= 0:
                raise ValueError("PDF_RECONSTRUCTION_FAILED: TAV.7 has zero pages")
            pages: list[dict[str, Any]] = []
            for index in range(page_count):
                page = document[index]
                try:
                    width_pt, height_pt = page.get_size()
                finally:
                    page.close()
                if width_pt <= 0 or height_pt <= 0:
                    raise ValueError("PDF_RECONSTRUCTION_FAILED: invalid page geometry")
                pages.append(
                    {
                        "page_index": index,
                        "width_pt": round(float(width_pt), 6),
                        "height_pt": round(float(height_pt), 6),
                        "target_raster_width_px": int(round(float(width_pt) * 300.0 / 72.0)),
                        "target_raster_height_px": int(round(float(height_pt) * 300.0 / 72.0)),
                    }
                )
        finally:
            document.close()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"PDF_RECONSTRUCTION_FAILED: {exc}") from exc

    return {
        **verified,
        "page_count": page_count,
        "pages": pages,
        "derivative_policy": {
            "authority": "DERIVATIVE_EVIDENCE_ONLY",
            "target_dpi": 300,
            "coordinate_basis": "PDF_POINTS_72_DPI",
            "raster_dimensions_deterministic_from_page_geometry": True,
        },
    }


def canonical_source_digest(metadata: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(metadata)).hexdigest()
