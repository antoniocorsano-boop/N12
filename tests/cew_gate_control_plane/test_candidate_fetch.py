import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from cew_gate_control_plane.candidate_fetch import fetch_candidate
from cew_gate_control_plane.contracts import ControlPlaneError


def git(cwd: Path, *args: str) -> str:
    cp = subprocess.run(["git", *args], cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return cp.stdout.strip()


def make_base_with_candidate(files: dict[str, bytes] | None = None) -> tuple[Path, Path, str]:
    root = Path(tempfile.mkdtemp(prefix="task9-fetch-"))
    work = root / "work"
    base = root / "base.git"
    work.mkdir()
    git(work, "init")
    git(work, "config", "user.email", "cew@example.invalid")
    git(work, "config", "user.name", "CEW")
    payload = files or {"qualification/cew-contract-01/n12/qualification.json": b"{}"}
    for rel, data in payload.items():
        path = work / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    git(work, "add", ".")
    git(work, "commit", "-m", "candidate")
    sha = git(work, "rev-parse", "HEAD")
    subprocess.run(["git", "init", "--bare", str(base)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    git(work, "remote", "add", "origin", str(base))
    git(work, "push", "origin", f"{sha}:refs/pull/148/head")
    return work, base, sha


class CandidateFetchIdentityTests(unittest.TestCase):
    def assert_code(self, code, fn):
        with self.assertRaises(ControlPlaneError) as ctx:
            fn()
        self.assertEqual(ctx.exception.code, code)

    def test_force_push_between_metadata_and_fetch_fails(self):
        work, base, old = make_base_with_candidate()
        (work / "new.txt").write_text("new")
        git(work, "add", "."); git(work, "commit", "-m", "force-push")
        new = git(work, "rev-parse", "HEAD")
        git(work, "push", "--force", "origin", f"{new}:refs/pull/148/head")
        dest = Path(tempfile.mkdtemp()) / "candidate.git"
        self.assert_code("CANDIDATE_FETCHED_SHA_MISMATCH", lambda: fetch_candidate(str(base), 148, old, dest))

    def test_fetched_ref_must_equal_requested_h(self):
        _work, base, sha = make_base_with_candidate()
        dest = Path(tempfile.mkdtemp()) / "candidate.git"
        self.assert_code("CANDIDATE_FETCHED_SHA_MISMATCH", lambda: fetch_candidate(str(base), 148, "f" * 40, dest))
        self.assertNotEqual(sha, "f" * 40)

    def test_fetched_ref_must_resolve_to_commit_object(self):
        root = Path(tempfile.mkdtemp(prefix="task9-object-"))
        base = root / "base.git"
        subprocess.run(["git", "init", "--bare", str(base)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        blob = subprocess.run(["git", "--git-dir", str(base), "hash-object", "-w", "--stdin"], input=b"x", stdout=subprocess.PIPE, check=True).stdout.decode().strip()
        subprocess.run(["git", "--git-dir", str(base), "update-ref", "refs/pull/148/head", blob], check=True)
        dest = root / "candidate.git"
        self.assert_code("CANDIDATE_REF_FETCH_FAILED", lambda: fetch_candidate(str(base), 148, blob, dest))


class CandidateNoExecTests(unittest.TestCase):
    def test_public_fork_candidate_is_accepted_as_data_via_base_pr_ref(self):
        _work, base, sha = make_base_with_candidate({"qualification/cew-contract-01/n12/qualification.json": b'{"origin":"fork"}'})
        dest = Path(tempfile.mkdtemp()) / "candidate.git"
        self.assertEqual(fetch_candidate(str(base), 148, sha, dest), sha)
        self.assertEqual(git(dest, "rev-parse", "--is-bare-repository"), "true")

    def test_malicious_candidate_files_are_never_executed(self):
        root = Path(tempfile.mkdtemp(prefix="task9-marker-"))
        marker = root / "EXECUTED"
        files = {
            "qualification/cew-contract-01/n12/qualification.json": b"{}",
            "evil.py": f"from pathlib import Path; Path({str(marker)!r}).write_text('python')\n".encode(),
            "evil.sh": f"#!/bin/sh\necho shell > {marker}\n".encode(),
            "package.json": (f'{{"scripts":{{"preinstall":"echo package > {marker}"}}}}').encode(),
            ".github/actions/evil/action.yml": (f"runs:\n  using: composite\n  steps:\n    - shell: bash\n      run: echo action > {marker}\n").encode(),
            ".github/workflows/evil.yml": b"name: evil\non: push\njobs: {}\n",
        }
        work, base, sha = make_base_with_candidate(files)
        os.chmod(work / "evil.sh", 0o755)
        git(work, "add", "evil.sh"); git(work, "commit", "-m", "make executable")
        sha = git(work, "rev-parse", "HEAD")
        git(work, "push", "--force", "origin", f"{sha}:refs/pull/148/head")
        dest = root / "candidate.git"
        self.assertEqual(fetch_candidate(str(base), 148, sha, dest), sha)
        self.assertFalse(marker.exists())
        self.assertFalse((dest / "evil.py").exists())

    def test_candidate_copies_of_gate_or_authority_do_not_affect_trusted_inputs(self):
        files = {
            "qualification/cew-contract-01/n12/qualification.json": b"{}",
            "cew_gate_authority/authority.py": b"raise SystemExit('candidate gate executed')",
            "governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json": b'{"candidate":"fake"}',
        }
        _work, base, sha = make_base_with_candidate(files)
        dest = Path(tempfile.mkdtemp()) / "candidate.git"
        self.assertEqual(fetch_candidate(str(base), 148, sha, dest), sha)
        self.assertEqual(git(dest, "show", f"{sha}:governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json"), '{"candidate":"fake"}')


if __name__ == "__main__":
    unittest.main()
