from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .authority import FrozenAuthority
from .operational import OperationalMaterialization


@dataclass(frozen=True)
class ReplayResult:
    passed: bool
    failure_codes: tuple[str, ...]
    output_identity: str | None = None
    output_sha256: str | None = None
    output_size_bytes: int | None = None
    generated_at: str | None = None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha_file(path: Path) -> str:
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


def run_model_generation_replay(
    materialization: OperationalMaterialization,
    authority: FrozenAuthority,
    output_path: Path,
) -> ReplayResult:
    if materialization.operational_commit != authority.operational_commit:
        return ReplayResult(False, ("OPERATIONAL_COMMIT_MISMATCH",))
    if _git_blob_sha_file(materialization.builder_path) != authority.builder.git_blob_sha:
        return ReplayResult(False, ("BUILDER_IDENTITY_BLOB_MISMATCH",))

    materialized_map = dict(materialization.input_paths)
    expected_paths = [rel for rel, _ in authority.inputs]
    if list(materialized_map) != expected_paths:
        return ReplayResult(False, ("INPUT_SET_MISMATCH",))
    failures: list[str] = []
    for rel, expected_sha in authority.inputs:
        path = materialized_map.get(rel)
        if path is None or not path.is_file():
            failures.append(f"INPUT_SET_MISSING:{rel}")
        elif _sha256_file(path) != expected_sha:
            failures.append(f"INPUT_DIGEST_MISMATCH:{rel}")
    if failures:
        return ReplayResult(False, tuple(failures))

    try:
        frozen_datetime = _frozen_datetime_class(authority.output.generated_at)
    except ValueError:
        return ReplayResult(False, ("REPLAY_TIMESTAMP_INVALID",))

    spec = importlib.util.spec_from_file_location("cew_gate_authority_frozen_builder", materialization.builder_path)
    if spec is None or spec.loader is None:
        return ReplayResult(False, ("BUILDER_IDENTITY_IMPORT_FAILED",))
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return ReplayResult(False, ("BUILDER_IDENTITY_IMPORT_FAILED",))
    if not hasattr(module, "build_model"):
        return ReplayResult(False, ("BUILDER_IDENTITY_ENTRYPOINT_MISSING",))
    module.datetime = frozen_datetime

    try:
        with _working_directory(materialization.root):
            model = module.build_model(*(Path(rel) for rel in expected_paths))
    except Exception as exc:
        return ReplayResult(False, (f"REPLAY_BUILD_FAILED:{type(exc).__name__}",))

    if model.get("generated_at") != authority.output.generated_at:
        return ReplayResult(False, ("REPLAY_TIMESTAMP_NOT_FROZEN",))

    payload = (json.dumps(model, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    actual_sha = hashlib.sha256(payload).hexdigest()
    actual_size = len(payload)
    if output_path.name != authority.output.identity:
        failures.append("OUTPUT_IDENTITY_MISMATCH")
    if actual_sha != authority.output.sha256:
        failures.append("OUTPUT_SHA256_MISMATCH")
    if actual_size != authority.output.size_bytes:
        failures.append("OUTPUT_SIZE_MISMATCH")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)
    return ReplayResult(
        passed=not failures,
        failure_codes=tuple(failures),
        output_identity=output_path.name,
        output_sha256=actual_sha,
        output_size_bytes=actual_size,
        generated_at=str(model.get("generated_at")),
    )
