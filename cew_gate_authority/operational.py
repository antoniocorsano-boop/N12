from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .authority import FrozenAuthority


@dataclass(frozen=True)
class OperationalMaterialization:
    root: Path
    operational_commit: str
    builder_path: Path
    builder_git_blob_sha: str
    input_paths: tuple[tuple[str, Path], ...]
    registration_path: Path
    registration_git_blob_sha: str


def _safe_trusted_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or not value or "\\" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"invalid trusted authority path: {value!r}")
    return value


def _git(repo: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"operational Git object access failed: {detail}") from exc
    return result.stdout


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _blob_sha(repo: Path, commit: str, rel: str) -> str:
    return _git(repo, "rev-parse", f"{commit}:{rel}").decode("ascii").strip()


def _materialize(repo: Path, commit: str, rel: str, dest: Path) -> bytes:
    data = _git(repo, "show", f"{commit}:{rel}")
    target = dest / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return data


def materialize_operational_authority(repo: Path, authority: FrozenAuthority, dest: Path) -> OperationalMaterialization:
    repo = Path(repo)
    dest = Path(dest)
    resolved = _git(repo, "rev-parse", f"{authority.operational_commit}^{{commit}}").decode("ascii").strip()
    if resolved != authority.operational_commit:
        raise ValueError("operational commit identity mismatch")

    builder_rel = _safe_trusted_path(authority.builder.path)
    actual_builder_blob = _blob_sha(repo, authority.operational_commit, builder_rel)
    if actual_builder_blob != authority.builder.git_blob_sha:
        raise ValueError("builder Git blob identity mismatch")
    _materialize(repo, authority.operational_commit, builder_rel, dest)

    materialized_inputs: list[tuple[str, Path]] = []
    for rel, expected_sha in authority.inputs:
        rel = _safe_trusted_path(rel)
        data = _materialize(repo, authority.operational_commit, rel, dest)
        if _sha256_bytes(data) != expected_sha:
            raise ValueError(f"input SHA-256 mismatch: {rel}")
        materialized_inputs.append((rel, dest / rel))

    registration_rel = _safe_trusted_path(authority.registration.source_path)
    actual_registration_blob = _blob_sha(repo, authority.operational_commit, registration_rel)
    if actual_registration_blob != authority.registration.source_git_blob_sha:
        raise ValueError("registration source Git blob identity mismatch")
    _materialize(repo, authority.operational_commit, registration_rel, dest)

    return OperationalMaterialization(
        root=dest,
        operational_commit=authority.operational_commit,
        builder_path=dest / builder_rel,
        builder_git_blob_sha=actual_builder_blob,
        input_paths=tuple(materialized_inputs),
        registration_path=dest / registration_rel,
        registration_git_blob_sha=actual_registration_blob,
    )
