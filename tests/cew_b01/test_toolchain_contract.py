import importlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "governance" / "cew-b01" / "EXTERNAL_TOOLCHAIN_v1.json"
LOCK = ROOT / "requirements" / "cew-b01.lock.txt"
TOOLCHAIN_MODULE = ROOT / "cew_b01" / "toolchain.py"

EXPECTED_TOOLS = {
    "docling",
    "docling-parse",
    "pypdfium2",
    "pdfplumber",
    "ocrmypdf",
    "tesseract",
    "opencv",
    "ezdxf",
    "build123d",
    "ocp",
    "cadcraft",
}

ALLOWED_SLICE_STATUSES = {
    "ADOPT",
    "ADOPT_BENCHMARK_N12",
    "ADOPT_CONDITIONAL",
    "FOUNDATION",
    "DEFER_FOR_THIS_SLICE_NO_IMMUTABLE_DXF_SOURCE",
    "BENCHMARK_N12_NON_CORE",
}


def _require_step2_files(testcase: unittest.TestCase) -> None:
    missing = [str(path.relative_to(ROOT)) for path in (MANIFEST, LOCK, TOOLCHAIN_MODULE) if not path.exists()]
    testcase.assertFalse(missing, f"Step 2 governed files are missing: {missing}")


class ToolchainContractTests(unittest.TestCase):
    def load_manifest(self):
        _require_step2_files(self)
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def load_module(self):
        _require_step2_files(self)
        return importlib.import_module("cew_b01.toolchain")

    def test_governed_files_exist(self):
        _require_step2_files(self)

    def test_manifest_has_exact_required_tool_set_and_metadata(self):
        manifest = self.load_manifest()
        self.assertEqual(manifest["schema_id"], "CEW_B01_EXTERNAL_TOOLCHAIN")
        self.assertEqual(manifest["schema_version"], 1)
        tools = manifest["tools"]
        self.assertEqual({item["tool_id"] for item in tools}, EXPECTED_TOOLS)
        for item in tools:
            self.assertIn(item["slice_status"], ALLOWED_SLICE_STATUSES)
            self.assertIsInstance(item["blocking"], bool)
            self.assertTrue(item["license"])
            self.assertTrue(item["source"])

    def test_required_python_packages_are_exact_pinned_and_pymupdf_is_absent(self):
        manifest = self.load_manifest()
        lock_text = LOCK.read_text(encoding="utf-8")
        self.assertNotIn("pymupdf", lock_text.lower())
        pins = {}
        for raw in lock_text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            self.assertRegex(line, r"^[A-Za-z0-9_.-]+==[^=\s]+$")
            name, version = line.split("==", 1)
            pins[name.lower()] = version

        for item in manifest["tools"]:
            package = item.get("python_package")
            if package and item.get("install_for_slice", False):
                self.assertIn(package.lower(), pins, package)
                self.assertEqual(pins[package.lower()], item["version"])

    def test_ocr_is_conditional(self):
        manifest = self.load_manifest()
        by_id = {item["tool_id"]: item for item in manifest["tools"]}
        self.assertEqual(by_id["ocrmypdf"]["slice_status"], "ADOPT_CONDITIONAL")
        self.assertEqual(by_id["tesseract"]["slice_status"], "ADOPT_CONDITIONAL")
        self.assertEqual(by_id["ocrmypdf"]["execution_mode"], "CONDITIONAL_TRIGGER_ONLY")
        self.assertEqual(by_id["tesseract"]["execution_mode"], "CONDITIONAL_TRIGGER_ONLY")

    def test_ezdxf_is_deferred_for_this_slice_without_real_dxf(self):
        manifest = self.load_manifest()
        by_id = {item["tool_id"]: item for item in manifest["tools"]}
        self.assertEqual(
            by_id["ezdxf"]["slice_status"],
            "DEFER_FOR_THIS_SLICE_NO_IMMUTABLE_DXF_SOURCE",
        )
        self.assertFalse(by_id["ezdxf"]["blocking"])
        self.assertFalse(by_id["ezdxf"]["install_for_slice"])

    def test_cadcraft_is_separate_and_non_blocking(self):
        manifest = self.load_manifest()
        by_id = {item["tool_id"]: item for item in manifest["tools"]}
        self.assertEqual(by_id["cadcraft"]["slice_status"], "BENCHMARK_N12_NON_CORE")
        self.assertFalse(by_id["cadcraft"]["blocking"])
        self.assertFalse(by_id["cadcraft"]["install_for_slice"])

    def test_validator_rejects_unknown_status_and_pymupdf_dependency(self):
        module = self.load_module()
        manifest = self.load_manifest()
        bad_status = json.loads(json.dumps(manifest))
        bad_status["tools"][0]["slice_status"] = "UNKNOWN"
        with self.assertRaises(module.ToolchainContractError):
            module.ToolchainContract.from_mapping(bad_status)

        bad_dep = json.loads(json.dumps(manifest))
        bad_dep["required_python_packages"] = ["PyMuPDF==1.0.0"]
        with self.assertRaises(module.ToolchainContractError):
            module.ToolchainContract.from_mapping(bad_dep)


if __name__ == "__main__":
    unittest.main()
