from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_REPOSITORY = "antoniocorsano-boop/N12"
_MAIN_REF = "refs/heads/main"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class ControlPlaneError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class DispatchRequest:
    pr_number: int
    candidate_sha: str


@dataclass(frozen=True)
class PrBinding:
    pr_number: int
    head_repository: str
    head_sha: str


def validate_dispatch_context(
    repository: str,
    ref: str,
    ref_type: str,
    pr_number: object,
    candidate_sha: object,
) -> DispatchRequest:
    if repository != _REPOSITORY or ref != _MAIN_REF or ref_type != "branch":
        raise ControlPlaneError("NON_CANONICAL_CONTROL_PLANE_REF")
    if not isinstance(pr_number, int) or isinstance(pr_number, bool) or pr_number < 1:
        raise ControlPlaneError("INVALID_DISPATCH_INPUT")
    if not isinstance(candidate_sha, str) or _SHA40.fullmatch(candidate_sha) is None:
        raise ControlPlaneError("INVALID_DISPATCH_INPUT")
    return DispatchRequest(pr_number=pr_number, candidate_sha=candidate_sha)


def load_strict_json_bytes(data: bytes, *, label: str) -> dict[str, object]:
    def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ControlPlaneError(label)
            out[key] = value
        return out

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=strict_object)
    except ControlPlaneError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControlPlaneError(label) from exc
    if not isinstance(value, dict):
        raise ControlPlaneError(label)
    return value


def _dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ControlPlaneError("PR_METADATA_UNAVAILABLE")
    return value


def _text(mapping: dict[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ControlPlaneError("PR_METADATA_UNAVAILABLE")
    return value


def validate_pr_metadata(metadata: object, request: DispatchRequest) -> PrBinding:
    pr = _dict(metadata)
    if pr.get("state") != "open":
        raise ControlPlaneError("PR_NOT_OPEN")
    number = pr.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number != request.pr_number:
        raise ControlPlaneError("PR_HEAD_MISMATCH")

    base = _dict(pr.get("base"))
    base_repo = _dict(base.get("repo"))
    if _text(base_repo, "full_name") != _REPOSITORY or _text(base, "ref") != "main":
        raise ControlPlaneError("PR_BASE_MISMATCH")

    head = _dict(pr.get("head"))
    head_sha = _text(head, "sha")
    if head_sha != request.candidate_sha:
        raise ControlPlaneError("PR_HEAD_MISMATCH")
    head_repo = _dict(head.get("repo"))
    head_repository = _text(head_repo, "full_name")
    return PrBinding(pr_number=number, head_repository=head_repository, head_sha=head_sha)
