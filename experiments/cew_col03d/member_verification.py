from __future__ import annotations

import base64
import binascii
import hashlib
import lzma
from pathlib import Path
from typing import Any, Iterable
import zlib


HISTORICAL_MEMBER_ROOT = "archive/historical_packages/v25/members"
HISTORICAL_TRANSPORT_ROOT = "archive/historical_packages/v25/transport"

_REQUIRED_ROWS = (
    ("TAV5_CARPENTERIA.dxf", 717875, "f8daddb352ac52399f83d34995dada371ab8940d4866baa9d5acaa913b67e3ec", "02ca74cf", "DERIVED_GRAPHICAL_REFERENCE"),
    ("TAV6_TRAVI.dxf", 379309, "770eda8e5cf37f386427229aba68e414a3da3b6bda81f6cd557cf11cea1d14c1", "66e49298", "DERIVED_GRAPHICAL_REFERENCE"),
    ("TAV7_PILASTRI.dxf", 454309, "6ab095fee72db4f5163dac6cc85e04b8b47e6b54a9f4d8090a9c515512bec47d", "944223a9", "DERIVED_GRAPHICAL_REFERENCE"),
    ("ABACO_TOPOLOGICO_TAV5_v11.csv", 2852, "186345c8227945003e8ed57cdc6bc9d93a4f2c22ecfbbfe0af0e3e415cd1b442", "5d428214", "HISTORICAL_TOPOLOGY_REFERENCE"),
    ("ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv", 4564, "3226fd19cc6a9fc7ff52d5c95d28f16f72b7b173e3b9d3a7403d5dbbb74107a6", "f5b62a8f", "CANDIDATE_CROSS_DOCUMENT_ASSOCIATION"),
    ("MATRICE_PILASTRI_27x5_v22.csv", 6349, "a77de6b5f1310b8e0662f35f5381b656a134f36ffd92c24b8bbaf74b9cc89ce1", "816694d0", "HISTORICAL_VERTICAL_MATRIX_REFERENCE"),
    ("ABACO_TRAVI_TAV6_v23.csv", 8240, "48d48e014718b3d951fd1c4c5669f149203e684306ebf7933c3e2a16c95182bb", "0f53d534", "BEAM_DOCUMENTARY_REFERENCE"),
    ("ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv", 7279, "18ac263085b1da832346f8280d9788ad30708bb76cff99d19ee127858a38ee1e", "c1e1136e", "CANDIDATE_BEAM_ASSOCIATION"),
)

REQUIRED_MEMBER_CONTRACTS: tuple[dict[str, Any], ...] = tuple(
    {
        "artifact_name": name,
        "repository_path": f"{HISTORICAL_MEMBER_ROOT}/{name}",
        "size_bytes": size,
        "sha256": sha256,
        "package_crc32": crc32,
        "qualified_role": role,
        "transport_encoding": "XZ_BASE64",
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "promotion_authorized": False,
    }
    for name, size, sha256, crc32, role in _REQUIRED_ROWS
)


def verify_member_bytes(artifact_name: str, data: bytes, contract: dict[str, Any]) -> dict[str, Any]:
    if artifact_name != contract.get("artifact_name"):
        raise ValueError("HISTORICAL_MEMBER_CONTRACT_DRIFT")
    if contract.get("authority") != "HISTORICAL_DERIVED_EVIDENCE" or contract.get("promotion_authorized") is not False:
        raise ValueError("HISTORICAL_MEMBER_CONTRACT_DRIFT")
    actual_size = len(data)
    actual_sha256 = hashlib.sha256(data).hexdigest()
    actual_crc32 = f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"
    if (
        actual_size != int(contract.get("size_bytes") or -1)
        or actual_sha256 != str(contract.get("sha256") or "")
        or actual_crc32 != str(contract.get("package_crc32") or "").lower()
    ):
        raise ValueError("PROVENANCE_MISMATCH")
    return {
        "artifact_name": artifact_name,
        "repository_path": str(contract["repository_path"]),
        "size_bytes": actual_size,
        "sha256": actual_sha256,
        "package_crc32": actual_crc32,
        "qualified_role": str(contract["qualified_role"]),
        "materialization_state": "MATERIALIZED_VERIFIED",
        "authority": "HISTORICAL_DERIVED_EVIDENCE",
        "promotion_authorized": False,
    }


def _read_transport_payload(transport_root: Path, artifact_name: str) -> bytes:
    single = transport_root / f"{artifact_name}.xz.b64"
    if single.is_file():
        payload_paths = [single]
    else:
        payload_paths = sorted(transport_root.glob(f"{artifact_name}.xz.b64.part*"))
    if not payload_paths:
        raise ValueError(f"REQUIRED_MEMBER_TRANSPORT_NOT_FOUND:{artifact_name}")
    try:
        encoded = "".join(
            "".join(path.read_text(encoding="ascii").split())
            for path in payload_paths
        )
        compressed = base64.b64decode(encoded, validate=True)
        return lzma.decompress(compressed, format=lzma.FORMAT_XZ)
    except (OSError, UnicodeError, binascii.Error, lzma.LZMAError) as exc:
        raise ValueError(f"TRANSPORT_DECODE_FAILED:{artifact_name}") from exc


def reconstruct_required_member_directory(
    transport_root: str | Path,
    output_root: str | Path,
    contracts: Iterable[dict[str, Any]] = REQUIRED_MEMBER_CONTRACTS,
) -> list[dict[str, Any]]:
    transport_path = Path(transport_root)
    output_path = Path(output_root)
    reconstructed: list[dict[str, Any]] = []
    for contract in sorted(contracts, key=lambda row: str(row.get("artifact_name") or "")):
        name = str(contract.get("artifact_name") or "")
        if contract.get("transport_encoding") != "XZ_BASE64":
            raise ValueError(f"HISTORICAL_MEMBER_TRANSPORT_CONTRACT_DRIFT:{name}")
        data = _read_transport_payload(transport_path, name)
        verified = verify_member_bytes(name, data, contract)
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / name).write_bytes(data)
        reconstructed.append(
            {
                **verified,
                "transport_encoding": "XZ_BASE64",
                "transport_reconstruction_state": "LOSSLESS_RECONSTRUCTED",
            }
        )
    return reconstructed


def verify_required_member_directory(
    root: Path,
    contracts: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verified: list[dict[str, Any]] = []
    for contract in sorted(contracts, key=lambda row: str(row.get("artifact_name") or "")):
        name = str(contract.get("artifact_name") or "")
        path = Path(root) / name
        if not path.is_file():
            raise ValueError(f"REQUIRED_MEMBER_NOT_MATERIALIZED:{name}")
        verified.append(verify_member_bytes(name, path.read_bytes(), contract))
    return verified
