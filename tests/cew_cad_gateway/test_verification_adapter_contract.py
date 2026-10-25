from __future__ import annotations

import asyncio
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from cew_cad_gateway.adapters.opencadstudio import OpenCADStudioError
from cew_cad_gateway.canonical import sha256_file
from cew_cad_gateway.changesets import ChangesetService, ProposalRequest
from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.receipts import ReceiptStore
from cew_cad_gateway.types import (
    CADStatus,
    CapabilityIdentity,
    ChangeReceipt,
    CreatePolyline,
    DocumentIdentity,
    EpistemicState,
    InspectionReceipt,
    PathClass,
)
from cew_cad_gateway.verification import VerificationService
from cew_cad_gateway.workspace import Workspace


class StrictInspectionAdapter:
    """Model the governed query and native kernel measurement contracts."""

    def __init__(self, status: CADStatus) -> None:
        self.current = status
        self.inspect_requests: list[dict[str, object]] = []
        self.measure_requests: list[dict[str, object]] = []

    async def status(self):
        return self.current

    async def inspect(self, request):
        self.inspect_requests.append(dict(request))
        if request != {"op": "query", "handle": "A1"}:
            raise OpenCADStudioError("OCS_INSPECT_FIELD_NOT_AUTHORIZED")
        return {
            "entities": [
                {"handle": "A1", "type": "LwPolyline", "layer": "CEW-LAB", "closed": True}
            ]
        }

    async def measure(self, request):
        self.measure_requests.append(dict(request))
        if request != {"handles": ["A1"]}:
            raise AssertionError(request)
        return {
            "measurements": [
                {"handle": "A1", "curve": {"length": 14.0, "area": 12.0}}
            ]
        }

    async def capture(self, request):
        return {"resource_uri": "memory://capture/post", "diff": {"changed": True}}

    async def audit(self, target):
        return {
            "ok": True,
            "target_format": "dwg",
            "target_version": "2018",
            "target_compatible": True,
            "dropped_on_save": [],
        }

    async def save_verified(self, *args, **kwargs):
        raise AssertionError("not part of this contract test")

    async def apply_operation(self, *args, **kwargs):
        raise AssertionError("verification must not mutate")

    async def operation_status(self, request_id):
        raise AssertionError("verification must not query mutation status")


class VerificationAdapterContractTests(unittest.TestCase):
    def test_single_resolved_handle_uses_governed_exact_handle_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "CivilExisting"
            root.mkdir()
            zones = {
                "SOURCE": "00_sources",
                "BASELINE": "01_baseline",
                "WORKING": "02_working",
                "EVIDENCE": "03_evidence",
                "CHANGESETS": "04_changesets",
                "AUDITS": "05_audits",
                "VERIFIED": "06_verified",
                "ISSUED": "07_issued",
            }
            for zone in zones.values():
                (root / zone).mkdir()

            policy = GatewayPolicy(
                zones=zones,
                mutable_path_classes=("WORKING",),
                max_primary_operations=1,
                allow_overwrite=False,
                allowed_mutating_operations=("create_polyline", "undo_own_change"),
                allowed_property_paths=(),
                required_capabilities=("query", "audit", "capture", "save_verified"),
            )
            workspace = Workspace(root, policy)
            source = root / "02_working" / "lab.dwg"
            source.write_bytes(b"lab")
            document = DocumentIdentity(
                path=str(source),
                sha256=sha256_file(source),
                document_id=3,
                revision=2,
            )
            capabilities = CapabilityIdentity(
                cad_build="2026.42@b6fbac39ffc7",
                capabilities_sha256="1" * 64,
            )
            inspection = InspectionReceipt(
                schema="cew.cad.inspection.v1",
                status=CADStatus(
                    session_id="session-lab-005",
                    document=document,
                    capabilities=capabilities,
                    path_class=PathClass.WORKING,
                ),
                audit_sha256="2" * 64,
                observed_at="2026-10-25T09:32:31+00:00",
            )
            proposal = ProposalRequest(
                changeset_id="CEW-CAD-LAB-005-CONTRACT",
                intent="verify exact LAB polyline",
                operations=(
                    CreatePolyline(
                        layer="CEW-LAB",
                        points=((0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)),
                        closed=True,
                    ),
                ),
                evidence_refs=("E-LAB-005",),
                claim_refs=("C-LAB-005",),
                decision_refs=("D-LAB-005",),
                coordinate_states=(EpistemicState.MIS,) * 4,
                epistemic_states=(EpistemicState.MIS,),
                preconditions=(),
                postconditions=(),
                expected_changed_entities=("NEW:Polyline",),
                forbidden_side_effects=("no unrelated entity changes",),
                unresolved=(),
                influential_unresolved=False,
                target_unique=True,
                output_path=None,
            )
            changeset = ChangesetService(
                policy,
                known_evidence={"E-LAB-005"},
                known_claims={"C-LAB-005"},
                known_decisions={"D-LAB-005"},
            ).propose(proposal, inspection)
            change = ChangeReceipt(
                schema="cew.cad.change.v1",
                changeset_sha256=changeset.changeset_sha256,
                approval_sha256="3" * 64,
                request_id="cew-cad-lab-005-contract",
                revision_before=2,
                revision_after=3,
                changed_entities=("A1",),
                status="COMPLETED",
            )
            adapter = StrictInspectionAdapter(
                CADStatus(
                    session_id="session-lab-005",
                    document=replace(document, revision=3),
                    capabilities=capabilities,
                )
            )
            audits = root / "05_audits" / "contract"
            audits.mkdir()
            service = VerificationService(
                adapter=adapter,
                workspace=workspace,
                receipt_store=ReceiptStore(audits),
                target_format="dwg",
                target_version="2018",
            )

            try:
                receipt = asyncio.run(service.verify(changeset, change))
            except OpenCADStudioError as exc:
                self.fail(f"verification emitted adapter-rejected inspection request: {exc}")

            self.assertEqual(receipt.decision, "PASS")
            self.assertEqual(adapter.inspect_requests, [{"op": "query", "handle": "A1"}])
            self.assertEqual(adapter.measure_requests, [{"handles": ["A1"]}])


if __name__ == "__main__":
    unittest.main()
