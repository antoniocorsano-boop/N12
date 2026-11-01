from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from .package_source import HISTORICAL_V25_PACKAGE, verify_package_source


PACKAGE_ASSET_MANIFEST_PATH = Path("archive/historical_packages/v25/package_asset_manifest.json")

_FROZEN_ASSET_CONTRACT: dict[str, Any] = {
    "schema": "CEW_COL03D_PACKAGE_ASSET_V1",
    "repository": "antoniocorsano-boop/N12",
    "release_id": 430_435_574,
    "release_must_remain_draft": True,
    "asset_id": 697_696_555,
    "asset_name": "Ariano_Irpino_DXF_strutturale_v25.zip",
    "asset_content_type": "application/zip",
    "package_sha256": "10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d",
    "package_size_bytes": 5_345_286,
    "package_member_count": 91,
    "authority": "HISTORICAL_DERIVED_EVIDENCE",
    "identity_promotion_authorized": False,
}


def _validate_manifest_contract(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ValueError("PACKAGE_ASSET_MANIFEST_DRIFT")
    if manifest != _FROZEN_ASSET_CONTRACT:
        raise ValueError("PACKAGE_ASSET_MANIFEST_DRIFT")


def load_package_asset_manifest(path: Path = PACKAGE_ASSET_MANIFEST_PATH) -> dict[str, Any]:
    try:
        manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("PACKAGE_ASSET_MANIFEST_UNAVAILABLE") from exc
    _validate_manifest_contract(manifest)
    return deepcopy(manifest)


def validate_package_asset_metadata(
    manifest: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    _validate_manifest_contract(manifest)
    expected = {
        "release_id": manifest["release_id"],
        "release_draft": manifest["release_must_remain_draft"],
        "asset_id": manifest["asset_id"],
        "name": manifest["asset_name"],
        "content_type": manifest["asset_content_type"],
        "size": manifest["package_size_bytes"],
        "digest": f"sha256:{manifest['package_sha256']}",
        "state": "uploaded",
    }
    if not isinstance(metadata, dict) or any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("PACKAGE_ASSET_METADATA_MISMATCH")
    return {
        "repository": manifest["repository"],
        "release_id": manifest["release_id"],
        "release_draft": True,
        "asset_id": manifest["asset_id"],
        "asset_name": manifest["asset_name"],
        "asset_content_type": manifest["asset_content_type"],
        "asset_size_bytes": manifest["package_size_bytes"],
        "asset_digest": f"sha256:{manifest['package_sha256']}",
        "asset_state": "uploaded",
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
    }


def verified_asset_package_witness(
    manifest: dict[str, Any],
    package_verification: dict[str, Any],
) -> dict[str, Any]:
    _validate_manifest_contract(manifest)
    required = {
        "logical_name": manifest["asset_name"],
        "sha256": manifest["package_sha256"],
        "size_bytes": manifest["package_size_bytes"],
        "member_count": manifest["package_member_count"],
        "materialization_state": "MATERIALIZED_VERIFIED",
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
    }
    if not isinstance(package_verification, dict) or any(
        package_verification.get(key) != value for key, value in required.items()
    ):
        raise ValueError("PACKAGE_ASSET_VERIFICATION_MISMATCH")
    return {
        "logical_name": manifest["asset_name"],
        "repository_path": f"github-release-asset://{manifest['repository']}/{manifest['release_id']}/{manifest['asset_id']}",
        "sha256": manifest["package_sha256"],
        "size_bytes": manifest["package_size_bytes"],
        "member_count": manifest["package_member_count"],
        "verification_state": "MATERIALIZED_VERIFIED",
        "repository_materialized": True,
        "exact_source_replayable": True,
        "release_id": manifest["release_id"],
        "asset_id": manifest["asset_id"],
        "asset_name": manifest["asset_name"],
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
        "structural_identity_authorized": False,
        "canonical_geometry_authorized": False,
        "canonical_write_authorized": False,
    }


def verify_downloaded_package_asset(
    path: Path,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    asset_manifest = deepcopy(manifest or load_package_asset_manifest())
    _validate_manifest_contract(asset_manifest)
    package_contract = deepcopy(HISTORICAL_V25_PACKAGE)
    package_contract["logical_name"] = asset_manifest["asset_name"]
    package_contract["sha256"] = asset_manifest["package_sha256"]
    package_contract["size_bytes"] = asset_manifest["package_size_bytes"]
    package_contract["member_count"] = asset_manifest["package_member_count"]
    verified = verify_package_source(Path(path), package_contract)
    return verified_asset_package_witness(asset_manifest, verified)
