from __future__ import annotations

ROUTE_SCHEMA = "CEW_SPIRAL_ROUTE_DECISION_v1"
ROUTE_RECEIPT_SCHEMA = "CEW_SPIRAL_ROUTE_RECEIPT_v1"

COST_RANK = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
}

CLOSED_AUTHORITY_KEYS = {
    "structural_identity_authorized",
    "canonical_geometry_authorized",
    "canonical_write_authorized",
    "m0g_authorized",
    "family_assignment_authorized",
    "section_assignment_authorized",
}

ROUTES = {
    "QUALIFIED_SOURCE_NATIVE",
    "GOVERNED_RASTER_OCR",
    "MANUAL_OR_NEW_PRIMARY_EVIDENCE",
}
