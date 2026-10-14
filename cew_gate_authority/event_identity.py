from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .types import CandidateIdentity, ControlPlaneIdentity


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _text(mapping: Mapping[str, Any], key: str, field: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} is required")
    return value


def _positive_int(mapping: Mapping[str, Any], key: str, field: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{field} must be a positive integer")
    return value


def _pull_request(event: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(event.get("pull_request"), "pull_request")


def control_plane_from_pull_request_target_event(event: Mapping[str, Any]) -> ControlPlaneIdentity:
    pr = _pull_request(_mapping(event, "event"))
    base = _mapping(pr.get("base"), "pull_request.base")
    return ControlPlaneIdentity(base_commit_sha=_text(base, "sha", "pull_request.base.sha"))


def candidate_from_pull_request_target_event(event: Mapping[str, Any]) -> CandidateIdentity:
    event = _mapping(event, "event")
    repository = _mapping(event.get("repository"), "repository")
    pr = _pull_request(event)
    head = _mapping(pr.get("head"), "pull_request.head")
    head_repo = _mapping(head.get("repo"), "pull_request.head.repo")
    return CandidateIdentity(
        base_repository=_text(repository, "full_name", "repository.full_name"),
        pr_number=_positive_int(pr, "number", "pull_request.number"),
        head_repository=_text(head_repo, "full_name", "pull_request.head.repo.full_name"),
        head_sha=_text(head, "sha", "pull_request.head.sha"),
    )


def verify_dispatch_candidate(
    pr_metadata: Mapping[str, Any],
    requested_sha: str,
    *,
    base_repository: str,
) -> CandidateIdentity:
    pr = _mapping(pr_metadata, "pull_request")
    head = _mapping(pr.get("head"), "pull_request.head")
    head_repo = _mapping(head.get("repo"), "pull_request.head.repo")
    current_head = _text(head, "sha", "pull_request.head.sha")
    if requested_sha != current_head:
        raise ValueError("requested candidate SHA is not the current PR head")
    return CandidateIdentity(
        base_repository=base_repository,
        pr_number=_positive_int(pr, "number", "pull_request.number"),
        head_repository=_text(head_repo, "full_name", "pull_request.head.repo.full_name"),
        head_sha=current_head,
    )
