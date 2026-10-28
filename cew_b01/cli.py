from __future__ import annotations

import argparse
import json

from .source_contract import load_source_contract, materialize_source, validate_frozen_n12_tav5


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m cew_b01.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    materialize = sub.add_parser("materialize-source")
    materialize.add_argument(
        "--contract",
        default="governance/cew-b01/N12_TAV5_SOURCE_v1.json",
    )
    materialize.add_argument("--repository-path", required=True)
    materialize.add_argument("--destination", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize-source":
        contract = load_source_contract(args.contract)
        validate_frozen_n12_tav5(contract)
        result = materialize_source(contract, args.repository_path, args.destination)
        print(json.dumps({
            "destination": str(result.destination),
            "git_blob_sha": result.git_blob_sha,
            "sha256": result.sha256,
            "size_bytes": result.size_bytes,
        }, sort_keys=True))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
