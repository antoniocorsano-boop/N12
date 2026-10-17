"""
Task 8: Knowledge Persistence Proof
Demonstrate that analysis survives interruptions without data loss.
Two-phase proof: analyze -> save -> interrupt -> resume -> verify.
"""
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

from model.etwin.reading_state import ReadingState

STATE_DIR = Path(r"docs\FOGLIO_LAVORO\etwin_crops\TAV-05S")


def demonstrate_persistence():
    """Two-phase persistence proof."""
    state_path = STATE_DIR / "persistence_proof_state.json"

    print("=" * 60)
    print("TASK 8: KNOWLEDGE PERSISTENCE PROOF")
    print("=" * 60)

    # Phase 1: Fresh analysis
    print("\n--- Phase 1: Initial Analysis (5 tiles) ---")
    state = ReadingState(state_path)
    state.initialize("TAV-05S", "DM-TAV-05S-001")

    phase1_tiles = [
        "T-R-TAV-05S-PLAN-00", "T-R-TAV-05S-PLAN-01", "T-R-TAV-05S-PLAN-02",
        "T-R-TAV-05S-PLAN-03", "T-R-TAV-05S-PLAN-04",
    ]

    for tile_id in phase1_tiles:
        state.mark_tile_read(tile_id, method="visual")
        state.add_observation({
            "tile_id": tile_id,
            "finding": f"Phase 1 observation for {tile_id}",
            "method": "visual",
            "confidence": 0.85,
        })

    state.add_claim({
        "entity_id": "N002",
        "property": "verticalTermination",
        "value": "continues_above",
        "source": "DXF",
        "evidence_status": "DOC",
        "phase": 1,
    })
    state.add_claim({
        "entity_id": "N041",
        "property": "termination",
        "value": "TERM",
        "source": "DXF",
        "evidence_status": "DOC",
        "phase": 1,
    })

    summary1 = state.get_summary()
    print(f"  Tiles: {summary1['tiles_read']}, Observations: {summary1['observations']}, Claims: {summary1['claims']}")

    # Capture Phase 1 state hash
    phase1_json = json.dumps(state.state, sort_keys=True, ensure_ascii=False)

    # Phase 2: "Interrupt" — reload from disk
    print("\n--- Phase 2: Simulate Interruption & Reload ---")
    state2 = ReadingState(state_path)

    # Verify Phase 1 data survived
    assert state2.get_tiles_read() == phase1_tiles, "TILES CHANGED!"
    assert len(state2.get_observations()) == 5, "OBSERVATIONS CHANGED!"
    assert len(state2.get_claims()) == 2, "CLAIMS CHANGED!"

    phase2_json = json.dumps(state2.state, sort_keys=True, ensure_ascii=False)
    assert phase1_json == phase2_json, "STATE MODIFIED DURING RELOAD!"
    print("  Phase 1 data: INTACT (byte-identical)")

    # Phase 3: Continue analysis
    print("\n--- Phase 3: Continue Analysis (3 more tiles) ---")
    phase3_tiles = [
        "T-R-TAV-05S-PLAN-05", "T-R-TAV-05S-PLAN-06", "T-R-TAV-05S-PLAN-07",
    ]

    for tile_id in phase3_tiles:
        state2.mark_tile_read(tile_id, method="visual")
        state2.add_observation({
            "tile_id": tile_id,
            "finding": f"Phase 3 observation for {tile_id}",
            "method": "visual",
            "confidence": 0.80,
        })

    state2.add_claim({
        "entity_id": "N005",
        "property": "termination",
        "value": "LINE",
        "source": "DXF",
        "evidence_status": "DOC",
        "phase": 3,
    })

    summary3 = state2.get_summary()
    print(f"  Tiles: {summary3['tiles_read']}, Observations: {summary3['observations']}, Claims: {summary3['claims']}")

    # Phase 4: Final verification
    print("\n--- Phase 4: Final Verification ---")
    state3 = ReadingState(state_path)
    final_tiles = state3.get_tiles_read()
    final_obs = state3.get_observations()
    final_claims = state3.get_claims()

    # Verify Phase 1 claims still present
    p1_claims = [c for c in final_claims if c.get("phase") == 1]
    p3_claims = [c for c in final_claims if c.get("phase") == 3]

    print(f"  Final tiles: {len(final_tiles)} (8 expected)")
    print(f"  Final observations: {len(final_obs)} (8 expected)")
    print(f"  Final claims: {len(final_claims)} (3 expected)")
    print(f"  Phase 1 claims: {len(p1_claims)} (2 expected)")
    print(f"  Phase 3 claims: {len(p3_claims)} (1 expected)")

    # Verify append-only: Phase 1 observations unchanged
    p1_obs = [o for o in final_obs if o.get("tile_id", "").split("-")[-1].isdigit()
              and int(o["tile_id"].split("-")[-1]) < 5]
    p3_obs = [o for o in final_obs if o.get("tile_id", "").split("-")[-1].isdigit()
              and int(o["tile_id"].split("-")[-1]) >= 5]

    print(f"  Phase 1 observations: {len(p1_obs)} (5 expected)")
    print(f"  Phase 3 observations: {len(p3_obs)} (3 expected)")

    all_ok = (
        len(final_tiles) == 8 and
        len(final_obs) == 8 and
        len(final_claims) == 3 and
        len(p1_claims) == 2 and
        len(p3_claims) == 1 and
        len(p1_obs) == 5 and
        len(p3_obs) == 3
    )

    if all_ok:
        print("\n  PERSISTENCE PROOF: PASS")
        print("  - Phase 1 data survived interruption")
        print("  - Phase 3 data appended correctly")
        print("  - No previous knowledge lost")
    else:
        print("\n  PERSISTENCE PROOF: FAIL")

    return all_ok


if __name__ == "__main__":
    success = demonstrate_persistence()
    sys.exit(0 if success else 1)
