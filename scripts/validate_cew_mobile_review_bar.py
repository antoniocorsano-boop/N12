#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from cew_mobile_review import (  # noqa: E402
    AUTHORITY_CLOSED,
    PRIMARY_ACTIONS,
    append_action,
    append_undo,
    export_review_bundle,
    normalize_point,
    replay_effective_state,
    validate_manifest,
)
from build_cew_mobile_review_pack import build_html  # noqa: E402


def fixture_manifest() -> dict:
    return {
        "schema_version": "cew-mobile-candidate-review-v1",
        "review_id": "MOBILE-REVIEW-FIXTURE",
        "source": {
            "source_id": "SOURCE-FIXTURE",
            "authority": "TEST_FIXTURE_ONLY",
        },
        "candidates": [
            {
                "candidate_id": "CAND-001",
                "image_uri": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='640' height='480'%3E%3Crect width='640' height='480' fill='white'/%3E%3C/svg%3E",
                "prompt": "Valuta solo l'impronta grafica evidenziata.",
            },
            {
                "candidate_id": "CAND-002",
                "image_uri": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='640' height='480'%3E%3Crect width='640' height='480' fill='white'/%3E%3C/svg%3E",
            },
        ],
    }


def assert_contract() -> None:
    assert PRIMARY_ACTIONS == (
        "PILASTRO",
        "NON_PILASTRO",
        "INQUADRATO_MALE",
        "ALTRO_PILASTRO",
    )
    assert all(value is False for value in AUTHORITY_CLOSED.values())

    manifest = fixture_manifest()
    validate_manifest(manifest)

    assert normalize_point(50, 25, 100, 50) == {"x": 0.5, "y": 0.5}
    assert normalize_point(-10, 80, 100, 50) == {"x": 0.0, "y": 1.0}

    events: list[dict] = []
    events = append_action(events, "CAND-001", "PILASTRO", timestamp="2026-10-30T18:00:00Z")
    assert events[-1]["terminal"] is True
    assert replay_effective_state(events)["CAND-001"]["decision"] == "PILASTRO"

    events = append_undo(events, timestamp="2026-10-30T18:00:01Z")
    assert events[-1]["event_type"] == "UNDO_LAST"
    assert "CAND-001" not in replay_effective_state(events)

    events = append_action(
        events,
        "CAND-001",
        "NON_PILASTRO",
        reason="TRAVE",
        timestamp="2026-10-30T18:00:02Z",
    )
    assert events[-1]["reason"] == "TRAVE"

    events = append_action(
        events,
        "CAND-002",
        "ALTRO_PILASTRO",
        point={"x": 0.25, "y": 0.75},
        timestamp="2026-10-30T18:00:03Z",
    )
    assert events[-1]["terminal"] is False
    assert events[-1]["point"] == {"x": 0.25, "y": 0.75}

    bundle = export_review_bundle(manifest, events)
    assert bundle["authority"] == AUTHORITY_CLOSED
    assert bundle["canonical_write_authorized"] is False
    assert bundle["canonical_write_performed"] is False
    assert len(bundle["events"]) == len(events)

    html = build_html(manifest)
    required_fragments = [
        'class="mobile-action-bar"',
        'class="evidence-viewport"',
        'id="progress"',
        'id="undo"',
        'data-action="PILASTRO"',
        'data-action="NON_PILASTRO"',
        'data-action="INQUADRATO_MALE"',
        'data-action="ALTRO_PILASTRO"',
        'env(safe-area-inset-bottom)',
        'min-height:48px',
        'padding-bottom:calc(var(--bar-height)',
        'ADDITIONAL_OCCURRENCE',
        'UNDO_LAST',
        'canonical_write_authorized:false',
        'canonical_write_performed:false',
    ]
    for fragment in required_fragments:
        assert fragment in html, f"missing mobile contract fragment: {fragment}"

    # Four primary decision buttons exactly. CSS selectors may also contain
    # data-action attributes and must not be counted as interactive controls.
    assert html.count('<button class="primary-action" data-action="') == 4

    print("CEW_MOBILE_REVIEW_BAR_CONTRACT=PASS")
    print(json.dumps({"actions": list(PRIMARY_ACTIONS), "authority": AUTHORITY_CLOSED}, sort_keys=True))


def main() -> int:
    assert_contract()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
