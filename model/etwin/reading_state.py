"""
Task 4: Persistent Reading State Manager
JSON-based state persistence for reading progress.
Append-only: new observations never delete previous ones.
Supports resume from any point.
"""
import json
import sys
import time
from pathlib import Path
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')

from model.etwin.document_engine import (
    EvidenceCrop, Claim, EvidenceStatus, ClaimStatus, GeometricCoords,
    BBoxNative, BBoxNormalized, save_json
)


class ReadingState:
    """Persistent, append-only reading state for a document map."""

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.state = self._load()

    def _default_state(self) -> dict:
        return {
            "version": 1,
            "document_id": "",
            "map_id": "",
            "tiles_read": [],
            "observations": [],
            "claims": [],
            "conflicts": [],
            "decisions": [],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "last_modified": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def _load(self) -> dict:
        if self.state_path.exists():
            with open(self.state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._default_state()

    def save(self):
        """Persist state to disk."""
        self.state["last_modified"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def initialize(self, document_id: str, map_id: str):
        """Initialize state for a new document map."""
        self.state["document_id"] = document_id
        self.state["map_id"] = map_id
        self.save()

    def mark_tile_read(self, tile_id: str, method: str = "manual"):
        """Mark a tile as read (append-only)."""
        entry = {
            "tile_id": tile_id,
            "method": method,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        # Append-only: don't add if already present
        existing_tiles = {t["tile_id"] for t in self.state["tiles_read"]}
        if tile_id not in existing_tiles:
            self.state["tiles_read"].append(entry)
            self.save()

    def add_observation(self, observation: dict):
        """Add an observation (append-only)."""
        observation["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        observation["obs_id"] = f"OBS-{len(self.state['observations']):04d}"
        self.state["observations"].append(observation)
        self.save()

    def add_claim(self, claim: dict):
        """Add a claim (append-only)."""
        claim["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        claim["claim_id"] = f"CLM-{len(self.state['claims']):04d}"
        self.state["claims"].append(claim)
        self.save()

    def add_conflict(self, conflict: dict):
        """Record a conflict between claims (append-only)."""
        conflict["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.state["conflicts"].append(conflict)
        self.save()

    def add_decision(self, decision: dict):
        """Record a decision about a conflict (append-only)."""
        decision["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.state["decisions"].append(decision)
        self.save()

    def get_tiles_read(self) -> list[str]:
        """Return list of tile IDs that have been read."""
        return [t["tile_id"] for t in self.state["tiles_read"]]

    def get_observations(self) -> list[dict]:
        return self.state["observations"]

    def get_claims(self) -> list[dict]:
        return self.state["claims"]

    def get_summary(self) -> dict:
        return {
            "document_id": self.state["document_id"],
            "map_id": self.state["map_id"],
            "tiles_read": len(self.state["tiles_read"]),
            "observations": len(self.state["observations"]),
            "claims": len(self.state["claims"]),
            "conflicts": len(self.state["conflicts"]),
            "decisions": len(self.state["decisions"]),
            "created_at": self.state["created_at"],
            "last_modified": self.state["last_modified"],
        }


def demonstrate_persistence():
    """Demonstrate: analyze tiles -> save -> interrupt -> resume -> verify."""
    state_dir = Path(r"docs\FOGLIO_LAVORO\etwin_crops\TAV-05S")
    state_path = state_dir / "reading_state.json"

    print("=" * 60)
    print("TASK 4: PERSISTENT READING STATE DEMONSTRATION")
    print("=" * 60)

    # Phase 1: Create fresh state
    print("\n--- Phase 1: Initial Analysis ---")
    state = ReadingState(state_path)
    state.initialize("TAV-05S", "DM-TAV-05S-001")

    # Simulate reading 5 tiles
    test_tiles = [
        "T-R-TAV-05S-PLAN-00", "T-R-TAV-05S-PLAN-01", "T-R-TAV-05S-PLAN-02",
        "T-R-TAV-05S-PLAN-03", "T-R-TAV-05S-PLAN-04",
    ]

    for tile_id in test_tiles:
        state.mark_tile_read(tile_id, method="visual_inspection")
        state.add_observation({
            "tile_id": tile_id,
            "finding": f"Structural elements visible in {tile_id}",
            "method": "visual",
            "confidence": 0.8,
        })

    # Add some claims
    state.add_claim({
        "entity_id": "N002",
        "property": "position",
        "value": "x=36481, y=12234",
        "source": "DXF inventory",
        "evidence_status": "DOC",
    })
    state.add_claim({
        "entity_id": "N041",
        "property": "termination",
        "value": "TERM",
        "source": "DXF inventory",
        "evidence_status": "DOC",
    })

    summary1 = state.get_summary()
    print(f"  Tiles read: {summary1['tiles_read']}")
    print(f"  Observations: {summary1['observations']}")
    print(f"  Claims: {summary1['claims']}")
    print(f"  State saved: {state_path}")

    # Phase 2: "Interrupt" — reload from disk (simulates process restart)
    print("\n--- Phase 2: Simulate Interruption & Resume ---")
    state2 = ReadingState(state_path)
    summary2 = state2.get_summary()

    # Verify Phase 1 data survived
    tiles_read = state2.get_tiles_read()
    observations = state2.get_observations()
    claims = state2.get_claims()

    print(f"  Reloaded tiles: {len(tiles_read)}")
    print(f"  Reloaded observations: {len(observations)}")
    print(f"  Reloaded claims: {len(claims)}")

    # Verify data integrity
    assert len(tiles_read) == 5, f"Expected 5 tiles, got {len(tiles_read)}"
    assert len(observations) == 5, f"Expected 5 observations, got {len(observations)}"
    assert len(claims) == 2, f"Expected 2 claims, got {len(claims)}"
    assert tiles_read == test_tiles, "Tile order changed!"
    print("  Phase 1 data: INTACT")

    # Phase 3: Continue analysis
    print("\n--- Phase 3: Continue Analysis ---")
    more_tiles = [
        "T-R-TAV-05S-PLAN-05", "T-R-TAV-05S-PLAN-06", "T-R-TAV-05S-PLAN-07",
    ]
    for tile_id in more_tiles:
        state2.mark_tile_read(tile_id, method="visual_inspection")
        state2.add_observation({
            "tile_id": tile_id,
            "finding": f"Additional elements in {tile_id}",
            "method": "visual",
            "confidence": 0.75,
        })

    state2.add_claim({
        "entity_id": "N005",
        "property": "termination",
        "value": "LINE (continues)",
        "source": "DXF inventory",
        "evidence_status": "DOC",
    })

    summary3 = state2.get_summary()
    print(f"  Total tiles read: {summary3['tiles_read']}")
    print(f"  Total observations: {summary3['observations']}")
    print(f"  Total claims: {summary3['claims']}")

    # Phase 4: Final verification
    print("\n--- Phase 4: Final Verification ---")
    state3 = ReadingState(state_path)
    final_tiles = state3.get_tiles_read()
    final_obs = state3.get_observations()
    final_claims = state3.get_claims()

    # Verify Phase 1 claims are still present
    phase1_claims = [c for c in final_claims if c.get("entity_id") in ("N002", "N041")]
    phase3_claims = [c for c in final_claims if c.get("entity_id") == "N005"]

    print(f"  Final tiles: {len(final_tiles)} (8 expected)")
    print(f"  Final observations: {len(final_obs)} (8 expected)")
    print(f"  Final claims: {len(final_claims)} (3 expected)")
    print(f"  Phase 1 claims present: {len(phase1_claims)} (2 expected)")
    print(f"  Phase 3 claims present: {len(phase3_claims)} (1 expected)")

    # Assertions
    all_ok = (
        len(final_tiles) == 8 and
        len(final_obs) == 8 and
        len(final_claims) == 3 and
        len(phase1_claims) == 2 and
        len(phase3_claims) == 1
    )

    if all_ok:
        print("\n  PERSISTENCE PROOF: PASS")
    else:
        print("\n  PERSISTENCE PROOF: FAIL")

    return all_ok


if __name__ == "__main__":
    success = demonstrate_persistence()
    sys.exit(0 if success else 1)
