from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
import unittest

try:
    from experiments.cew_col03c.source_materialization import (
        TAV07_SOURCE,
        build_pdf_source_metadata,
        canonical_source_digest,
        verify_materialized_source,
    )
except (ImportError, ModuleNotFoundError):
    TAV07_SOURCE = None
    build_pdf_source_metadata = None
    canonical_source_digest = None
    verify_materialized_source = None


# Minimal, valid, one-page PDF with a deterministic byte representation.
_MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 100]/Resources<<>>>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n194\n%%EOF\n"
)


class SourceMaterializationTests(unittest.TestCase):
    def test_tav07_contract_is_frozen(self):
        self.assertIsNotNone(TAV07_SOURCE, "TAV.7 materialization implementation missing")
        self.assertEqual(TAV07_SOURCE["catalogue_id"], "TAV-07A")
        self.assertEqual(TAV07_SOURCE["archive_commit"], "78c20a52db4f391ce0d13b9705b9f04737e218c9")
        self.assertEqual(TAV07_SOURCE["path"], "archive/documentazione_originaria/tavola7.pdf")
        self.assertEqual(TAV07_SOURCE["sha256"], "38a0cce18dcda0b9a36d8473f0d428735c4b89934975d551d4bfffd24fe54a2b")
        self.assertEqual(TAV07_SOURCE["repository_blob"], "bf92501e723843fd912976b1b711285a61c548d3")
        self.assertEqual(TAV07_SOURCE["size_bytes"], 798816)
        self.assertEqual(TAV07_SOURCE["class"], "particolari_strutturali")
        self.assertEqual(TAV07_SOURCE["state"], "DOC")

    def test_wrong_digest_fails_closed(self):
        self.assertIsNotNone(verify_materialized_source, "TAV.7 materialization implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tavola7.pdf"
            path.write_bytes(b"wrong")
            contract = dict(TAV07_SOURCE)
            contract["size_bytes"] = len(b"wrong")
            with self.assertRaisesRegex(ValueError, "PROVENANCE_MISMATCH"):
                verify_materialized_source(path, contract, allow_test_digest_override=True)

    def test_wrong_archive_contract_fails_closed_before_bytes(self):
        self.assertIsNotNone(verify_materialized_source, "TAV.7 materialization implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tavola7.pdf"
            path.write_bytes(b"x")
            contract = dict(TAV07_SOURCE)
            contract["archive_commit"] = "0" * 40
            contract["sha256"] = hashlib.sha256(b"x").hexdigest()
            contract["size_bytes"] = 1
            with self.assertRaisesRegex(ValueError, "source contract drift"):
                verify_materialized_source(path, contract)

    def test_exact_synthetic_contract_can_verify_bytes_without_promoting_authority(self):
        self.assertIsNotNone(verify_materialized_source, "TAV.7 materialization implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tavola7.pdf"
            path.write_bytes(_MINIMAL_PDF)
            contract = dict(TAV07_SOURCE)
            contract["sha256"] = hashlib.sha256(_MINIMAL_PDF).hexdigest()
            contract["size_bytes"] = len(_MINIMAL_PDF)
            verified = verify_materialized_source(path, contract, allow_test_digest_override=True)
            self.assertEqual(verified["materialization_state"], "MATERIALIZED_VERIFIED")
            self.assertEqual(verified["authority"], "PRIMARY_DOCUMENTARY_SOURCE")
            self.assertFalse(verified["identity_promotion_authorized"])

    def test_pdf_metadata_is_deterministic_and_keeps_pdf_as_authority(self):
        self.assertIsNotNone(build_pdf_source_metadata, "TAV.7 metadata implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tavola7.pdf"
            path.write_bytes(_MINIMAL_PDF)
            contract = dict(TAV07_SOURCE)
            contract["sha256"] = hashlib.sha256(_MINIMAL_PDF).hexdigest()
            contract["size_bytes"] = len(_MINIMAL_PDF)
            first = build_pdf_source_metadata(path, contract, allow_test_digest_override=True)
            second = build_pdf_source_metadata(path, contract, allow_test_digest_override=True)
            self.assertEqual(first, second)
            self.assertEqual(first["page_count"], 1)
            self.assertEqual(first["authority"], "PRIMARY_DOCUMENTARY_SOURCE")
            self.assertEqual(first["derivative_policy"]["authority"], "DERIVATIVE_EVIDENCE_ONLY")
            self.assertEqual(first["derivative_policy"]["target_dpi"], 300)
            self.assertEqual(canonical_source_digest(first), canonical_source_digest(second))

    def test_unreadable_or_zero_page_pdf_cannot_qualify(self):
        self.assertIsNotNone(build_pdf_source_metadata, "TAV.7 metadata implementation missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tavola7.pdf"
            data = b"not-a-pdf"
            path.write_bytes(data)
            contract = dict(TAV07_SOURCE)
            contract["sha256"] = hashlib.sha256(data).hexdigest()
            contract["size_bytes"] = len(data)
            with self.assertRaisesRegex(ValueError, "PDF_RECONSTRUCTION_FAILED"):
                build_pdf_source_metadata(path, contract, allow_test_digest_override=True)


if __name__ == "__main__":
    unittest.main()
