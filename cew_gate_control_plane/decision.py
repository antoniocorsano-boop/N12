from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FinalDecision:
    status: str
    success: bool
    failure_code: str | None


def reduce_decision(
    *,
    qualify_job_result: str,
    qualification_exit_code: int | None,
    receipt_emitted: bool,
    handoff_job_result: str,
) -> FinalDecision:
    if qualify_job_result != "success":
        return FinalDecision("CONTROL_PLANE_ERROR", False, "CONTROL_PLANE_OR_INVOCATION_ERROR")
    if type(receipt_emitted) is not bool:
        return FinalDecision("CONTROL_PLANE_ERROR", False, "CONTROL_PLANE_OR_INVOCATION_ERROR")
    if type(qualification_exit_code) is not int:
        return FinalDecision("CONTROL_PLANE_ERROR", False, "CONTROL_PLANE_OR_INVOCATION_ERROR")
    if qualification_exit_code == 2:
        return FinalDecision("CONTROL_PLANE_ERROR", False, "CONTROL_PLANE_OR_INVOCATION_ERROR")
    if qualification_exit_code not in {0, 1}:
        return FinalDecision("CONTROL_PLANE_ERROR", False, "CONTROL_PLANE_OR_INVOCATION_ERROR")
    if not receipt_emitted:
        return FinalDecision("RECEIPT_MISSING", False, "RECEIPT_NOT_EMITTED")
    if handoff_job_result != "success":
        return FinalDecision("HANDOFF_FAILED", False, "ARTIFACT_HANDOFF_FAILED")
    if qualification_exit_code == 1:
        return FinalDecision("NOT_QUALIFIED", False, "NOT_QUALIFIED")
    return FinalDecision("QUALIFIED", True, None)
