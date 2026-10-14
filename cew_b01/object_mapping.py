from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any, Iterable, Mapping

from .evidence_schema import EvidenceRegionCandidate


_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_DECISION_KEYS = {
    "candidate_id",
    "disposition",
    "semantic_label",
    "support_identifier",
    "section_family",
    "note",
}
_COORDINATE_KEYS = {
    "x",
    "y",
    "width",
    "height",
    "geometry",
    "coordinates",
    "coordinate",
    "frame",
    "bbox",
    "bounds",
    "polygon",
    "points",
}


class ReviewValidationError(ValueError):
    """Raised when a B01 review or mapping record violates the human-review boundary."""


class ReviewDisposition(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    AMBIGUOUS = "AMBIGUOUS"


def _optional_text(value: Any, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ReviewValidationError(f"{name} must be a non-empty string when supplied")
    return value.strip()


def _canonical_sha256(mapping: Mapping[str, Any]) -> str:
    payload = json.dumps(
        mapping,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ReviewDecision:
    candidate_id: str
    disposition: ReviewDisposition
    semantic_label: str | None = None
    support_identifier: str | None = None
    section_family: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id.startswith("CEW-B01-EV-"):
            raise ReviewValidationError("review decision must reference a CEW-B01 Evidence candidate")
        if not isinstance(self.disposition, ReviewDisposition):
            raise ReviewValidationError("disposition must be a ReviewDisposition")
        object.__setattr__(self, "semantic_label", _optional_text(self.semantic_label, "semantic_label"))
        object.__setattr__(self, "support_identifier", _optional_text(self.support_identifier, "support_identifier"))
        object.__setattr__(self, "section_family", _optional_text(self.section_family, "section_family"))
        object.__setattr__(self, "note", _optional_text(self.note, "note"))
        if self.disposition is ReviewDisposition.ACCEPT and self.semantic_label is None:
            raise ReviewValidationError("ACCEPT requires an explicit semantic_label")

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "ReviewDecision":
        if not isinstance(mapping, Mapping):
            raise ReviewValidationError("review decision must be a mapping")
        keys = set(mapping)
        forbidden = keys & _COORDINATE_KEYS
        if forbidden:
            raise ReviewValidationError(
                "review decisions cannot supply replacement coordinates: " + ", ".join(sorted(forbidden))
            )
        unknown = keys - _ALLOWED_DECISION_KEYS
        if unknown:
            raise ReviewValidationError("unknown review decision fields: " + ", ".join(sorted(unknown)))
        try:
            disposition = ReviewDisposition(mapping["disposition"])
            candidate_id = mapping["candidate_id"]
        except (KeyError, ValueError) as exc:
            raise ReviewValidationError("candidate_id and valid disposition are required") from exc
        return cls(
            candidate_id=candidate_id,
            disposition=disposition,
            semantic_label=mapping.get("semantic_label"),
            support_identifier=mapping.get("support_identifier"),
            section_family=mapping.get("section_family"),
            note=mapping.get("note"),
        )

    def to_mapping(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "disposition": self.disposition.value,
        }
        for key in ("semantic_label", "support_identifier", "section_family", "note"):
            value = getattr(self, key)
            if value is not None:
                result[key] = value
        return result


@dataclass(frozen=True)
class StructuralObjectCandidate:
    object_candidate_id: str
    evidence_candidate_id: str
    evidence_geometry_digest: str
    source_sha256: str
    semantic_label: str
    support_identifier: str | None
    section_family: str | None
    canonical: bool = False
    structural_identity_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.object_candidate_id, str) or not self.object_candidate_id.startswith("CEW-B01-OBJ-"):
            raise ReviewValidationError("invalid B01 StructuralObject candidate identity")
        if not isinstance(self.evidence_candidate_id, str) or not self.evidence_candidate_id.startswith("CEW-B01-EV-"):
            raise ReviewValidationError("StructuralObject candidate must reference B01 Evidence")
        if not isinstance(self.evidence_geometry_digest, str) or not _HEX64.fullmatch(self.evidence_geometry_digest):
            raise ReviewValidationError("evidence geometry digest must be explicit")
        if not isinstance(self.source_sha256, str) or not _HEX64.fullmatch(self.source_sha256):
            raise ReviewValidationError("source_sha256 must be explicit")
        if not isinstance(self.semantic_label, str) or not self.semantic_label:
            raise ReviewValidationError("semantic_label must be explicit")
        if self.canonical is not False:
            raise ReviewValidationError("B01 StructuralObject candidates cannot be canonical")
        if self.structural_identity_authorized is not False:
            raise ReviewValidationError("B01 cannot authorize structural identity")

    @classmethod
    def from_review(
        cls,
        evidence: EvidenceRegionCandidate,
        decision: ReviewDecision,
    ) -> "StructuralObjectCandidate":
        if decision.disposition is not ReviewDisposition.ACCEPT:
            raise ReviewValidationError("only ACCEPT decisions may map to StructuralObject candidates")
        if decision.candidate_id != evidence.candidate_id:
            raise ReviewValidationError("review decision and Evidence candidate identity mismatch")
        identity = {
            "evidence_candidate_id": evidence.candidate_id,
            "evidence_geometry_digest": evidence.geometry_digest,
            "source_sha256": evidence.source.sha256,
            "semantic_label": decision.semantic_label,
            "support_identifier": decision.support_identifier,
            "section_family": decision.section_family,
        }
        return cls(
            object_candidate_id="CEW-B01-OBJ-" + _canonical_sha256(identity)[:24],
            evidence_candidate_id=evidence.candidate_id,
            evidence_geometry_digest=evidence.geometry_digest,
            source_sha256=evidence.source.sha256,
            semantic_label=decision.semantic_label or "",
            support_identifier=decision.support_identifier,
            section_family=decision.section_family,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "object_candidate_id": self.object_candidate_id,
            "evidence_candidate_id": self.evidence_candidate_id,
            "evidence_geometry_digest": self.evidence_geometry_digest,
            "source_sha256": self.source_sha256,
            "semantic_label": self.semantic_label,
            "support_identifier": self.support_identifier,
            "section_family": self.section_family,
            "canonical": self.canonical,
            "structural_identity_authorized": self.structural_identity_authorized,
        }


def _index_evidence(candidates: Iterable[EvidenceRegionCandidate]) -> dict[str, EvidenceRegionCandidate]:
    indexed: dict[str, EvidenceRegionCandidate] = {}
    source_sha256: str | None = None
    for candidate in candidates:
        if not isinstance(candidate, EvidenceRegionCandidate):
            raise ReviewValidationError("mapping requires EvidenceRegionCandidate records")
        if candidate.candidate_id in indexed:
            raise ReviewValidationError("duplicate Evidence candidate identity")
        if source_sha256 is None:
            source_sha256 = candidate.source.sha256
        elif candidate.source.sha256 != source_sha256:
            raise ReviewValidationError("one B01 review bundle cannot mix source identities")
        indexed[candidate.candidate_id] = candidate
    return indexed


def _index_decisions(decisions: Iterable[ReviewDecision]) -> dict[str, ReviewDecision]:
    indexed: dict[str, ReviewDecision] = {}
    for decision in decisions:
        if not isinstance(decision, ReviewDecision):
            raise ReviewValidationError("mapping requires ReviewDecision records")
        if decision.candidate_id in indexed:
            raise ReviewValidationError("duplicate review decision for candidate")
        indexed[decision.candidate_id] = decision
    return indexed


def map_reviewed_evidence(
    evidence_candidates: Iterable[EvidenceRegionCandidate],
    decisions: Iterable[ReviewDecision],
) -> tuple[StructuralObjectCandidate, ...]:
    evidence_by_id = _index_evidence(evidence_candidates)
    decision_by_id = _index_decisions(decisions)
    unknown = set(decision_by_id) - set(evidence_by_id)
    if unknown:
        raise ReviewValidationError("review decision references unknown Evidence candidate")
    mapped = [
        StructuralObjectCandidate.from_review(evidence_by_id[candidate_id], decision)
        for candidate_id, decision in decision_by_id.items()
        if decision.disposition is ReviewDisposition.ACCEPT
    ]
    return tuple(sorted(mapped, key=lambda item: item.object_candidate_id))


def freeze_pre_comparator_bundle(
    evidence_candidates: Iterable[EvidenceRegionCandidate],
    decisions: Iterable[ReviewDecision],
) -> dict[str, Any]:
    evidence_tuple = tuple(evidence_candidates)
    decision_tuple = tuple(decisions)
    evidence_by_id = _index_evidence(evidence_tuple)
    decision_by_id = _index_decisions(decision_tuple)
    unknown = set(decision_by_id) - set(evidence_by_id)
    if unknown:
        raise ReviewValidationError("cannot freeze review decisions for unknown Evidence candidates")
    structural_candidates = map_reviewed_evidence(evidence_tuple, decision_tuple)
    counts = {item.value: 0 for item in ReviewDisposition}
    for decision in decision_tuple:
        counts[decision.disposition.value] += 1
    body = {
        "schema_id": "CEW_B01_G4_PRE_COMPARATOR",
        "schema_version": 1,
        "source_sha256": next(iter(evidence_by_id.values())).source.sha256 if evidence_by_id else None,
        "evidence_candidate_count": len(evidence_by_id),
        "evidence_index": [
            {
                "candidate_id": item.candidate_id,
                "geometry_digest": item.geometry_digest,
            }
            for item in sorted(evidence_by_id.values(), key=lambda item: item.candidate_id)
        ],
        "review_decisions": [
            decision.to_mapping()
            for decision in sorted(decision_tuple, key=lambda item: item.candidate_id)
        ],
        "review_summary": {
            "accepted": counts[ReviewDisposition.ACCEPT.value],
            "rejected": counts[ReviewDisposition.REJECT.value],
            "ambiguous": counts[ReviewDisposition.AMBIGUOUS.value],
            "unreviewed": len(evidence_by_id) - len(decision_by_id),
        },
        "structural_candidate_count": len(structural_candidates),
        "structural_candidates": [item.to_mapping() for item in structural_candidates],
        "canonical": False,
        "structural_identity_authorized": False,
        "historical_comparator_loaded": False,
    }
    body["bundle_sha256"] = _canonical_sha256(body)
    return body


def compare_historical_summary(
    pre_comparator_bundle: Mapping[str, Any],
    historical_summary: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(pre_comparator_bundle, Mapping):
        raise ReviewValidationError("pre-comparator bundle must be a mapping")
    digest = pre_comparator_bundle.get("bundle_sha256")
    if not isinstance(digest, str) or not _HEX64.fullmatch(digest):
        raise ReviewValidationError("historical comparison requires a frozen pre-comparator digest")
    digest_body = dict(pre_comparator_bundle)
    digest_body.pop("bundle_sha256", None)
    if _canonical_sha256(digest_body) != digest:
        raise ReviewValidationError("pre-comparator bundle digest mismatch")
    if not isinstance(historical_summary, Mapping):
        raise ReviewValidationError("historical summary must be a mapping")
    support_count = historical_summary.get("support_count")
    family_count = historical_summary.get("family_count")
    for name, value in (("support_count", support_count), ("family_count", family_count)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ReviewValidationError(f"historical {name} must be a non-negative integer")
    structural_candidates = pre_comparator_bundle.get("structural_candidates")
    if not isinstance(structural_candidates, list):
        raise ReviewValidationError("frozen bundle structural_candidates must be a list")
    families = {
        item.get("section_family")
        for item in structural_candidates
        if isinstance(item, Mapping) and isinstance(item.get("section_family"), str) and item.get("section_family")
    }
    observed_support_count = len(structural_candidates)
    observed_family_count = len(families)
    return {
        "pre_comparator_bundle_sha256": digest,
        "historical_reference": {
            "support_count": support_count,
            "family_count": family_count,
        },
        "observed_source_derived": {
            "support_count": observed_support_count,
            "family_count": observed_family_count,
        },
        "agreement": {
            "support_count": observed_support_count == support_count,
            "family_count": observed_family_count == family_count,
        },
        "mutation_authorized": False,
    }
