from __future__ import annotations

import unittest

try:
    from experiments.cew_col03c.derived_reference_quality import (
        FROZEN_ARCHIVE_COMMIT,
        audit_candidate_matrix_reference,
        audit_topology_reference,
        materialize_reference_descriptor,
    )
except (ImportError, ModuleNotFoundError):
    FROZEN_ARCHIVE_COMMIT = None
    audit_candidate_matrix_reference = None
    audit_topology_reference = None
    materialize_reference_descriptor = None


NODES = [
    {"nodo": "N001", "x_mm": "1", "y_mm": "2", "stato": "PREDOC_TOPOLOGICO"},
    {"nodo": "N002", "x_mm": "3", "y_mm": "4", "stato": "PREDOC_TOPOLOGICO"},
]
CONNECTIONS = [
    {"id": "C001", "nodo_1": "N001", "nodo_2": "N002", "stato": "INF_DA_QUOTARE"},
    {"id": "C002", "nodo_1": "N002", "nodo_2": "N003", "stato": "INF_DA_QUOTARE"},
]
MATRIX = [
    {"hypothesis": "HYP_A", "segment": "C1", "candidate_from": "N001", "candidate_to": "N002", "evidence_status": "CANDIDATO_METRICO_SOLO"},
    {"hypothesis": "HYP_B", "segment": "C1", "candidate_from": "N010", "candidate_to": "N025", "evidence_status": "CANDIDATO_TOPOLOGICO_DEBOLE"},
]


class DerivedReferenceQualityTests(unittest.TestCase):
    def test_frozen_archive_commit_is_exact(self):
        self.assertIsNotNone(materialize_reference_descriptor, "derived-reference implementation missing")
        self.assertEqual(FROZEN_ARCHIVE_COMMIT, "78c20a52db4f391ce0d13b9705b9f04737e218c9")

    def test_reference_descriptor_requires_exact_archive_commit_and_sha(self):
        self.assertIsNotNone(materialize_reference_descriptor, "derived-reference implementation missing")
        with self.assertRaisesRegex(ValueError, "archive commit"):
            materialize_reference_descriptor(
                path="data/canonical/example.csv",
                archive_commit="0" * 40,
                bytes_sha256="a" * 64,
                rows=NODES,
            )
        with self.assertRaisesRegex(ValueError, "sha256"):
            materialize_reference_descriptor(
                path="data/canonical/example.csv",
                archive_commit=FROZEN_ARCHIVE_COMMIT,
                bytes_sha256="bad",
                rows=NODES,
            )

    def test_topology_unknown_endpoint_blocks_identity_use_without_synthesizing_node(self):
        self.assertIsNotNone(audit_topology_reference, "derived-reference implementation missing")
        provenance = materialize_reference_descriptor(
            path="data/canonical/tav5_topology_nodes_57.csv",
            archive_commit=FROZEN_ARCHIVE_COMMIT,
            bytes_sha256="1" * 64,
            rows=NODES,
        )
        result = audit_topology_reference(nodes=NODES, connections=CONNECTIONS, provenance=provenance)
        self.assertEqual(result["node_row_count"], 2)
        self.assertEqual(result["connection_row_count"], 2)
        self.assertEqual(result["declared_node_ids"], ["N001", "N002"])
        self.assertEqual(result["referenced_endpoint_ids"], ["N001", "N002", "N003"])
        self.assertEqual(result["unresolved_endpoint_ids"], ["N003"])
        self.assertEqual(result["identity_use_state"], "DATA_QUALITY_BLOCKED")
        self.assertFalse(result["identity_evidence_usable"])
        self.assertNotIn("N003", result["declared_node_ids"])

    def test_connection_count_comes_from_rows_not_historical_claim(self):
        self.assertIsNotNone(audit_topology_reference, "derived-reference implementation missing")
        provenance = materialize_reference_descriptor(
            path="data/canonical/tav5_topology_connections_v07.csv",
            archive_commit=FROZEN_ARCHIVE_COMMIT,
            bytes_sha256="2" * 64,
            rows=CONNECTIONS,
        )
        result = audit_topology_reference(
            nodes=NODES,
            connections=CONNECTIONS,
            provenance=provenance,
            historical_inventory_claim={"connection_count": 38, "node_count": 57},
        )
        self.assertEqual(result["connection_row_count"], 2)
        self.assertEqual(result["historical_inventory_claim"]["connection_count"], 38)
        self.assertNotEqual(result["connection_row_count"], result["historical_inventory_claim"]["connection_count"])

    def test_topology_quality_digest_is_row_order_invariant(self):
        self.assertIsNotNone(audit_topology_reference, "derived-reference implementation missing")
        provenance = materialize_reference_descriptor(
            path="data/canonical/tav5_topology_connections_v07.csv",
            archive_commit=FROZEN_ARCHIVE_COMMIT,
            bytes_sha256="3" * 64,
            rows=CONNECTIONS,
        )
        first = audit_topology_reference(nodes=NODES, connections=CONNECTIONS, provenance=provenance)
        second = audit_topology_reference(nodes=list(reversed(NODES)), connections=list(reversed(CONNECTIONS)), provenance=provenance)
        self.assertEqual(first["quality_digest"], second["quality_digest"])

    def test_candidate_matrix_is_reference_only_and_not_historical_27x5(self):
        self.assertIsNotNone(audit_candidate_matrix_reference, "derived-reference implementation missing")
        provenance = materialize_reference_descriptor(
            path="data/canonical/telaio5_tav5_candidate_matrix_v1.csv",
            archive_commit=FROZEN_ARCHIVE_COMMIT,
            bytes_sha256="4" * 64,
            rows=MATRIX,
        )
        result = audit_candidate_matrix_reference(rows=MATRIX, provenance=provenance)
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["reference_role"], "CANDIDATE_HYPOTHESES_ONLY")
        self.assertFalse(result["historical_27x5_matrix"])
        self.assertFalse(result["identity_evidence_usable"])
        self.assertEqual(result["authority"], "REFERENCE_ONLY")


if __name__ == "__main__":
    unittest.main()
