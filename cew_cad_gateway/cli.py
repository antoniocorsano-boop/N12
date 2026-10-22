from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .adapters.opencadstudio import OpenCADStudioAdapter
from .approval import ApprovalVerifier, sign_approval
from .artifacts import ArtifactRepository
from .changesets import ChangesetService
from .execution import ExecutionService
from .inspection import InspectionService
from .policy import GatewayPolicy
from .receipts import ReceiptStore
from .runtime import GatewayRuntimeImpl
from .server import run_stdio
from .verification import VerificationService
from .workspace import Workspace

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256_arg(value: str) -> str:
    if _SHA256.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("must be a lowercase 64-hex SHA-256")
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cew-cad")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the governed CEW-CAD MCP server over stdio")
    serve.add_argument("--workspace-root", required=True)
    serve.add_argument("--policy", required=True)
    serve.add_argument("--ocs-executable", required=True)
    serve.add_argument("--ocs-sha256", required=True, type=_sha256_arg)
    serve.add_argument("--approval-public-key", required=True)
    serve.add_argument("--evidence-ref", action="append", default=[])
    serve.add_argument("--claim-ref", action="append", default=[])
    serve.add_argument("--decision-ref", action="append", default=[])
    serve.add_argument("--target-format", choices=("dwg", "dxf"), default="dwg")
    serve.add_argument("--target-version", required=True)

    approve = sub.add_parser("approve", help="human-only signing of a stored Changeset")
    approve.add_argument("--workspace-root", required=True)
    approve.add_argument("--policy", required=True)
    approve.add_argument("--changeset-id", required=True)
    approve.add_argument("--private-key", required=True)
    approve.add_argument("--approval-id", required=True)
    approve.add_argument("--approved-by", required=True)
    approve.add_argument("--approved-at")
    return parser


def build_live_runtime(
    *,
    workspace_root: Path,
    policy_path: Path,
    ocs_executable: Path,
    ocs_sha256: str,
    approval_public_key: Path,
    evidence_refs: set[str],
    claim_refs: set[str],
    decision_refs: set[str],
    target_format: str,
    target_version: str,
) -> GatewayRuntimeImpl:
    policy = GatewayPolicy.load(policy_path)
    workspace = Workspace(workspace_root, policy)
    adapter = OpenCADStudioAdapter(
        ocs_executable,
        expected_executable_sha256=ocs_sha256,
    )
    receipt_store = ReceiptStore(workspace.zone_path("AUDITS"))
    inspection = InspectionService(adapter, workspace, receipt_store, now=_now)
    changesets = ChangesetService(
        policy,
        known_evidence=set(evidence_refs),
        known_claims=set(claim_refs),
        known_decisions=set(decision_refs),
    )
    approvals = ApprovalVerifier(approval_public_key, now=_now, max_age_seconds=900)
    execution = ExecutionService(
        adapter=adapter,
        workspace=workspace,
        policy=policy,
        approval_verifier=approvals,
        receipt_store=receipt_store,
    )
    verification = VerificationService(
        adapter=adapter,
        workspace=workspace,
        receipt_store=receipt_store,
        target_format=target_format,
        target_version=target_version,
    )
    artifacts = ArtifactRepository(workspace)
    return GatewayRuntimeImpl(
        inspection_service=inspection,
        changeset_service=changesets,
        execution_service=execution,
        verification_service=verification,
        artifacts=artifacts,
        workspace=workspace,
        target_format=target_format,
        target_version=target_version,
    )


def run_approve(
    *,
    workspace_root: Path,
    policy: GatewayPolicy,
    changeset_id: str,
    private_key: Path,
    approval_id: str,
    approved_by: str,
    approved_at: str | None = None,
) -> str:
    workspace = Workspace(workspace_root, policy)
    artifacts = ArtifactRepository(workspace)
    changeset = artifacts.load_changeset(changeset_id)
    approval = sign_approval(
        changeset=changeset,
        private_key_path=private_key,
        approval_id=approval_id,
        approved_by=approved_by,
        approved_at=approved_at or _now(),
    )
    artifacts.store_approval(approval)
    return approval.approval_id


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "serve":
        runtime = build_live_runtime(
            workspace_root=Path(args.workspace_root),
            policy_path=Path(args.policy),
            ocs_executable=Path(args.ocs_executable),
            ocs_sha256=args.ocs_sha256,
            approval_public_key=Path(args.approval_public_key),
            evidence_refs=set(args.evidence_ref),
            claim_refs=set(args.claim_ref),
            decision_refs=set(args.decision_ref),
            target_format=args.target_format,
            target_version=args.target_version,
        )
        run_stdio(runtime)
        return 0

    if args.command == "approve":
        policy = GatewayPolicy.load(Path(args.policy))
        approval_id = run_approve(
            workspace_root=Path(args.workspace_root),
            policy=policy,
            changeset_id=args.changeset_id,
            private_key=Path(args.private_key),
            approval_id=args.approval_id,
            approved_by=args.approved_by,
            approved_at=args.approved_at,
        )
        print(json.dumps({"approval_id": approval_id}, separators=(",", ":")))
        return 0

    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
