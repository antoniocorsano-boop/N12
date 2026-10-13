from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path


class ReplayTests(unittest.TestCase):
    def _fixture(self, root: Path):
        from scripts.cew_contract_01_replay import git_blob_sha_file, run_replay

        source_root = root / "src"
        (source_root / "scripts").mkdir(parents=True)
        (source_root / "data").mkdir()
        builder = source_root / "scripts/builder.py"
        builder.write_text(
            "from datetime import datetime, timezone\n"
            "from pathlib import Path\n"
            "import hashlib\n"
            "def build_model(a,b,c,d,e,f):\n"
            " return {\"generated_at\":datetime.now(timezone.utc).isoformat(),\"paths\":[x.as_posix() for x in (a,b,c,d,e,f)],\"digests\":[hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in (a,b,c,d,e,f)]}\n",
            encoding="utf-8",
        )
        inputs = []
        for index in range(6):
            source = source_root / f"data/i{index}.txt"
            source.write_text(f"input-{index}\n", encoding="utf-8")
            inputs.append({"path": f"data/i{index}.txt", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        generated_at = "2026-08-26T09:54:00.472520+00:00"
        expected_model = {
            "generated_at": generated_at,
            "paths": [item["path"] for item in inputs],
            "digests": [item["sha256"] for item in inputs],
        }
        payload = (json.dumps(expected_model, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        authority = {
            "operational_commit": "test",
            "builder": {"path": "scripts/builder.py", "git_blob_sha": git_blob_sha_file(builder)},
            "inputs": inputs,
            "generated_at": generated_at,
            "output": {
                "identity": "out.json",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            },
        }
        authority_path = root / "authority.json"
        authority_path.write_text(json.dumps(authority), encoding="utf-8")
        return run_replay, authority_path, source_root, authority

    def test_replay_freezes_only_timestamp_and_preserves_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run_replay, authority_path, source_root, authority = self._fixture(Path(td))
            output_path = Path(td) / "out.json"
            result = run_replay(authority_path, source_root, output_path)
            self.assertTrue(result["passed"])
            self.assertEqual(result["sha256"], authority["output"]["sha256"])
            model = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(model["generated_at"], authority["generated_at"])
            self.assertEqual(model["paths"], [item["path"] for item in authority["inputs"]])

    def test_replay_rejects_builder_blob_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run_replay, authority_path, source_root, _ = self._fixture(Path(td))
            data = json.loads(authority_path.read_text(encoding="utf-8"))
            data["builder"]["git_blob_sha"] = "bad"
            authority_path.write_text(json.dumps(data), encoding="utf-8")
            result = run_replay(authority_path, source_root, Path(td) / "out.json")
            self.assertFalse(result["passed"])
            self.assertIn("BUILDER_IDENTITY_BLOB_MISMATCH", result["errors"])

    def test_replay_rejects_missing_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run_replay, authority_path, source_root, _ = self._fixture(Path(td))
            data = json.loads(authority_path.read_text(encoding="utf-8"))
            data["generated_at"] = ""
            authority_path.write_text(json.dumps(data), encoding="utf-8")
            result = run_replay(authority_path, source_root, Path(td) / "out.json")
            self.assertFalse(result["passed"])
            self.assertIn("REPLAY_TIMESTAMP_INVALID", result["errors"])

    def test_replay_rejects_input_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            run_replay, authority_path, source_root, _ = self._fixture(Path(td))
            (source_root / "data/i3.txt").write_text("tampered\n", encoding="utf-8")
            result = run_replay(authority_path, source_root, Path(td) / "out.json")
            self.assertFalse(result["passed"])
            self.assertIn("INPUT_DIGEST_MISMATCH:data/i3.txt", result["errors"])


if __name__ == "__main__":
    unittest.main()
