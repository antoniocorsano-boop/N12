#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

VISIBLE_STATES = ("VERIFIED", "PROPOSED", "AMBIGUOUS", "BLOCKING", "NOT_ANALYZED")


@dataclass(frozen=True)
class ObjectView:
    object_id: str
    object_type: str
    family_id: str | None
    state: str
    label: str
    geometry_ref: str
    evidence_ref: str | None

    def validate(self) -> None:
        if self.state not in VISIBLE_STATES:
            raise ValueError(f"unsupported object state: {self.state}")
        if not self.object_id or not self.object_type or not self.geometry_ref:
            raise ValueError("object_id, object_type and geometry_ref are required")


@dataclass(frozen=True)
class BlockerView:
    blocker_id: str
    target_id: str
    reason_code: str
    human_explanation: str
    required_action: str
    gate_effect: str


@dataclass(frozen=True)
class FamilyView:
    family_id: str
    object_type: str
    label: str
    count: int


def build_workbench_state(*, object_type: str, objects: Iterable[ObjectView], blockers: Iterable[BlockerView]) -> dict:
    objects = list(objects)
    blockers = list(blockers)
    for obj in objects:
        obj.validate()
    scoped = [o for o in objects if o.object_type == object_type]
    families: dict[str, FamilyView] = {}
    for obj in scoped:
        key = obj.family_id or "UNCLASSIFIED"
        if key not in families:
            families[key] = FamilyView(key, object_type, key, 0)
        prev = families[key]
        families[key] = FamilyView(prev.family_id, prev.object_type, prev.label, prev.count + 1)
    state_counts = {state: sum(1 for o in scoped if o.state == state) for state in VISIBLE_STATES}
    active_blockers = [b for b in blockers if any(o.object_id == b.target_id for o in scoped)]
    return {
        "contract": "CEW_OA1_HUMAN_OBJECT_WORKBENCH_V1",
        "primary_view": "CAD_FIRST_TECHNICAL_SCENE",
        "source_view": "ON_DEMAND_PROVENANCE",
        "object_type_pass": object_type,
        "objects": [asdict(o) for o in scoped],
        "families": [asdict(f) for f in families.values()],
        "state_counts": state_counts,
        "blockers": [asdict(b) for b in active_blockers],
        "gate": {
            "can_close_type_pass": len(active_blockers) == 0 and state_counts["AMBIGUOUS"] == 0 and state_counts["NOT_ANALYZED"] == 0,
            "blocking_count": len(active_blockers),
        },
        "authority": {
            "canonical_write_authorized": False,
            "structural_identity_created": False,
            "visual_proximity_creates_identity": False,
        },
        "actions": {
            "enabled": ["SELECT_OBJECT", "FILTER_TYPE", "FILTER_FAMILY", "VIEW_BLOCKER", "VIEW_SOURCE"],
            "disabled_until_oa2": ["THIS_IS_A", "CREATE_PROTOTYPE", "ASSIGN_FAMILY"],
            "disabled_until_oa3": ["FIND_SIMILAR"],
        },
    }


def render_panel(state: dict) -> str:
    """Framework-neutral HTML fragment intended for insertion into the existing /workbench shell."""
    counts = state["state_counts"]
    family_rows = "".join(
        f'<li data-family="{f["family_id"]}"><button type="button">{f["label"]} <strong>{f["count"]}</strong></button></li>'
        for f in state["families"]
    ) or '<li>Nessuna famiglia disponibile</li>'
    blocker_rows = "".join(
        f'<li data-blocker="{b["blocker_id"]}"><strong>{b["target_id"]}</strong><span>{b["human_explanation"]}</span><small>{b["required_action"]}</small></li>'
        for b in state["blockers"]
    ) or '<li>Nessun blocco per questa passata</li>'
    return f'''<section id="oa1Workbench" data-oa-contract="CEW_OA1_HUMAN_OBJECT_WORKBENCH_V1" data-canonical-write-authorized="false">
  <header class="oa-type-pass">
    <div><small>Passata per tipologia</small><h2>{state["object_type_pass"]}</h2></div>
    <div class="oa-state-summary" aria-label="Stati oggetti">
      <span data-state="VERIFIED">Verificati <strong>{counts["VERIFIED"]}</strong></span>
      <span data-state="PROPOSED">Proposti <strong>{counts["PROPOSED"]}</strong></span>
      <span data-state="AMBIGUOUS">Ambigui <strong>{counts["AMBIGUOUS"]}</strong></span>
      <span data-state="BLOCKING">Bloccanti <strong>{counts["BLOCKING"]}</strong></span>
      <span data-state="NOT_ANALYZED">Non analizzati <strong>{counts["NOT_ANALYZED"]}</strong></span>
    </div>
  </header>
  <div class="oa-layout">
    <aside class="oa-families" aria-label="Famiglie"><h3>Famiglie</h3><ul>{family_rows}</ul></aside>
    <div class="oa-cad-host" data-primary-view="CAD_FIRST_TECHNICAL_SCENE" aria-label="Vista CAD degli oggetti"></div>
    <aside class="oa-blockers" aria-label="Cosa blocca"><h3>Cosa blocca</h3><ul>{blocker_rows}</ul></aside>
  </div>
  <footer><button type="button" data-action="VIEW_SOURCE">Vedi fonte</button><span>Fonte disponibile su richiesta; il CAD resta la vista operativa primaria.</span></footer>
</section>'''


def pilot_fixture() -> dict:
    return build_workbench_state(
        object_type="COLUMN",
        objects=[
            ObjectView("P01", "COLUMN", "COLUMN_40x40", "VERIFIED", "Pilastro P01", "cad:P01", "ER:P01"),
            ObjectView("P02", "COLUMN", "COLUMN_40x40", "PROPOSED", "Pilastro P02", "cad:P02", "ER:P02"),
            ObjectView("P03", "COLUMN", None, "AMBIGUOUS", "Pilastro P03", "cad:P03", "ER:P03"),
            ObjectView("P04", "COLUMN", None, "BLOCKING", "Pilastro P04", "cad:P04", "ER:P04"),
            ObjectView("P05", "COLUMN", None, "NOT_ANALYZED", "Pilastro P05", "cad:P05", None),
            ObjectView("B01", "BEAM", "BEAM_25x70", "VERIFIED", "Trave B01", "cad:B01", "ER:B01"),
        ],
        blockers=[
            BlockerView(
                "BLK-P04",
                "P04",
                "SOURCE_EVIDENCE_REQUIRED",
                "P04 non può essere classificato con l'evidenza attualmente collegata.",
                "Apri la fonte e verifica la rappresentazione documentale.",
                "OA-G3_BLOCKED",
            )
        ],
    )


if __name__ == "__main__":
    state = pilot_fixture()
    print(render_panel(state))
