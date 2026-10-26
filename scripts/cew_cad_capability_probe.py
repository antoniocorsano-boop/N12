from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Callable

from cew_cad_gateway.capability_diagnostic import capture_capability_diagnostic


async def capture_capability_samples(
    *,
    executable: Path,
    expected_executable_sha256: str,
    output_dir: Path,
    client_factory: Callable[[Path], Any] | None = None,
) -> dict[str, object]:
    return await capture_capability_diagnostic(
        executable=executable,
        expected_executable_sha256=expected_executable_sha256,
        output_dir=output_dir,
        client_factory=client_factory,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cew-cad-capability-probe",
        description="Read-only two-sample OpenCADStudio capability drift probe.",
    )
    parser.add_argument("--ocs-executable", required=True, type=Path)
    parser.add_argument("--ocs-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = asyncio.run(
        capture_capability_samples(
            executable=args.ocs_executable,
            expected_executable_sha256=args.ocs_sha256,
            output_dir=args.output_dir,
        )
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
