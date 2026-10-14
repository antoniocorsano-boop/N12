from __future__ import annotations

import posixpath
import subprocess
import unicodedata
from pathlib import Path
from typing import Sequence

from .authority import CandidateLimits


def normalize_candidate_path(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("candidate path must be a non-empty string")
    if "\x00" in value or "\\" in value or value.startswith("/") or value.endswith("/"):
        raise ValueError("candidate path is not a safe relative POSIX path")
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError("candidate path must already be NFC normalized")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("candidate path contains ambiguous or escaping component")
    return value


class CandidateReader:
    def __init__(
        self,
        repo_git_dir: Path,
        head_sha: str,
        limits: CandidateLimits,
        *,
        allowlist: Sequence[str] = (),
    ) -> None:
        self.repo_git_dir = Path(repo_git_dir)
        self.head_sha = str(head_sha)
        self.limits = limits
        normalized = [normalize_candidate_path(path) for path in allowlist]
        if len(normalized) != len(set(normalized)):
            raise ValueError("candidate allowlist contains duplicate normalized paths")
        self.allowlist = frozenset(normalized)
        self._git("cat-file", "-e", f"{self.head_sha}^{{commit}}")

    def _git(self, *args: str) -> bytes:
        try:
            result = subprocess.run(
                ["git", f"--git-dir={self.repo_git_dir}", *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                shell=False,
            )
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(f"git object access failed: {detail}") from exc
        return result.stdout

    def _entry(self, path: str) -> tuple[str, str, str]:
        safe = normalize_candidate_path(path)
        if safe not in self.allowlist:
            raise ValueError("candidate path is outside A0 allowlist")
        raw = self._git("ls-tree", "-z", "--full-tree", self.head_sha, "--", safe)
        entries = [entry for entry in raw.split(b"\0") if entry]
        if len(entries) != 1:
            raise ValueError("candidate path is missing or ambiguous")
        meta, sep, encoded_path = entries[0].partition(b"\t")
        if not sep:
            raise ValueError("invalid git tree entry")
        fields = meta.decode("ascii").split()
        if len(fields) != 3:
            raise ValueError("invalid git tree entry metadata")
        mode, object_type, object_sha = fields
        actual_path = encoded_path.decode("utf-8")
        if actual_path != safe:
            raise ValueError("git tree path does not match requested candidate path")
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("candidate object is not a regular blob")
        return mode, object_type, object_sha

    def _blob_size(self, object_sha: str) -> int:
        raw = self._git("cat-file", "-s", object_sha)
        try:
            return int(raw.strip())
        except ValueError as exc:
            raise ValueError("invalid git blob size") from exc

    def _surface_paths(self, root: str) -> set[str]:
        raw = self._git("ls-tree", "-r", "-z", "--full-tree", self.head_sha, "--", root)
        paths: set[str] = set()
        for entry in (item for item in raw.split(b"\0") if item):
            _meta, sep, encoded_path = entry.partition(b"\t")
            if not sep:
                raise ValueError("invalid git tree entry")
            path = normalize_candidate_path(encoded_path.decode("utf-8"))
            if path in paths:
                raise ValueError("candidate surface contains duplicate paths")
            paths.add(path)
        return paths

    def read_blob(self, path: str) -> bytes:
        _, _, object_sha = self._entry(path)
        size = self._blob_size(object_sha)
        if size > self.limits.max_blob_bytes:
            raise ValueError("candidate blob exceeds max_blob_bytes")
        data = self._git("cat-file", "blob", object_sha)
        if len(data) != size:
            raise ValueError("candidate blob size changed during read")
        return data

    def read_text(self, path: str) -> str:
        try:
            return self.read_blob(path).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("candidate text blob is not valid UTF-8") from exc

    def verify_allowlisted_surface(self, paths: Sequence[str]) -> None:
        normalized = [normalize_candidate_path(path) for path in paths]
        if not normalized:
            raise ValueError("candidate surface must be non-empty")
        if len(normalized) != len(set(normalized)):
            raise ValueError("candidate surface contains duplicate normalized paths")
        if len(normalized) > self.limits.max_blobs:
            raise ValueError("candidate surface exceeds max_blobs")

        parents = [posixpath.dirname(path) for path in normalized]
        root = posixpath.commonpath(parents)
        if not root or root == ".":
            raise ValueError("candidate surface has no bounded qualification root")
        if self._surface_paths(root) != set(normalized):
            raise ValueError("candidate qualification surface does not match A0 allowlist")

        total = 0
        for path in normalized:
            _, _, object_sha = self._entry(path)
            size = self._blob_size(object_sha)
            if size > self.limits.max_blob_bytes:
                raise ValueError("candidate blob exceeds max_blob_bytes")
            total += size
            if total > self.limits.max_aggregate_bytes:
                raise ValueError("candidate surface exceeds max_aggregate_bytes")
