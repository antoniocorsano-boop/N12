from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from .authority import load_authority
from .candidate_reader import CandidateReader
from .event_identity import verify_dispatch_candidate
from .operational import materialize_operational_authority
from .qualification import evaluate_qualification
from .receipt import canonical_receipt_bytes
from .replay import run_model_generation_replay
from .types import ControlPlaneIdentity, GateCoreIdentity

_GATE_REPOSITORY = "antoniocorsano-boop/N12"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cew-gate-authority")
    sub = parser.add_subparsers(dest="command", required=True)
    qualify = sub.add_parser("qualify")
    qualify.add_argument("--candidate-git-dir", type=Path, required=True)
    qualify.add_argument("--operational-repo", type=Path, required=True)
    qualify.add_argument("--authority", type=Path, required=True)
    qualify.add_argument("--pr-metadata", type=Path, required=True)
    qualify.add_argument("--requested-sha", required=True)
    qualify.add_argument("--base-commit", required=True)
    qualify.add_argument("--gate-core-commit", required=True)
    qualify.add_argument("--qualified-at", required=True)
    qualify.add_argument("--output", type=Path, required=True)
    return parser


def _load_json_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def qualify(args: argparse.Namespace) -> int:
    authority = load_authority(args.authority)
    pr_metadata = _load_json_object(args.pr_metadata)
    candidate = verify_dispatch_candidate(
        pr_metadata,
        args.requested_sha,
        base_repository=_GATE_REPOSITORY,
    )
    control_plane = ControlPlaneIdentity(base_commit_sha=args.base_commit)
    gate_core = GateCoreIdentity(
        repository=_GATE_REPOSITORY,
        commit_sha=args.gate_core_commit,
        version="G0",
    )
    reader = CandidateReader(
        args.candidate_git_dir,
        candidate.head_sha,
        authority.limits,
        allowlist=authority.candidate_allowlist,
    )
    with tempfile.TemporaryDirectory(prefix="cew-gate-authority-") as temp:
        root = Path(temp)
        materialized = materialize_operational_authority(
            args.operational_repo,
            authority,
            root / "operational",
        )
        replay = run_model_generation_replay(
            materialized,
            authority,
            root / authority.output.identity,
        )
        receipt = evaluate_qualification(
            reader,
            authority,
            replay,
            control_plane,
            gate_core,
            candidate,
            qualified_at=args.qualified_at,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_receipt_bytes(receipt) + b"\n")
    return 0 if receipt.qualified else 1


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "qualify":
            return qualify(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CEW Gate Authority: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
