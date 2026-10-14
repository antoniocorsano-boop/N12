from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

MANIFEST = Path("governance/cew-gate-authority/gate-core/G0_MANIFEST.json")
TOOLCHAIN = Path("governance/cew-gate-authority/TRUSTED_TOOLCHAIN_v1.json")
EXPECTED_COMPONENTS = {
    "cew_gate_authority/__init__.py",
    "cew_gate_authority/authority.py",
    "cew_gate_authority/candidate_reader.py",
    "cew_gate_authority/cli.py",
    "cew_gate_authority/event_identity.py",
    "cew_gate_authority/failure_codes.py",
    "cew_gate_authority/operational.py",
    "cew_gate_authority/qualification.py",
    "cew_gate_authority/receipt.py",
    "cew_gate_authority/replay.py",
    "cew_gate_authority/types.py",
    "governance/cew-gate-authority/authorities/N12_CEW_CONTRACT_01_A0.json",
    "governance/cew-gate-authority/schemas/QUALIFICATION_RECEIPT_v1.schema.json",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def blob_sha(path: str) -> str:
    return subprocess.check_output(["git", "hash-object", path], text=True).strip()


def bundle_digest(components: dict[str, str]) -> str:
    payload = "".join(f"{path}\0{components[path]}\n" for path in sorted(components)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class G0ManifestTests(unittest.TestCase):
    def test_manifest_binds_exact_runtime_a0_and_receipt_schema_blobs(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_id"], "CEW_GATE_CORE_MANIFEST")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["gate_core_version"], "G0")
        self.assertEqual(manifest["commit_binding"], "HUMAN_PROMOTION_RECORD_REQUIRED")
        components = {item["path"]: item["git_blob_sha"] for item in manifest["source_components"]}
        self.assertEqual(set(components), EXPECTED_COMPONENTS)
        for path, expected in components.items():
            self.assertRegex(expected, SHA40)
            self.assertEqual(blob_sha(path), expected, path)
        self.assertEqual(manifest["source_bundle_algorithm"], "sha256(sorted(path + NUL + git_blob_sha + LF))")
        self.assertEqual(manifest["source_bundle_sha256"], bundle_digest(components))

    def test_toolchain_has_only_reviewed_immutable_action_pins_and_binary_digests(self):
        toolchain = json.loads(TOOLCHAIN.read_text(encoding="utf-8"))
        self.assertEqual(toolchain["schema_id"], "CEW_GATE_AUTHORITY_TRUSTED_TOOLCHAIN")
        self.assertEqual(toolchain["schema_version"], 1)
        self.assertEqual(toolchain["runner"], "ubuntu-24.04")
        actions = toolchain["github_actions"]
        self.assertEqual(actions["actions/checkout"], "11d5960a326750d5838078e36cf38b85af677262")
        self.assertEqual(actions["actions/setup-python"], "a26af69be951a213d495a4c3e4e4022e16d87065")
        self.assertEqual(actions["github/codeql-action"], "24c54180a607b1449ed407dd24f251e4e9147c8d")
        for value in actions.values():
            self.assertRegex(value, SHA40)
        self.assertEqual(toolchain["binaries"]["actionlint"]["version"], "1.7.12")
        self.assertEqual(toolchain["binaries"]["actionlint"]["sha256_linux_amd64"], "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8")
        self.assertEqual(toolchain["binaries"]["zizmor"]["version"], "1.30.1")
        self.assertEqual(toolchain["binaries"]["zizmor"]["sha256_linux_x86_64"], "e65324f4430c2717591937edcec90ccbefaf14c174f8ec9415e03ca875b46e1a")
        for binary in toolchain["binaries"].values():
            self.assertRegex(next(value for key, value in binary.items() if key.startswith("sha256_")), SHA256)


if __name__ == "__main__":
    unittest.main()
