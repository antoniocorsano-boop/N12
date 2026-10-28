from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

from .command_plan import BIMCraftCommandPlan, BenchmarkFixture
from .contracts import BIMCraftToolchainContract
from .reconcile import ReconciliationResult


@dataclass(frozen=True)
class BenchmarkReceipt:
    schema_id: str
    schema_version: int
    benchmark_id: str
    candidate_sha: str
    adoption_state: str
    upstream_release: str
    upstream_commit_sha: str
    asset_name: str
    asset_sha256: str
    fixture_project: str
    fixture_source_sha256: str
    command_plan_sha256: str
    observed_capabilities: tuple[str, ...]
    output_digests: Mapping[str, str]
    reconciliation_status: str
    expected_count: int
    observed_count: int
    difference_count: int
    result: str
    canonical_write_authorized: bool
    structural_identity_authorized: bool
    fem_authorized: bool
    master_change_authorized: bool
    n12_stage_b_authorized: bool

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["observed_capabilities"] = list(self.observed_capabilities)
        payload["output_digests"] = dict(self.output_digests)
        return payload


def _hex(value: str, length: int, name: str) -> str:
    if len(value) != length or any(c not in "0123456789abcdef" for c in value.lower()):
        raise ValueError(f"{name} must be {length}-character hex")
    return value.lower()


def build_benchmark_receipt(
    *,
    contract: BIMCraftToolchainContract,
    fixture: BenchmarkFixture,
    command_plan: BIMCraftCommandPlan,
    reconciliation: ReconciliationResult,
    candidate_sha: str,
    observed_capabilities: Sequence[str],
    output_digests: Mapping[str, str],
) -> BenchmarkReceipt:
    candidate = _hex(candidate_sha, 40, "candidate_sha")
    digests = {str(name): _hex(str(digest), 64, f"output_digests.{name}") for name, digest in output_digests.items()}

    if contract.adoption_state != "BENCHMARK":
        raise ValueError("BIMCRAFT_RECEIPT_AUTHORITY_ESCALATION")
    if any(
        (
            contract.canonical_write_authorized,
            contract.structural_identity_authorized,
            contract.fem_authorized,
            contract.master_change_authorized,
            contract.n12_stage_b_authorized,
        )
    ):
        raise ValueError("BIMCRAFT_RECEIPT_AUTHORITY_ESCALATION")
    if fixture.authority != "BENCHMARK_ONLY" or fixture.canonical or fixture.structural_identity_authorized:
        raise ValueError("BIMCRAFT_RECEIPT_FIXTURE_AUTHORITY_ESCALATION")
    if command_plan.authority != "BENCHMARK_ONLY" or command_plan.project != fixture.project:
        raise ValueError("BIMCRAFT_RECEIPT_PLAN_SCOPE_MISMATCH")

    result = "PASS" if reconciliation.status == "PASS" and not reconciliation.differences else "REWORK"
    return BenchmarkReceipt(
        schema_id="CEW_BIMCRAFT_BENCHMARK_RECEIPT",
        schema_version=1,
        benchmark_id=contract.benchmark_id,
        candidate_sha=candidate,
        adoption_state=contract.adoption_state,
        upstream_release=contract.release,
        upstream_commit_sha=contract.upstream_commit_sha,
        asset_name=contract.asset_name,
        asset_sha256=contract.asset_sha256,
        fixture_project=fixture.project,
        fixture_source_sha256=fixture.source_sha256,
        command_plan_sha256=command_plan.sha256,
        observed_capabilities=tuple(sorted(set(observed_capabilities))),
        output_digests=dict(sorted(digests.items())),
        reconciliation_status=reconciliation.status,
        expected_count=reconciliation.expected_count,
        observed_count=reconciliation.observed_count,
        difference_count=len(reconciliation.differences),
        result=result,
        canonical_write_authorized=False,
        structural_identity_authorized=False,
        fem_authorized=False,
        master_change_authorized=False,
        n12_stage_b_authorized=False,
    )
