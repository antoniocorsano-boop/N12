#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "automation/CEW_DOCUMENT_MAP_MODEL_v1.json"
MAPS = ROOT / "data/canonical/CEW_DOCUMENT_MAP_REGISTRY_v1.json"
CANDIDATES = ROOT / "automation/CEW_DOCUMENT_FEATURE_CANDIDATES_v1.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def model() -> dict:
    return load_json(MODEL)


def maps() -> dict[str, dict]:
    payload = load_json(MAPS)
    return {row["source_id"]: row for row in payload.get("maps", [])}


def candidates() -> dict[str, dict]:
    payload = load_json(CANDIDATES)
    return {row["candidate_id"]: row for row in payload.get("candidates", [])}


def document_map(source_id: str) -> dict | None:
    row = maps().get(source_id)
    if not row:
        return None
    cand = candidates()
    return {
        **row,
        "validated_features": [cand[cid] for cid in row.get("validated_feature_ids", []) if cid in cand],
        "candidate_features": [cand[cid] for cid in row.get("candidate_feature_ids", []) if cid in cand],
    }


def validate_candidate(candidate: dict) -> list[str]:
    m = model()
    errors: list[str] = []
    for field in m["candidate_required_fields"]:
        if candidate.get(field) in (None, ""):
            errors.append(f"MISSING_{field.upper()}")
    if candidate.get("feature_type") not in set(m["feature_types"]):
        errors.append("UNKNOWN_FEATURE_TYPE")
    if candidate.get("state") not in set(m["feature_states"]):
        errors.append("UNKNOWN_FEATURE_STATE")
    if candidate.get("state") == "VALIDATED" and not candidate.get("reviewer"):
        errors.append("VALIDATED_REQUIRES_HUMAN_REVIEWER")
    confidence = candidate.get("confidence")
    if confidence is not None:
        try:
            value = float(confidence)
        except (TypeError, ValueError):
            errors.append("CONFIDENCE_NOT_NUMERIC")
        else:
            if value < 0 or value > 1:
                errors.append("CONFIDENCE_OUT_OF_RANGE")
    bbox = candidate.get("bbox_normalized_0_1")
    if bbox is not None:
        if not isinstance(bbox, list) or len(bbox) != 4:
            errors.append("BBOX_REQUIRES_X_Y_WIDTH_HEIGHT")
        else:
            try:
                x, y, w, h = [float(v) for v in bbox]
            except (TypeError, ValueError):
                errors.append("BBOX_NOT_NUMERIC")
            else:
                if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.000001 or y + h > 1.000001:
                    errors.append("BBOX_OUTSIDE_NORMALIZED_PAGE")
    return errors


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _human_feature(feature_type: str) -> str:
    labels = {
        "DRAWING_TITLE": "Titolo della tavola",
        "DRAWING_NUMBER": "Numero elaborato",
        "DRAWING_SCALE": "Scala",
        "READING_ORIENTATION": "Orientamento di lettura",
        "PROJECT_LEVEL": "Livello / piano",
        "FRAME_OR_GRID_REFERENCE": "Telaio / reticolo",
        "SECTION_OR_ELEVATION_REFERENCE": "Sezioni / elevazioni",
        "DETAIL": "Dettagli",
        "SCHEDULE_OR_TABLE": "Abachi / tabelle",
        "EXPLODED_REINFORCEMENT_VIEW": "Armature esplose",
        "LEGEND": "Legenda",
        "DIMENSION_CHAIN": "Catene di quote",
        "CALLOUT": "Richiami",
        "NOTE": "Note",
        "UNRESOLVED_REGION": "Regioni non comprese",
    }
    return labels.get(feature_type, feature_type.replace("_", " ").title())


