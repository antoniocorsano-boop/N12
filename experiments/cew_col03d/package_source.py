from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any
import zipfile


HISTORICAL_V25_PACKAGE: dict[str, Any] = {
    "logical_name": "Ariano_Irpino_DXF_strutturale_v25.zip",
    "repository_path": "archive/historical_packages/v25/Ariano_Irpino_DXF_strutturale_v25.zip",
    "sha256": "10eba8c6fea2c04feeea0294278f90d90a080a247f07028cd1eaf106a2d52c8d",
    "size_bytes": 5_345_286,
    "member_count": 91,
    "authority": "HISTORICAL_DERIVED_EVIDENCE",
    "identity_promotion_authorized": False,
    "repository_materialized": True,
}

_FROZEN_KEYS = (
    "logical_name",
    "repository_path",
    "sha256",
    "size_bytes",
    "member_count",
    "authority",
    "identity_promotion_authorized",
    "repository_materialized",
)


def _validate_contract(contract: dict[str, Any], *, allow_test_digest_override: bool) -> None:
    if not isinstance(contract, dict):
        raise ValueError("PACKAGE_SOURCE_CONTRACT_DRIFT")
    if contract.get("authority") != "HISTORICAL_DERIVED_EVIDENCE":
        raise ValueError("PACKAGE_SOURCE_CONTRACT_DRIFT")
    if contract.get("identity_promotion_authorized") is not False:
        raise ValueError("PACKAGE_SOURCE_CONTRACT_DRIFT")
    if allow_test_digest_override:
        for key in ("logical_name", "repository_path"):
            if contract.get(key) != HISTORICAL_V25_PACKAGE[key]:
                raise ValueError("PACKAGE_SOURCE_CONTRACT_DRIFT")
        return
    if any(contract.get(key) != HISTORICAL_V25_PACKAGE[key] for key in _FROZEN_KEYS):
        raise ValueError("PACKAGE_SOURCE_CONTRACT_DRIFT")


def verify_package_source(
    path: Path,
    contract: dict[str, Any] | None = None,
    *,
    allow_test_digest_override: bool = False,
) -> dict[str, Any]:
    source_contract = deepcopy(contract or HISTORICAL_V25_PACKAGE)
    _validate_contract(source_contract, allow_test_digest_override=allow_test_digest_override)

    source_path = Path(path)
    if not source_path.is_file():
        raise ValueError("PACKAGE_SOURCE_NOT_FOUND")

    data = source_path.read_bytes()
    actual_sha256 = hashlib.sha256(data).hexdigest()
    actual_size = len(data)
    if actual_sha256 != str(source_contract.get("sha256") or "") or actual_size != int(
        source_contract.get("size_bytes") or -1
    ):
        raise ValueError("PROVENANCE_MISMATCH")

    try:
        with zipfile.ZipFile(source_path, "r") as archive:
            corrupt_member = archive.testzip()
            if corrupt_member is not None:
                raise ValueError("PACKAGE_ZIP_INVALID")
            member_count = len(archive.infolist())
    except (zipfile.BadZipFile, OSError):
        raise ValueError("PACKAGE_ZIP_INVALID") from None

    if member_count != int(source_contract.get("member_count") or -1):
        raise ValueError("PACKAGE_MEMBER_COUNT_MISMATCH")

    repository_path = Path(str(source_contract["repository_path"]))
    return {
        "logical_name": str(source_contract["logical_name"]),
        "source_path": source_path.as_posix(),
        "repository_path": repository_path.as_posix(),
        "sha256": actual_sha256,
        "size_bytes": actual_size,
        "member_count": member_count,
        "materialization_state": "MATERIALIZED_VERIFIED",
        "repository_materialized": source_path.as_posix() == repository_path.as_posix(),
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "identity_promotion_authorized": False,
    }
