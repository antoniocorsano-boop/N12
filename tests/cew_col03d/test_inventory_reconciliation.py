from __future__ import annotations

import unittest

try:
    from experiments.cew_col03d.inventory_reconciliation import (
        REQUIRED_V25_MEMBER_NAMES,
        classify_member_request,
        reconcile_required_members,
    )
except (ImportError, ModuleNotFoundError):
    REQUIRED_V25_MEMBER_NAMES = None
    classify_member_request = None
    reconcile_required_members = None


INVENTORY_TEXT = """# Inventario artefatti storici

## Pacchetto DXF strutturale v25

Artefatti verificati come presenti:

- `TAV5_CARPENTERIA.dxf`
- `TAV6_TRAVI.dxf`
- `TAV7_PILASTRI.dxf`
- `ABACO_TOPOLOGICO_TAV5_v11.csv`
- `ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv`
- `MATRICE_PILASTRI_27x5_v22.csv`
- `ABACO_TRAVI_TAV6_v23.csv`
- `ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv`
- ulteriori DXF di controllo relativi a catene verticali, tipi di pilastro e famiglie di travi.

## Interpretazione

Le associazioni geometriche restano proposte geometriche.
"""

EXPECTED_NAMES = [
    "ABACO_ASSOCIAZIONE_PILASTRI_TAV5_TAV7_v19.csv",
    "ABACO_TOPOLOGICO_TAV5_v11.csv",
    "ABACO_TRAVI_TAV6_v23.csv",
    "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv",
    "MATRICE_PILASTRI_27x5_v22.csv",
    "TAV5_CARPENTERIA.dxf",
    "TAV6_TRAVI.dxf",
    "TAV7_PILASTRI.dxf",
]


class HistoricalInventoryReconciliationTests(unittest.TestCase):
    def test_required_v25_members_are_derived_from_governed_inventory(self):
        self.assertIsNotNone(reconcile_required_members, "COL-03D inventory reconciliation missing")
        rows = reconcile_required_members(INVENTORY_TEXT, EXPECTED_NAMES)
        self.assertEqual([row["artifact_name"] for row in rows], EXPECTED_NAMES)
        self.assertTrue(all(row["governed_inventory_member"] for row in rows))
        self.assertTrue(all(row["package_presence_state"] == "PRESENT" for row in rows))
        self.assertTrue(all(row["materialization_state"] == "PACKAGE_MEMBER_DISCOVERED" for row in rows))
        self.assertTrue(all(row["promotion_authorized"] is False for row in rows))

    def test_registered_member_missing_from_package_is_inventory_package_mismatch(self):
        self.assertIsNotNone(reconcile_required_members, "COL-03D inventory reconciliation missing")
        zip_names = [name for name in EXPECTED_NAMES if name != "TAV7_PILASTRI.dxf"]
        rows = reconcile_required_members(INVENTORY_TEXT, zip_names)
        tav7 = next(row for row in rows if row["artifact_name"] == "TAV7_PILASTRI.dxf")
        self.assertEqual(tav7["package_presence_state"], "ABSENT")
        self.assertEqual(tav7["materialization_state"], "INVENTORY_PACKAGE_MISMATCH")
        self.assertFalse(tav7["promotion_authorized"])

    def test_obsolete_synthetic_beam_name_is_not_in_governed_inventory(self):
        self.assertIsNotNone(classify_member_request, "COL-03D member request classifier missing")
        result = classify_member_request(
            "TABELLA_CORRISPONDENZE_TRAVI_v25.csv",
            INVENTORY_TEXT,
            EXPECTED_NAMES,
        )
        self.assertFalse(result["governed_inventory_member"])
        self.assertEqual(result["materialization_state"], "NOT_IN_GOVERNED_INVENTORY")
        self.assertFalse(result["promotion_authorized"])

    def test_actual_v25_beam_association_name_is_governed_and_present(self):
        self.assertIsNotNone(classify_member_request, "COL-03D member request classifier missing")
        result = classify_member_request(
            "ASSOCIAZIONE_TRAVI_TAV5_TAV6_v25.csv",
            INVENTORY_TEXT,
            EXPECTED_NAMES,
        )
        self.assertTrue(result["governed_inventory_member"])
        self.assertEqual(result["materialization_state"], "PACKAGE_MEMBER_DISCOVERED")
        self.assertFalse(result["promotion_authorized"])

    def test_required_member_policy_matches_inventory_exactly(self):
        self.assertIsNotNone(REQUIRED_V25_MEMBER_NAMES, "COL-03D required-member policy missing")
        self.assertEqual(sorted(REQUIRED_V25_MEMBER_NAMES), EXPECTED_NAMES)


if __name__ == "__main__":
    unittest.main()
