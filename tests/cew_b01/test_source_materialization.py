import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from cew_b01.source_contract import (
    SourceContract,
    SourceMaterializationError,
    materialize_source,
)


def git(repo: Path, *args: str):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class SourceMaterializationTests(unittest.TestCase):
    def make_fixture(self, root: Path):
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        git(repo, "config", "user.name", "CEW Test")
        git(repo, "config", "user.email", "cew@example.invalid")
        rel = Path("archive/documentazione_originaria/tavola 5.pdf")
        source = repo / rel
        source.parent.mkdir(parents=True)
        payload = b"%PDF-1.4\nCEW-B01 fixture\n%%EOF\n"
        source.write_bytes(payload)
        git(repo, "add", str(rel))
        git(repo, "commit", "-q", "-m", "fixture")
        commit = git(repo, "rev-parse", "HEAD")
        blob = git(repo, "rev-parse", f"{commit}:{rel.as_posix()}")
        sha = hashlib.sha256(payload).hexdigest()
        contract = SourceContract.from_mapping({
            "repository": "antoniocorsano-boop/N12",
            "commit": commit,
            "path": rel.as_posix(),
            "git_blob_sha": blob,
            "sha256": sha,
            "page_index": 0,
            "source_role": "TEST_IMMUTABLE_SOURCE",
        })
        return repo, payload, contract

    def test_materializes_only_after_commit_blob_and_sha256_match(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, payload, contract = self.make_fixture(root)
            destination = root / "out" / "tavola-5.pdf"
            result = materialize_source(contract, repo, destination)
            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(result.destination, destination)
            self.assertEqual(result.git_blob_sha, contract.git_blob_sha)
            self.assertEqual(result.sha256, contract.sha256)
            self.assertEqual(result.size_bytes, len(payload))

    def test_wrong_blob_fails_closed_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, _, contract = self.make_fixture(root)
            bad = SourceContract.from_mapping(dict(contract.to_mapping(), git_blob_sha="0" * 40))
            destination = root / "out.pdf"
            with self.assertRaises(SourceMaterializationError):
                materialize_source(bad, repo, destination)
            self.assertFalse(destination.exists())

    def test_wrong_sha256_fails_closed_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, _, contract = self.make_fixture(root)
            bad = SourceContract.from_mapping(dict(contract.to_mapping(), sha256="f" * 64))
            destination = root / "out.pdf"
            with self.assertRaises(SourceMaterializationError):
                materialize_source(bad, repo, destination)
            self.assertFalse(destination.exists())

    def test_wrong_commit_path_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo, _, contract = self.make_fixture(root)
            bad = SourceContract.from_mapping(dict(contract.to_mapping(), commit="a" * 40))
            destination = root / "out.pdf"
            with self.assertRaises(SourceMaterializationError):
                materialize_source(bad, repo, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
