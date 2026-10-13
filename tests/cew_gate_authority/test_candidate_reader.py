from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from cew_gate_authority.authority import CandidateLimits
from cew_gate_authority.candidate_reader import CandidateReader


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.decode("utf-8").strip()


def init_repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="cew-candidate-reader-"))
    git(root.parent, "init", str(root))
    git(root, "config", "user.email", "cew@example.invalid")
    git(root, "config", "user.name", "CEW Tests")
    return root


def commit_file(repo: Path, rel: str, data: bytes, mode: int | None = None) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if mode is not None:
        os.chmod(path, mode)
    git(repo, "add", rel)
    git(repo, "commit", "-m", f"add {rel}")
    return git(repo, "rev-parse", "HEAD")


def limits(**overrides) -> CandidateLimits:
    values = {"max_blobs": 256, "max_blob_bytes": 8 * 1024 * 1024, "max_aggregate_bytes": 64 * 1024 * 1024, "max_json_depth": 64, "max_csv_rows": 250000}
    values.update(overrides)
    return CandidateLimits(**values)


class CandidateReaderTests(unittest.TestCase):
    def test_reads_exact_head_after_branch_moves(self):
        repo = init_repo()
        rel = "qualification/cew-contract-01/n12/qualification.json"
        h1 = commit_file(repo, rel, b'{"version":1}')
        reader = CandidateReader(repo / ".git", h1, limits(), allowlist=(rel,))
        commit_file(repo, rel, b'{"version":2}')
        self.assertEqual(reader.read_blob(rel), b'{"version":1}')

    def test_missing_and_outside_allowlist_fail_closed(self):
        repo = init_repo()
        rel = "qualification/cew-contract-01/n12/qualification.json"
        h = commit_file(repo, rel, b"{}")
        reader = CandidateReader(repo / ".git", h, limits(), allowlist=(rel,))
        with self.assertRaises(ValueError): reader.read_blob("qualification/cew-contract-01/n12/missing.json")
        with self.assertRaises(ValueError): reader.read_blob("README.md")

    def test_path_confusion_is_rejected(self):
        repo = init_repo()
        rel = "qualification/cew-contract-01/n12/qualification.json"
        h = commit_file(repo, rel, b"{}")
        reader = CandidateReader(repo / ".git", h, limits(), allowlist=(rel,))
        for bad in ("/tmp/x", "../x", "a/../x", "a\\b", ""):
            with self.subTest(path=bad):
                with self.assertRaises(ValueError): reader.read_blob(bad)

    def test_duplicate_unicode_normalized_paths_are_rejected(self):
        repo = init_repo()
        rel = "qualification/cew-contract-01/n12/é.json"
        h = commit_file(repo, rel, b"{}")
        decomposed = "qualification/cew-contract-01/n12/e\u0301.json"
        reader = CandidateReader(repo / ".git", h, limits(), allowlist=(rel,))
        with self.assertRaises(ValueError): reader.verify_allowlisted_surface((rel, decomposed))

    def test_symlink_mode_is_rejected(self):
        repo = init_repo(); root = repo / "qualification/cew-contract-01/n12"; root.mkdir(parents=True)
        (root / "target.json").write_text("{}")
        (root / "qualification.json").symlink_to("target.json")
        git(repo, "add", "qualification"); git(repo, "commit", "-m", "add symlink")
        h = git(repo, "rev-parse", "HEAD"); rel = "qualification/cew-contract-01/n12/qualification.json"
        reader = CandidateReader(repo / ".git", h, limits(), allowlist=(rel,))
        with self.assertRaises(ValueError): reader.read_blob(rel)

    def test_gitlink_mode_is_rejected(self):
        repo = init_repo(); seed = commit_file(repo, "seed.txt", b"seed")
        rel = "qualification/cew-contract-01/n12/gitlink"
        git(repo, "update-index", "--add", "--cacheinfo", f"160000,{seed},{rel}")
        git(repo, "commit", "-m", "add gitlink")
        h = git(repo, "rev-parse", "HEAD")
        reader = CandidateReader(repo / ".git", h, limits(), allowlist=(rel,))
        with self.assertRaises(ValueError): reader.read_blob(rel)

    def test_blob_count_per_blob_and_aggregate_limits_fail_closed(self):
        repo = init_repo()
        paths = ("qualification/cew-contract-01/n12/a.json", "qualification/cew-contract-01/n12/b.json", "qualification/cew-contract-01/n12/c.json")
        for index, rel in enumerate(paths): commit_file(repo, rel, (b"x" * 33) if index == 0 else (b"y" * 20))
        h = git(repo, "rev-parse", "HEAD")
        with self.assertRaises(ValueError): CandidateReader(repo / ".git", h, limits(max_blob_bytes=32), allowlist=paths).read_blob(paths[0])
        with self.assertRaises(ValueError): CandidateReader(repo / ".git", h, limits(max_blobs=2), allowlist=paths).verify_allowlisted_surface(paths)
        with self.assertRaises(ValueError): CandidateReader(repo / ".git", h, limits(max_blob_bytes=64, max_aggregate_bytes=50), allowlist=paths).verify_allowlisted_surface(paths)


if __name__ == "__main__": unittest.main()
