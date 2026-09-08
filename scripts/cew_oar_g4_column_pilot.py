#!/usr/bin/env python3
"""Governed adapter for the G4 / TAV-05S column OAR pilot.

The pilot now consumes a canonical CEW SourceVersion and Page plus the registered
300 dpi derivative/page transform. Per-object EvidenceRegion identifiers are
still deliberately absent: candidates remain reviewable in OA-1, while CAD
promotion stays fail-closed until each support is geometrically bound and a
separate human OAR confirmation exists.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from cew_object_acquisition import (
    CandidateState,
    EvidenceProvenance,
    ObjectCandidate,
    ObjectSignature,
    ObjectType,
)
from cew_object_workbench import build_object_workbench_view

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "automation" / "CEW_OAR_G4_COLUMN_PILOT_INPUT_v1.json"


def _row_evidence_fingerprint(payload: dict, support_id: str, family_id: str) -> str:
    governed = {
        "pilot_id": payload["pilot_id"],
        "support_id": support_id,
        "family_id": family_id,
        "source": payload["source"],
        "semantic_audit": payload["semantic_audit"],
        "cew_binding": payload["cew_binding"],
    }
    encoded = json.dumps(governed, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def load_g4_column_candidates(path: Path = DEFAULT_INPUT) -> list[ObjectCandidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    families = payload["families"]
    binding = payload["cew_binding"]
    candidates: list[ObjectCandidate] = []

    for grouping in payload["objects"]:
        family_id = grouping["family_id"]
        family = families[family_id]
        for support_id in grouping["support_ids"]:
            evidence_fp = _row_evidence_fingerprint(payload, support_id, family_id)
            candidates.append(
                ObjectCandidate(
                    evidence_object_id=f"EOBJ-G4-SUPPORT-{support_id}",
                    object_type=ObjectType.COLUMN,
                    family_id=family_id,
                    signature=ObjectSignature(
                        cad_topology={"primitive": "RECTANGULAR_SUPPORT_SYMBOL"},
                        shape={
                            "kind": "RECT",
                            "ratio": family["section_x_cm"] / family["section_y_cm"],
                        },
                        dimensions={
                            "section_x_cm": family["section_x_cm"],
                            "section_y_cm": family["section_y_cm"],
                        },
                        orientation=family["orientation_class"],
                        associated_text=(
                            f"{family['section_x_cm']}x{family['section_y_cm']}",
                        ),
                        context={
                            "storey": payload["source"]["storey_id"],
                            "drawing": payload["source"]["source_sheet"],
                            "support_id": support_id,
                            "evidence_status": payload["source"]["evidence_status"],
                            "source_validation_state": payload["source"]["source_validation_state"],
                            "source_blob_sha": payload["source"]["primary_source_blob_sha"],
                            "source_sha256": payload["source"]["primary_source_sha256"],
                            "render_role": payload["source"]["render_role"],
                            "derived_asset_id": binding["derived_asset_id"],
                            "page_transform_id": binding["page_transform_id"],
                        },
                    ),
                    provenance=EvidenceProvenance(
                        source_version_id=binding["source_version_id"],
                        page_id=binding["page_id"],
                        evidence_region_id="",
                        evidence_fingerprint=evidence_fp,
                        registration_id=None,
                    ),
                    state=CandidateState.CANDIDATE,
                )
            )
    return candidates


def build_g4_column_pilot_workbench(path: Path = DEFAULT_INPUT) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    binding = payload["cew_binding"]
    view = build_object_workbench_view(load_g4_column_candidates(path))
    view["pilot"] = {
        "id": payload["pilot_id"],
        "source_scope": "TAV-05S / G4",
        "source_registration": "DIRECT_REGISTERED_DOCUMENT_EVIDENCE",
        "source_version_id": binding["source_version_id"],
        "page_id": binding["page_id"],
        "derived_asset_id": binding["derived_asset_id"],
        "page_transform_id": binding["page_transform_id"],
        "source_page_binding": "READY",
        "oar_human_confirmation": "NOT_ASSERTED",
        "evidence_region_binding": binding["evidence_region_binding"],
        "next_gate": "BIND_PER_OBJECT_EVIDENCE_REGIONS",
    }
    return view


def main() -> None:
    view = build_g4_column_pilot_workbench()
    print(json.dumps(view, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
