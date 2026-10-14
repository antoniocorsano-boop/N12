#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _frozen_datetime_class(timestamp: str):
    try:
        frozen = datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise ValueError("invalid frozen timestamp") from exc
    if frozen.tzinfo is None:
        raise ValueError("frozen timestamp must be timezone-aware")

    class FrozenDateTime:
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return frozen.replace(tzinfo=None)
            return frozen.astimezone(tz)

    return FrozenDateTime


def run_replay(authority_path: Path, source_root: Path, output_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        authority = json.loads(authority_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"passed": False, "errors": ["AUTHORITY_IDENTITY_PROFILE_INVALID"]}

    timestamp = str(authority.get("generated_at", "")).strip()
    try:
        frozen_datetime = _frozen_datetime_class(timestamp)
    except ValueError:
        return {"passed": False, "errors": ["REPLAY_TIMESTAMP_INVALID"]}

    builder_info = authority.get("builder") or {}
    builder_rel = str(builder_info.get("path", ""))
    builder_path = source_root / builder_rel
    if not builder_path.is_file():
        return {"passed": False, "errors": ["BUILDER_IDENTITY_FILE_MISSING"]}
    if git_blob_sha_file(builder_path) != str(builder_info.get("git_blob_sha", "")):
        return {"passed": False, "errors": ["BUILDER_IDENTITY_BLOB_MISMATCH"]}

    inputs = authority.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != 6:
        return {"passed": False, "errors": ["INPUT_SET_INVALID"]}
    paths = [str(item.get("path", "")) for item in inputs]
    if len(set(paths)) != 6 or any(not path for path in paths):
        return {"passed": False, "errors": ["INPUT_SET_INVALID"]}
    for item, rel in zip(inputs, paths):
        source = source_root / rel
        if not source.is_file():
            errors.append(f"INPUT_SET_MISSING:{rel}")
            continue
        if sha256_file(source) != str(item.get("sha256", "")):
            errors.append(f"INPUT_DIGEST_MISMATCH:{rel}")
    if errors:
        return {"passed": False, "errors": errors}

    spec = importlib.util.spec_from_file_location("cew_contract_01_frozen_builder", builder_path)
    if spec is None or spec.loader is None:
        return {"passed": False, "errors": ["BUILDER_IDENTITY_IMPORT_FAILED"]}
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return {"passed": False, "errors": ["BUILDER_IDENTITY_IMPORT_FAILED"]}
    if not hasattr(module, "build_model"):
        return {"passed": False, "errors": ["BUILDER_IDENTITY_ENTRYPOINT_MISSING"]}
    module.datetime = frozen_datetime

    try:
        with _working_directory(source_root):
            model = module.build_model(*(Path(path) for path in paths))
    except Exception as exc:
        return {"passed": False, "errors": [f"REPLAY_BUILD_FAILED:{type(exc).__name__}"]}

    if model.get("generated_at") != timestamp:
        return {"passed": False, "errors": ["REPLAY_TIMESTAMP_NOT_FROZEN"]}

    payload = (json.dumps(model, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    expected = authority.get("output") or {}
    if output_path.name != str(expected.get("identity", "")):
        errors.append("OUTPUT_IDENTITY_MISMATCH")
    actual_sha = hashlib.sha256(payload).hexdigest()
    actual_size = len(payload)
    if actual_sha != str(expected.get("sha256", "")):
        errors.append("OUTPUT_SHA256_MISMATCH")
    if actual_size != expected.get("size_bytes"):
        errors.append("OUTPUT_SIZE_MISMATCH")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    return {
        "passed": not errors,
        "errors": errors,
        "identity": output_path.name,
        "sha256": actual_sha,
        "size_bytes": actual_size,
        "generated_at": model.get("generated_at"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    result = run_replay(args.authority, args.source_root, args.output)
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