def build_document_map_panel(source_id: str) -> str:
    dm = document_map(source_id)
    if not dm:
        return "<section class='docmap-panel'><h2>Document Map</h2><p class='muted'>Nessun DocumentMap governato per questa tavola. Il PDF originale resta disponibile senza inferenze automatiche.</p></section>"

    metadata = dm.get("registered_metadata", {})
    unknown = dm.get("unknown_fields", [])
    validated = dm.get("validated_features", [])
    candidate_rows = dm.get("candidate_features", [])

    metadata_rows = "".join(
        f"<li><b>{_esc(k.replace('_',' ').title())}</b><span>{_esc(v)}</span></li>"
        for k, v in metadata.items()
        if k not in {"metadata_basis", "metadata_is_drawing_internal_reading"}
    )

    validated_rows = "".join(
        f"<li><b>{_esc(_human_feature(row.get('feature_type','')))}</b><span>{_esc(row.get('value_text'))}</span><small>VALIDATED · uso documentale, non promozione ingegneristica</small></li>"
        for row in validated
    ) or "<li><span>Nessuna caratteristica interna della tavola è ancora validata.</span></li>"

    candidate_html = "".join(
        f"<li><b>{_esc(_human_feature(row.get('feature_type','')))}</b><span>{_esc(row.get('value_text') or 'candidato senza valore testuale')}</span><small>{_esc(row.get('state'))} · {_esc(row.get('detector_or_author'))}</small></li>"
        for row in candidate_rows
    ) or "<li><span>Nessun candidato OCR/vector/AI registrato.</span></li>"

    unknown_html = "".join(f"<span class='docmap-chip'>{_esc(_human_feature(x))}</span>" for x in unknown)
    evidence_links = "".join(f"<code>{_esc(x)}</code> " for x in dm.get("evidence_region_ids", [])) or "—"

    return f'''<section class="docmap-panel"><div class="docmap-head"><div><div class="docmap-eyebrow">B1.3 · DOCUMENT UNDERSTANDING</div><h2>Document Map</h2></div><span class="docmap-state">{_esc(dm.get('state'))}</span></div>
<p class="muted">Mappa di comprensione della tavola. Distingue metadata già registrati, contenuti interni validati, candidati macchina e campi ancora sconosciuti.</p>
<details open><summary>Metadata registrati</summary><ul class="docmap-list">{metadata_rows}</ul><p class="docmap-note">Questi metadata provengono dai registri CEW; non vengono presentati come lettura interna della tavola.</p></details>
<details><summary>Caratteristiche validate</summary><ul class="docmap-list">{validated_rows}</ul></details>
<details><summary>Candidati da revisionare</summary><ul class="docmap-list">{candidate_html}</ul><p class="docmap-note">Un candidato non crea EvidenceRegion, binding strutturale o dato canonico.</p></details>
<details open><summary>Da comprendere</summary><div class="docmap-chips">{unknown_html}</div></details>
<details><summary>EvidenceRegion già governate</summary><p>{evidence_links}</p></details>
<div class="docmap-warning"><b>Autorità:</b> `VALIDATED` qui significa validato per la comprensione documentale. Non equivale a DOC, non crea automaticamente un fatto ingegneristico e non autorizza scritture canoniche.</div></section>'''


CSS = """
.docmap-panel{margin-top:14px;border-top:1px solid #edf0f2;padding-top:14px}.docmap-head{display:flex;align-items:center;gap:8px}.docmap-head>div{flex:1}.docmap-eyebrow{font-size:10px;letter-spacing:.08em;font-weight:850;color:#173f5f}.docmap-state{font-size:11px;font-weight:800;background:#eef3f7;border-radius:999px;padding:5px 8px}.docmap-panel details{border-top:1px solid #edf0f2;padding:8px 0}.docmap-panel summary{cursor:pointer;font-weight:750}.docmap-list{list-style:none;padding:0;margin:6px 0}.docmap-list li{display:grid;gap:2px;padding:6px 0}.docmap-list li small{color:#65717e}.docmap-chip{display:inline-block;margin:3px;padding:4px 7px;border-radius:999px;background:#fff5df;border:1px solid #ead6a5;font-size:11px}.docmap-note{font-size:11px;color:#65717e}.docmap-warning{font-size:11px;background:#fff7e8;border-left:4px solid #8a4b08;padding:9px;margin-top:8px}.docmap-panel code{font-size:10px}
"""
