from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Mapping


class SourceContractError(ValueError):
    """Raised when a source contract is malformed or violates a frozen anchor."""


class SourceMaterializationError(RuntimeError):
    """Raised when immutable Git/source identity cannot be proven."""


FROZEN_N12_TAV5 = {
    "repository": "antoniocorsano-boop/N12",
    "commit": "78c20a52db4f391ce0d13b9705b9f04737e218c9",
    "path": "archive/documentazione_originaria/tavola 5.pdf",
    "git_blob_sha": "ec32cd621877e9037cb26ebc083164140a8e3e68",
    "sha256": "2143b256511788691291cef533559306fc2988c7cb59a16d49cf86d1d7e94c7f",
    "page_index": 0,
    "source_role": "PRIMARY_IMMUTABLE_QUALIFICATION_SOURCE",
}

_FIELDS = tuple(FROZEN_N12_TAV5.keys())
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceContract:
    repository: str
    commit: str
    path: str
    git_blob_sha: str
    sha256: str
    page_index: int
    source_role: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "SourceContract":
        keys = set(raw)
        expected = set(_FIELDS)
        if keys != expected:
            missing = sorted(expected - keys)
            extra = sorted(keys - expected)
            raise SourceContractError(f"source contract fields mismatch; missing={missing}, extra={extra}")

        repository = raw["repository"]
        commit = raw["commit"]
        path = raw["path"]
        blob = raw["git_blob_sha"]
        sha256 = raw["sha256"]
        page_index = raw["page_index"]
        source_role = raw["source_role"]

        if not isinstance(repository, str) or repository.count("/") != 1 or repository.startswith("/"):
            raise SourceContractError("repository must be an immutable owner/repository identity")
        if not isinstance(commit, str) or not _HEX40.fullmatch(commit):
            raise SourceContractError("commit must be an exact lowercase 40-hex Git commit SHA")
        if not isinstance(blob, str) or not _HEX40.fullmatch(blob):
            raise SourceContractError("git_blob_sha must be an exact lowercase 40-hex Git object SHA")
        if not isinstance(sha256, str) or not _HEX64.fullmatch(sha256):
            raise SourceContractError("sha256 must be an exact lowercase 64-hex digest")
        if not isinstance(path, str) or not path:
            raise SourceContractError("path must be a non-empty repository-relative POSIX path")
        posix = PurePosixPath(path)
        if posix.is_absolute() or ".." in posix.parts or path != posix.as_posix():
            raise SourceContractError("path must be normalized, relative, and traversal-free")
        if isinstance(page_index, bool) or not isinstance(page_index, int) or page_index < 0:
            raise SourceContractError("page_index must be a non-negative integer")
        if not isinstance(source_role, str) or not source_role.strip():
            raise SourceContractError("source_role must be a non-empty string")

        return cls(
            repository=repository,
            commit=commit,
            path=path,
            git_blob_sha=blob,
            sha256=sha256,
            page_index=page_index,
            source_role=source_role,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in _FIELDS}


@dataclass(frozen=True)
class MaterializedSource:
    contract: SourceContract
    destination: Path
    git_blob_sha: str
    sha256: str
    size_bytes: int


def load_source_contract(path: Path | str) -> SourceContract:
    source_path = Path(path)
    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceContractError(f"cannot load source contract: {source_path}") from exc
    if not isinstance(raw, dict):
        raise SourceContractError("source contract must be a JSON object")
    return SourceContract.from_mapping(raw)


def validate_frozen_n12_tav5(contract: SourceContract) -> None:
    actual = contract.to_mapping()
    if actual != FROZEN_N12_TAV5:
        mismatches = [key for key in _FIELDS if actual.get(key) != FROZEN_N12_TAV5[key]]
        raise SourceContractError(f"contract does not match frozen N12 TAV5 anchor: {mismatches}")


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", "replace") if binary else proc.stderr
        raise SourceMaterializationError(f"git {' '.join(args)} failed: {stderr.strip()}")
    return proc.stdout if binary else proc.stdout.strip()


def materialize_source(
    contract: SourceContract,
    repository_path: Path | str,
    destination: Path | str,
) -> MaterializedSource:
    repo = Path(repository_path)
    dest = Path(destination)
    if not repo.exists():
        raise SourceMaterializationError(f"repository path does not exist: {repo}")

    resolved_commit = _git(repo, "rev-parse", "--verify", f"{contract.commit}^{{commit}}")
    if resolved_commit != contract.commit:
        raise SourceMaterializationError("requested immutable commit did not resolve exactly")

    actual_blob = _git(repo, "rev-parse", f"{contract.commit}:{contract.path}")
    if actual_blob != contract.git_blob_sha:
        raise SourceMaterializationError(
            f"Git blob mismatch for frozen source: expected {contract.git_blob_sha}, got {actual_blob}"
        )

    payload = _git(repo, "cat-file", "blob", actual_blob, binary=True)
    assert isinstance(payload, bytes)
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != contract.sha256:
        raise SourceMaterializationError(
            f"SHA-256 mismatch for frozen source: expected {contract.sha256}, got {actual_sha256}"
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    return MaterializedSource(
        contract=contract,
        destination=dest,
        git_blob_sha=actual_blob,
        sha256=actual_sha256,
        size_bytes=len(payload),
    )
