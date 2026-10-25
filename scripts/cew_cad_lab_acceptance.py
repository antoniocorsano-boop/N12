from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cew_cad_gateway.artifacts import ArtifactRepository
from cew_cad_gateway.canonical import sha256_file
from cew_cad_gateway.cli import build_live_runtime
from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.server import PolylineProposalInput
from cew_cad_gateway.types import PathClass
from cew_cad_gateway.workspace import Workspace, WorkspaceError

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PilotError(RuntimeError):
    pass


def _sha256_arg(value: str) -> str:
    if _SHA256.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("must be a lowercase 64-hex SHA-256")
    return value


def _point(value: str) -> tuple[float, float]:
    try:
        left, right = value.split(",", 1)
        return float(left), float(right)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("point must be X,Y") from exc


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def create_evidence_dir(repo_root: Path, stamp: str) -> Path:
    target_root = (repo_root.resolve() / "target" / "cew-cad-01").resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    target = (target_root / stamp).resolve()
    if not target.is_relative_to(target_root):
        raise PilotError("EVIDENCE_PATH_ESCAPE")
    target.mkdir(parents=False, exist_ok=False)
    return target


def validate_lab_target(workspace: Workspace, lab_dwg_ref: str, expected_source_sha256: str) -> Path:
    path = workspace.resolve_ref(lab_dwg_ref, PathClass.WORKING)
    if not path.exists() or not path.is_file():
        raise PilotError("LAB_DWG_MISSING")
    observed = sha256_file(path)
    if observed != expected_source_sha256:
        raise ValueError("LAB_DWG_HASH_MISMATCH")
    return path


