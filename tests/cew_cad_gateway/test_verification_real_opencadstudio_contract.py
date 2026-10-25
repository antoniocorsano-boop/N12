from __future__ import annotations

import asyncio
import tempfile
import unittest
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path

from cew_cad_gateway.adapters.opencadstudio import OpenCADStudioAdapter
from cew_cad_gateway.canonical import sha256_file
from cew_cad_gateway.changesets import ChangesetService, ProposalRequest
from cew_cad_gateway.policy import GatewayPolicy
from cew_cad_gateway.receipts import ReceiptStore
from cew_cad_gateway.types import (
    CADStatus,
    ChangeReceipt,
    CreatePolyline,
    EpistemicState,
    InspectionReceipt,
    PathClass,
)
from cew_cad_gateway.verification import VerificationService
from cew_cad_gateway.workspace import Workspace


class VerificationMCPClient:
    """External-boundary fake; OpenCADStudioAdapter itself remains real."""

    def __init__(self, document_path: Path) -> None:
        self.document_path = document_path
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def list_tools(self) -> set[str]:
        return {"ocs_sessions", "ocs_read", "ocs_execute", "ocs_capture"}

    async def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append((name, dict(arguments)))
        session = {
            "ok": True,
            "session_id": "session-lab-005",
            "document_id": 3,
            "revision": 3,
            "bridge": {
                "name": "OpenCADStudio",
                "version": "2026.42",
                "build_rev": "b6fbac39ffc7",
                "tool_schema": "d15005e14fc00154501db5d261cb9febae1bcc61f6d9b850e91b7fd1879c3b8e",
            },
            "documents": [
                {
                    "id": 3,
                    "path": str(self.document_path),
                    "revision": 3,
                    "start": False,
                    "title": "cew-cad-lab.dwg",
                    "dirty": True,
                }
            ],
            "command": {"status": "idle"},
        }
        if name == "ocs_sessions":
            return {"result": [session]}
        if name == "ocs_read" and arguments.get("op") == "capabilities":
            return {
                "ok": True,
                "api": "ocs-cad-automation",
                "version": 1,
                "bridge": session["bridge"],
                "concurrency": {"document_id": True, "request_id": True, "revision": True},
                "editor": {
                    "capture": True,
                    "commands": True,
                    "events": True,
                    "files": True,
                    "properties": True,
                    "selection": True,
                },
                "geometry": {
                    "query": True,
                    "spatial_filters": True,
                    "kernel_measurements": True,
                    "interactive_commands": True,
                },
                "operations": {"audit": True, "capture": True, "verified_save": True, "batch": True},
                "records": {"collections": [], "filters": []},
                "transactions": {"atomic_property_updates": True, "batch": True, "redo": True, "undo": True},
            }
        if name == "ocs_read" and arguments.get("op") == "state":
            return session
        if name == "ocs_read" and arguments.get("op") == "query":
            self.assert_query(arguments)
            return {
                "ok": True,
                "count": 1,
                "entities": [
                    {
                        "handle": "A1",
                        "type": "LwPolyline",
                        "layer": "CEW-LAB",
                        "closed": True,
                    }
                ],
            }
        if name == "ocs_read" and arguments.get("op") == "measure":
            self.assert_measure(arguments)
            return {
                "ok": True,
                "measurements": [
                    {
                        "handle": "A1",
                        "closed": True,
                        "curve": {"length": 14.0, "area": 12.0},
                    }
                ],
            }
        if name == "ocs_read" and arguments.get("op") == "audit":
            if arguments.get("parameters") != {"target_format": "dwg", "target_version": "2018"}:
                raise AssertionError(arguments)
            return {
                "ok": True,
                "target_format": "dwg",
                "target_version": "2018",
                "target_compatible": True,
                "dropped_on_save": [],
            }
        if name == "ocs_capture":
            if arguments != {
                "ocs_session_id": "session-lab-005",
                "scope": "viewport",
                "diff": True,
            }:
                raise AssertionError(arguments)
            return {"resource_uri": "memory://capture/post", "diff": {"changed": True}}
        raise AssertionError((name, arguments))

    @staticmethod
    def assert_query(arguments: dict[str, object]) -> None:
        if arguments != {
            "ocs_session_id": "session-lab-005",
            "op": "query",
            "handle": "A1",
        }:
            raise AssertionError(arguments)

    @staticmethod
    def assert_measure(arguments: dict[str, object]) -> None:
        if arguments != {
            "ocs_session_id": "session-lab-005",
            "op": "measure",
            "parameters": {"handles": ["A1"]},
        }:
            raise AssertionError(arguments)


class VerificationRealOpenCADStudioContractTests(unittest.TestCase):
    def test_verification_uses_real_adapter_query_and_kernel_measure_contract(self) -> None:
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
            executable = root / "OpenCADStudio.exe"
            executable.write_bytes(b"fake-ocs-executable")

            client = VerificationMCPClient(source)

            @asynccontextmanager
            async def factory(_executable: Path):
                yield client

            adapter = OpenCADStudioAdapter(
                executable,
                expected_executable_sha256=sha256_file(executable),
                client_factory=factory,
                required_capabilities=policy.required_capabilities,
            )
            current = asyncio.run(adapter.status())
            base_document = replace(current.document, revision=2)
            inspection = InspectionReceipt(
                schema="cew.cad.inspection.v1",
                status=CADStatus(
                    session_id=current.session_id,
                    document=base_document,
                    capabilities=current.capabilities,
                    path_class=PathClass.WORKING,
                ),
                audit_sha256="2" * 64,
                observed_at="2026-10-25T09:32:31+00:00",
            )
            proposal = ProposalRequest(
                changeset_id="CEW-CAD-LAB-005-REAL-ADAPTER-CONTRACT",
                intent="verify exact LAB polyline through the real OCS adapter",
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
                request_id="cew-cad-lab-005-real-adapter-contract",
                revision_before=2,
                revision_after=3,
                changed_entities=("A1",),
                status="COMPLETED",
            )
            audits = root / "05_audits" / "real-adapter-contract"
            audits.mkdir()
            service = VerificationService(
                adapter=adapter,
                workspace=workspace,
                receipt_store=ReceiptStore(audits),
                target_format="dwg",
                target_version="2018",
            )

            receipt = asyncio.run(service.verify(changeset, change))

            self.assertEqual(receipt.decision, "PASS")
            self.assertIn(
                (
                    "ocs_read",
                    {"ocs_session_id": "session-lab-005", "op": "query", "handle": "A1"},
                ),
                client.calls,
            )
            self.assertIn(
                (
                    "ocs_read",
                    {
                        "ocs_session_id": "session-lab-005",
                        "op": "measure",
                        "parameters": {"handles": ["A1"]},
                    },
                ),
                client.calls,
            )


if __name__ == "__main__":
    unittest.main()
