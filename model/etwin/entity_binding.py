"""
Task 6: eTwin Entity/Candidate Binding
Bind terrace entities to eTwin properties.
N002/N005/N039 = StructuralEntity (CONFIRMED)
N041 = DocumentEntityCandidate (CANDIDATE, R-R1-01 active)
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from model.etwin.document_engine import (
    StructuralEntity, DocumentEntityCandidate, PropertyResolution,
    Claim, EvidenceCrop, EntityIdentityStatus, save_json
)

CROPS_DIR = Path(r"docs\FOGLIO_LAVORO\etwin_crops\terrace_evidence")


def load_evidence_crops() -> list[dict]:
    """Load the evidence crops manifest."""
    manifest_path = CROPS_DIR / "evidence_crops.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_terrace_entities() -> dict:
    """Build entity/candidate bindings for terrace region."""
    crops = load_evidence_crops()

    # Find crop by evidence_id
    def find_crop(eid: str) -> dict | None:
        for c in crops:
            if c["evidence_id"] == eid:
                return c
        return None

    entities = {}
    resolutions = []
    claims = []

    # --- N002: CONFIRMED StructuralEntity ---
    n002_crop = find_crop("EV-PILLAR-N002")
    n002_entity = StructuralEntity(
        entity_id="N002",
        entity_type="Column",
        identity_status=EntityIdentityStatus.CONFIRMED,
        position_x_mm=36481.0,
        position_y_mm=12234.0,
        vertical_start="G1",
        vertical_end="G5",
        termination_reason="continues_above",
        evidence_ids=["EV-PILLAR-N002"],
        notes="LINE in DXF, verify=A, type=A02/N002/ES",
    )
    entities["N002"] = n002_entity

    n002_claim = Claim(
        claim_id="CLM-N002-TERM",
        entity_id="N002",
        property_name="verticalTermination",
        property_value="continues_above",
        evidence_refs=["EV-PILLAR-N002"],
        source_document_id="TAV-05S",
        confidence=0.9,
        notes="DXF marks LINE, R1 corrected to stop at G1 for terrace",
    )
    claims.append(n002_claim)

    resolutions.append(PropertyResolution(
        resolution_id="RES-N002-TERM",
        entity_id="N002",
        property_name="verticalTermination",
        claim_id="CLM-N002-TERM",
        evidence_id="EV-PILLAR-N002",
        crop_path=n002_crop["crop_path"] if n002_crop else "",
        document_id="TAV-05S",
        page_number=1,
        status="RESOLVED",
    ))

    # --- N005: CONFIRMED StructuralEntity ---
    n005_crop = find_crop("EV-PILLAR-N005")
    n005_entity = StructuralEntity(
        entity_id="N005",
        entity_type="Column",
        identity_status=EntityIdentityStatus.CONFIRMED,
        position_x_mm=36484.0,
        position_y_mm=7840.0,
        vertical_start="G1",
        vertical_end="G5",
        termination_reason="continues_above",
        evidence_ids=["EV-PILLAR-N005"],
        notes="LINE in DXF, verify=A, type=A03/N005/ES",
    )
    entities["N005"] = n005_entity

    n005_claim = Claim(
        claim_id="CLM-N005-TERM",
        entity_id="N005",
        property_name="verticalTermination",
        property_value="continues_above",
        evidence_refs=["EV-PILLAR-N005"],
        source_document_id="TAV-05S",
        confidence=0.9,
        notes="DXF marks LINE, R1 corrected to stop at G1 for terrace",
    )
    claims.append(n005_claim)

    resolutions.append(PropertyResolution(
        resolution_id="RES-N005-TERM",
        entity_id="N005",
        property_name="verticalTermination",
        claim_id="CLM-N005-TERM",
        evidence_id="EV-PILLAR-N005",
        crop_path=n005_crop["crop_path"] if n005_crop else "",
        document_id="TAV-05S",
        page_number=1,
        status="RESOLVED",
    ))

    # --- N039: CONFIRMED StructuralEntity ---
    n039_crop = find_crop("EV-PILLAR-N039")
    n039_entity = StructuralEntity(
        entity_id="N039",
        entity_type="Column",
        identity_status=EntityIdentityStatus.CONFIRMED,
        position_x_mm=35456.0,
        position_y_mm=3226.0,
        vertical_start="G1",
        vertical_end="G5",
        termination_reason="continues_above",
        evidence_ids=["EV-PILLAR-N039"],
        notes="LINE in DXF, verify=A, type=A22/N039/EN",
    )
    entities["N039"] = n039_entity

    n039_claim = Claim(
        claim_id="CLM-N039-TERM",
        entity_id="N039",
        property_name="verticalTermination",
        property_value="continues_above",
        evidence_refs=["EV-PILLAR-N039"],
        source_document_id="TAV-05S",
        confidence=0.9,
        notes="DXF marks LINE, R1 corrected to stop at G1 for terrace",
    )
    claims.append(n039_claim)

    resolutions.append(PropertyResolution(
        resolution_id="RES-N039-TERM",
        entity_id="N039",
        property_name="verticalTermination",
        claim_id="CLM-N039-TERM",
        evidence_id="EV-PILLAR-N039",
        crop_path=n039_crop["crop_path"] if n039_crop else "",
        document_id="TAV-05S",
        page_number=1,
        status="RESOLVED",
    ))

    # --- N041: DocumentEntityCandidate (NOT StructuralEntity) ---
    n041_crop = find_crop("EV-PILLAR-N041")
    n041_candidate = DocumentEntityCandidate(
        candidate_id="N041_CANDIDATE",
        entity_type="Column",
        identity_status=EntityIdentityStatus.CANDIDATE,
        possible_ids=["N041"],
        evidence_ids=["EV-PILLAR-N041"],
        resolution_notes=(
            "Identity gap R-R1-01: DXF marks TERM but no pillar type assigned. "
            "N041 exists in DXF S-TOPO-TEXT-INF as TERM, verify=B. "
            "Not present in S-PIL-A-TEXT (pillar type annotation absent). "
            "Cannot confirm identity as structural entity until type is resolved."
        ),
        blocking_residual="R-R1-01",
    )

    n041_claim = Claim(
        claim_id="CLM-N041-TERM",
        entity_id="N041_CANDIDATE",
        property_name="verticalTermination",
        property_value="TERM",
        evidence_refs=["EV-PILLAR-N041"],
        source_document_id="TAV-05S",
        confidence=0.7,
        notes="DXF marks TERM, but identity not confirmed — candidate only",
    )
    claims.append(n041_claim)

    resolutions.append(PropertyResolution(
        resolution_id="RES-N041-TERM",
        entity_id="N041_CANDIDATE",
        property_name="verticalTermination",
        claim_id="CLM-N041-TERM",
        evidence_id="EV-PILLAR-N041",
        crop_path=n041_crop["crop_path"] if n041_crop else "",
        document_id="TAV-05S",
        page_number=1,
        status="CANDIDATES",
    ))

    return {
        "entities": {k: v.to_dict() for k, v in entities.items()},
        "candidates": {n041_candidate.candidate_id: n041_candidate.to_dict()},
        "claims": [c.to_dict() for c in claims],
        "resolutions": [r.to_dict() for r in resolutions],
    }


def main():
    print("=" * 60)
    print("TASK 6: eTwin ENTITY/CANDIDATE BINDING")
    print("=" * 60)

    bindings = build_terrace_entities()

    # Print entity chains
    print("\n--- Structural Entities (CONFIRMED) ---")
    for eid, entity in bindings["entities"].items():
        print(f"\n  Entity: {entity['entity_id']} ({entity['identity_status']})")
        print(f"    Type: {entity['entity_type']}")
        print(f"    Position: x={entity['position_x_mm']}, y={entity['position_y_mm']}mm")
        print(f"    Vertical: {entity['vertical_start']} -> {entity['vertical_end']}")
        print(f"    Termination: {entity['termination_reason']}")

        # Find claim
        for claim in bindings["claims"]:
            if claim["entity_id"] == eid:
                print(f"    Claim: {claim['claim_id']}")
                print(f"      Property: {claim['property_name']} = {claim['property_value']}")
                print(f"      Evidence: {claim['evidence_refs']}")
                print(f"      Confidence: {claim['confidence']}")
                break

        # Find resolution
        for res in bindings["resolutions"]:
            if res["entity_id"] == eid:
                print(f"    Resolution: {res['resolution_id']} -> {res['crop_path']}")
                print(f"      -> Document: {res['document_id']}, page {res['page_number']}")
                break

    print("\n--- Document Entity Candidates ---")
    for cid, candidate in bindings["candidates"].items():
        print(f"\n  Candidate: {candidate['candidate_id']} ({candidate['identity_status']})")
        print(f"    Type: {candidate['entity_type']}")
        print(f"    Possible IDs: {candidate['possible_ids']}")
        print(f"    Blocking residual: {candidate['blocking_residual']}")
        print(f"    Notes: {candidate['resolution_notes'][:100]}...")

        for claim in bindings["claims"]:
            if claim["entity_id"] == cid:
                print(f"    Claim: {claim['claim_id']}")
                print(f"      Property: {claim['property_name']} = {claim['property_value']}")
                print(f"      Confidence: {claim['confidence']}")
                break

        for res in bindings["resolutions"]:
            if res["entity_id"] == cid:
                print(f"    Resolution: {res['resolution_id']} -> {res['crop_path']}")
                break

    # Save bindings
    output_path = Path(r"docs\FOGLIO_LAVORO\etwin_crops\terrace_evidence\entity_bindings.json")
    save_json(bindings, output_path)
    print(f"\nBindings saved: {output_path}")

    # Verify chain completeness
    print("\n--- Chain Verification ---")
    for res in bindings["resolutions"]:
        crop_path = Path(res["crop_path"])
        exists = crop_path.exists()
        status = "OK" if exists else "MISSING"
        print(f"  {res['resolution_id']}: crop {'exists' if exists else 'MISSING'} -> {status}")

    print(f"\nDONE: {len(bindings['entities'])} entities, {len(bindings['candidates'])} candidates")
    return bindings


if __name__ == "__main__":
    bindings = main()