def _validate_ocs_executable(path: Path, expected_sha256: str) -> Path:
    resolved = path.resolve()
    if not resolved.exists() or not resolved.is_file():
        raise PilotError("OCS_EXECUTABLE_MISSING")
    if sha256_file(resolved) != expected_sha256:
        raise PilotError("OCS_EXECUTABLE_HASH_MISMATCH")
    return resolved


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--ocs-executable", required=True)
    parser.add_argument("--ocs-sha256", required=True, type=_sha256_arg)
    parser.add_argument("--approval-public-key", required=True)
    parser.add_argument("--lab-dwg-ref", required=True)
    parser.add_argument("--expected-source-sha256", required=True, type=_sha256_arg)
    parser.add_argument("--target-format", choices=("dwg", "dxf"), default="dwg")
    parser.add_argument("--target-version", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--claim-ref", action="append", default=[])
    parser.add_argument("--decision-ref", action="append", default=[])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cew-cad-lab-acceptance",
        description="Controlled CEW-CAD-01 laboratory pilot. Never use on canonical N12 CAD artifacts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="read-only preflight and Changeset creation")
    _common_arguments(prepare)
    prepare.add_argument("--changeset-id", required=True)
    prepare.add_argument("--point", action="append", type=_point, required=True)
    prepare.add_argument("--intent", default="CEW-CAD-01 disposable laboratory polyline")

    execute = sub.add_parser("execute", help="apply an already signed approval, verify and save a new copy")
    _common_arguments(execute)
    execute.add_argument("--changeset-id", required=True)
    execute.add_argument("--approval-id", required=True)
    execute.add_argument(
        "--confirm-lab-mutation",
        required=True,
        choices=("CEW-LAB-ONLY",),
        help="explicit operator confirmation that the open drawing is a disposable lab copy",
    )

    recover = sub.add_parser(
        "recover",
        help="reconcile an already completed mutation, then verify and save without remutation",
    )
    _common_arguments(recover)
    recover.add_argument("--changeset-id", required=True)
    recover.add_argument("--approval-id", required=True)
    return parser


def _load_context(args: argparse.Namespace) -> tuple[GatewayPolicy, Workspace, Path, Any]:
    policy_path = Path(args.policy).resolve()
    policy = GatewayPolicy.load(policy_path)
    workspace = Workspace(Path(args.workspace_root), policy)
    lab = validate_lab_target(workspace, args.lab_dwg_ref, args.expected_source_sha256)
    executable = _validate_ocs_executable(Path(args.ocs_executable), args.ocs_sha256)
    public_key = Path(args.approval_public_key).resolve()
    if not public_key.exists() or not public_key.is_file():
        raise PilotError("APPROVAL_PUBLIC_KEY_MISSING")
    runtime = build_live_runtime(
        workspace_root=workspace.root,
        policy_path=policy_path,
        ocs_executable=executable,
        ocs_sha256=args.ocs_sha256,
        approval_public_key=public_key,
        evidence_refs=set(args.evidence_ref),
        claim_refs=set(args.claim_ref),
        decision_refs=set(args.decision_ref),
        target_format=args.target_format,
        target_version=args.target_version,
    )
    return policy, workspace, lab, runtime


def _assert_open_document(status: dict[str, Any], lab: Path, expected_sha256: str) -> None:
    document = status.get("document")
    if not isinstance(document, dict):
        raise PilotError("CAD_DOCUMENT_STATUS_MISSING")
    cad_path = document.get("path")
    cad_sha = document.get("sha256")
    if not isinstance(cad_path, str) or Path(cad_path).resolve() != lab.resolve():
        raise PilotError("OPEN_CAD_DOCUMENT_IS_NOT_LAB_TARGET")
    if cad_sha != expected_sha256:
        raise PilotError("OPEN_CAD_DOCUMENT_HASH_MISMATCH")


async def _prepare(args: argparse.Namespace) -> dict[str, Any]:
    _, workspace, lab, runtime = _load_context(args)
    if len(args.point) < 2:
        raise PilotError("POLYLINE_REQUIRES_AT_LEAST_TWO_POINTS")
    if not args.evidence_ref or not args.claim_ref or not args.decision_ref:
        raise PilotError("LAB_GOVERNANCE_REFS_REQUIRED")

    source_hash_before = sha256_file(lab)
    status = await runtime.status()
    _assert_open_document(status, lab, args.expected_source_sha256)
    audit = await runtime.audit(args.target_format, args.target_version)
    capture = await runtime.capture("viewport", False)
    proposal = PolylineProposalInput(
        changeset_id=args.changeset_id,
        intent=args.intent,
        points=list(args.point),
        evidence_refs=list(args.evidence_ref),
        claim_refs=list(args.claim_ref),
        decision_refs=list(args.decision_ref),
        coordinate_states=["RIF"] * len(args.point),
        epistemic_states=["RIF"],
        preconditions=["disposable working copy is the active CAD document"],
        postconditions=["geometry matches proposed laboratory polyline", "target audit remains lossless"],
        forbidden_side_effects=["no unrelated entity changes", "no source overwrite"],
        unresolved=[],
        influential_unresolved=False,
        target_unique=True,
    )
    proposed = await runtime.propose_changeset(proposal)
    if sha256_file(lab) != source_hash_before:
        raise PilotError("SOURCE_CHANGED_DURING_PREPARE")
    return {
        "phase": "PREPARED_READ_ONLY",
        "lab_dwg": str(lab),
        "source_sha256": source_hash_before,
        "status": status,
        "audit": audit,
        "capture": capture,
        "proposal": proposed,
        "next_gate": "HUMAN_SIGNED_APPROVAL_REQUIRED",
    }


async def _execute(args: argparse.Namespace) -> dict[str, Any]:
    _, workspace, lab, runtime = _load_context(args)
    source_hash_before = sha256_file(lab)
    status = await runtime.status()
    _assert_open_document(status, lab, args.expected_source_sha256)

    artifacts = ArtifactRepository(workspace)
    changeset = artifacts.load_changeset(args.changeset_id)
    approval = artifacts.load_approval(args.approval_id)
    if approval.changeset_id != changeset.changeset_id:
        raise PilotError("APPROVAL_CHANGESET_ID_MISMATCH")

    changed = await runtime.apply_approved_changeset(args.changeset_id, args.approval_id)
    verified = await runtime.verify_changeset(args.changeset_id, changed["change_id"])
    if verified.get("decision") != "PASS":
        raise PilotError("TECHNICAL_VERIFICATION_NOT_PASS")
    saved = await runtime.save_verified_copy(args.changeset_id, verified["verification_id"])
    source_hash_after = sha256_file(lab)
    if source_hash_after != source_hash_before or source_hash_after != args.expected_source_sha256:
        raise PilotError("SOURCE_CHANGED_DURING_EXECUTE")
    return {
        "phase": "LIVE_LAB_PILOT_COMPLETE",
        "lab_dwg": str(lab),
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "change": changed,
        "verification": verified,
        "verified_copy": saved,
        "promotion": "NOT_AUTHORIZED",
    }


async def _recover(args: argparse.Namespace) -> dict[str, Any]:
    _, workspace, lab, runtime = _load_context(args)
    source_hash_before = sha256_file(lab)
    status = await runtime.status()
    _assert_open_document(status, lab, args.expected_source_sha256)

    artifacts = ArtifactRepository(workspace)
    changeset = artifacts.load_changeset(args.changeset_id)
    approval = artifacts.load_approval(args.approval_id)
    if approval.changeset_id != changeset.changeset_id:
        raise PilotError("APPROVAL_CHANGESET_ID_MISMATCH")

    recovered = await runtime.recover_approved_changeset(args.changeset_id, args.approval_id)
    if recovered.get("status") != "RECOVERED_AND_SAVED":
        raise PilotError("RECOVERY_NOT_PASS")

    source_hash_after = sha256_file(lab)
    if source_hash_after != source_hash_before or source_hash_after != args.expected_source_sha256:
        raise PilotError("SOURCE_CHANGED_DURING_RECOVERY")
    return {
        "phase": "LIVE_LAB_RECOVERY_COMPLETE",
        "lab_dwg": str(lab),
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "recovery": recovered,
        "mutation_replayed": False,
        "promotion": "NOT_AUTHORIZED",
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence_dir = create_evidence_dir(Path(args.repo_root), _stamp())
    try:
        if args.command == "prepare":
            result = asyncio.run(_prepare(args))
        elif args.command == "execute":
            result = asyncio.run(_execute(args))
        else:
            result = asyncio.run(_recover(args))
    except Exception as exc:
        failure = {"status": "FAIL", "phase": args.command, "error_type": type(exc).__name__, "error": str(exc)}
        _write_json(evidence_dir / "pilot-result.json", failure)
        print(json.dumps(failure, separators=(",", ":"), ensure_ascii=False))
        return 2

    payload = {"status": "PASS", **result}
    _write_json(evidence_dir / "pilot-result.json", payload)
    print(json.dumps({"status": "PASS", "evidence_dir": str(evidence_dir), "phase": result["phase"]}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
