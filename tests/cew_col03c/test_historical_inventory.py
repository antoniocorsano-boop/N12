from __future__ import annotations

import unittest

try:
    from experiments.cew_col03c.historical_inventory import (
        classify_historical_artifact,
        parse_historical_inventory,
        require_row_level_evidence_usable,
    )
except (ImportError, ModuleNotFoundError):
    classify_historical_artifact = None
    parse_historical_inventory = None
    require_row_level_evidence_usable = None


INVENTORY = """# Artefatti storici recuperati

### TAV7_PILASTRI.dxf
- Ricostruito dai pacchetti storici v25 e v51.
- Catena di 27 pilastri dal livello 5 al livello 1.

### ABACO_TOPOLOGICO_TAV5_v11.csv
- Estratto dal pacchetto v19.
- 57 nodi, 38 connessioni, 10 componenti.

### ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv
- Estratto dal pacchetto v19.

### MATRICE_PILASTRI_27x5_v22.csv
- Estratta dal pacchetto v22.
"""


class HistoricalInventoryTests(unittest.TestCase):
    def test_inventory_parsing_preserves_artifact_names_and_package_refs(self):
        self.assertIsNotNone(parse_historical_inventory, "historical inventory implementation missing")
        rows = parse_historical_inventory(INVENTORY, source_ref="commit:643dc893:archive/ARTEFATTI_STORICI.md")
        by_name = {row["artifact_name"]: row for row in rows}
        self.assertEqual(set(by_name), {
            "TAV7_PILASTRI.dxf",
            "ABACO_TOPOLOGICO_TAV5_v11.csv",
            "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
            "MATRICE_PILASTRI_27x5_v22.csv",
        })
        self.assertEqual(by_name["TAV7_PILASTRI.dxf"]["historical_package_refs"], ["v25", "v51"])
        self.assertEqual(by_name["MATRICE_PILASTRI_27x5_v22.csv"]["historical_package_refs"], ["v22"])

    def test_inventory_only_artifact_is_not_materialized(self):
        self.assertIsNotNone(classify_historical_artifact, "historical inventory implementation missing")
        record = {
            "artifact_name": "MATRICE_PILASTRI_27x5_v22.csv",
            "inventory_source_ref": "commit:643dc893:archive/ARTEFATTI_STORICI.md",
            "historical_package_refs": ["v22"],
        }
        classified = classify_historical_artifact(record, materialized_path=None, sha256=None)
        self.assertEqual(classified["materialization_state"], "KNOWN_INVENTORY_NOT_MATERIALIZED")
        self.assertFalse(classified["bytes_available"])
        self.assertFalse(classified["row_level_evidence_usable"])
        self.assertEqual(classified["authority"], "REFERENCE_ONLY")

    def test_inventory_only_artifact_cannot_be_used_as_row_level_evidence(self):
        self.assertIsNotNone(require_row_level_evidence_usable, "historical inventory implementation missing")
        record = {
            "artifact_name": "TAV7_PILASTRI.dxf",
            "materialization_state": "KNOWN_INVENTORY_NOT_MATERIALIZED",
            "row_level_evidence_usable": False,
        }
        with self.assertRaisesRegex(ValueError, "not materialized|row-level"):
            require_row_level_evidence_usable(record)

    def test_materialized_bytes_without_expected_provenance_do_not_qualify(self):
        self.assertIsNotNone(classify_historical_artifact, "historical inventory implementation missing")
        record = {
            "artifact_name": "ABACO_TOPOLOGICO_TAV5_v11.csv",
            "inventory_source_ref": "commit:643dc893:archive/ARTEFATTI_STORICI.md",
            "historical_package_refs": ["v19"],
        }
        classified = classify_historical_artifact(
            record,
            materialized_path="/tmp/ABACO_TOPOLOGICO_TAV5_v11.csv",
            sha256="a" * 64,
        )
        self.assertEqual(classified["materialization_state"], "PROVENANCE_MISMATCH")
        self.assertFalse(classified["row_level_evidence_usable"])


if __name__ == "__main__":
    unittest.main()
