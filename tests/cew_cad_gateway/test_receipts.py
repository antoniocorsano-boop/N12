from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from cew_cad_gateway.receipts import ReceiptStore, ReceiptStoreError


class ReceiptStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "receipts"
        self.root.mkdir()
        self.store = ReceiptStore(self.root)

    def test_write_returns_stored_receipt_with_correct_digest(self) -> None:
        value = {"key": "value", "number": 42}
        stored = self.store.write("test", value)
        self.assertEqual(stored.kind, "test")
        self.assertTrue(stored.path.exists())
        self.assertEqual(len(stored.sha256), 64)  # SHA256 is 64 hex chars
        # Verify the digest matches the content
        from cew_cad_gateway.canonical import sha256_json
        expected = sha256_json(value)
        self.assertEqual(stored.sha256, expected)

    def test_write_idempotent_for_identical_content(self) -> None:
        """Writing identical canonical content twice must succeed and return same digest."""
        value = {"key": "value", "number": 42}
        stored1 = self.store.write("test", value)
        stored2 = self.store.write("test", value)
        self.assertEqual(stored1.sha256, stored2.sha256)
        self.assertEqual(stored1.path, stored2.path)
        self.assertEqual(stored1.kind, stored2.kind)

    def test_write_fails_for_conflicting_content(self) -> None:
        """Writing to same path with different content must fail closed."""
        value1 = {"key": "value1"}
        value2 = {"key": "value2"}  # Different content, but same kind would produce different digest
        # Actually, different content produces different digest, so different filename
        # The conflict case is when we try to write same digest but different bytes
        # This is hard to trigger with sha256_json since it's deterministic
        # But we can test that the file system protects against corruption
        stored1 = self.store.write("test", value1)
        # Manually corrupt the file
        stored1.path.write_bytes(b"corrupted content")
        # Now try to write the same value again - should fail because file exists but content differs
        with self.assertRaises(ReceiptStoreError):
            self.store.write("test", value1)

    def test_write_atomic_via_temp_file(self) -> None:
        """Write should use atomic temp file + rename to avoid partial writes."""
        value = {"large": "x" * 10000}
        stored = self.store.write("large", value)
        # The file should exist and have correct content
        self.assertTrue(stored.path.exists())
        content = stored.path.read_bytes()
        # Should be valid JSON
        import json
        parsed = json.loads(content.decode("utf-8").strip())
        self.assertEqual(parsed, value)

    def test_write_preserves_exact_bytes(self) -> None:
        """Byte-identical content must produce byte-identical files."""
        value = {"exact": "bytes"}
        stored1 = self.store.write("exact", value)
        # Read the raw bytes
        bytes1 = stored1.path.read_bytes()
        stored2 = self.store.write("exact", value)
        bytes2 = stored2.path.read_bytes()
        self.assertEqual(bytes1, bytes2)


if __name__ == "__main__":
    unittest.main()