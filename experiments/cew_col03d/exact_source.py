from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from typing import Any

from .csv_evidence import parse_csv_member
from .dxf_evidence import audit_dxf_member
from .historical_quality import audit_historical_semantics
from .inventory_reconciliation import reconcile_required_members
from .member_verification import (
    REQUIRED_MEMBER_CONTRACTS,
    reconstruct_required_member_directory,
)
from .package_source import HISTORICAL_V25_PACKAGE
from .recovery import OUTPUT_NAMES, build_recovery_artifacts


_CSV_NAMES = tuple(
    sorted(contract["artifact_name"] for contract in REQUIRED_MEMBER_CONTRACTS if contract["artifact_name"].endswith(".csv"))
)
_DXF_NAMES = tuple(
    sorted(contract["artifact_name"] for contract in REQUIRED_MEMBER_CONTRACTS if contract["artifact_name"].endswith(".dxf"))
)


def _package_witness() -> dict[str, Any]:
    witness = deepcopy(HISTORICAL_V25_PACKAGE)
    witness["verification_state"] = "EXTERNALLY_VERIFIED_IMMUTABLE_WITNESS"
    witness["repository_materialized"] = False
    witness["exact_source_replayable"] = False
    return witness


def build_exact_source_recovery(
    *,
    transport_root: str | Path,
    inventory_text: str,
    predecessor_sha: str,
) -> dict[str, dict[str, Any]]:
    transport_path = Path(transport_root)
    with tempfile.TemporaryDirectory(prefix="cew-col03d-members-") as tmp:
        member_root = Path(tmp)
        member_rows = reconstruct_required_member_directory(
            transport_path,
            member_root,
            REQUIRED_MEMBER_CONTRACTS,
        )

        package_member_names = [contract["artifact_name"] for contract in REQUIRED_MEMBER_CONTRACTS]
        inventory_rows = reconcile_required_members(inventory_text, package_member_names)

        csv_evidence = [
            parse_csv_member(name, (member_root / name).read_bytes())
            for name in _CSV_NAMES
        ]
        dxf_evidence = [
            audit_dxf_member(name, (member_root / name).read_bytes())
            for name in _DXF_NAMES
        ]
        historical_quality = audit_historical_semantics(csv_evidence)

        return build_recovery_artifacts(
            predecessor_sha=predecessor_sha,
            package_witness=_package_witness(),
            member_rows=member_rows,
            inventory_rows=inventory_rows,
            csv_evidence=csv_evidence,
            dxf_evidence=dxf_evidence,
            historical_quality=historical_quality,
        )


def write_col03d_artifacts(
    output_root: str | Path,
    artifacts: dict[str, dict[str, Any]],
) -> list[Path]:
    if set(artifacts) != set(OUTPUT_NAMES):
        raise ValueError("COL03D_OUTPUT_SURFACE_DRIFT")

    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    unexpected = sorted(path.name for path in root.iterdir() if path.name not in OUTPUT_NAMES)
    if unexpected:
        raise ValueError(f"UNEXPECTED_COL03D_OUTPUT_SURFACE:{','.join(unexpected)}")

    written: list[Path] = []
    for name in OUTPUT_NAMES:
        path = root / name
        payload = json.dumps(
            artifacts[name],
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            separators=(",", ": "),
        ) + "\n"
        path.write_text(payload, encoding="utf-8", newline="\n")
        written.append(path)
    return written
