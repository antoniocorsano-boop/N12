#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = ROOT / "data/canonical/CEW_OBSERVATION_REGISTRY_v1.csv"
DOCUMENT_MAPS = ROOT / "data/canonical/CEW_DOCUMENT_MAP_REGISTRY_v1.json"

UNCERTAINTY_STATES = (
    "OPEN",
    "IN_REVIEW",
    "RESOLVED",
    "NOT_RESOLVABLE_FROM_CURRENT_SOURCES",
)


def _rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _esc(value: object) -> str:
    return html.escape(str(value or ""))


def _observations_for_region(region_id: str) -> list[dict]:
    return [row for row in _rows(OBSERVATIONS) if row.get("evidence_region_id") == region_id]


def _document_map(source_id: str, page_id: str) -> dict | None:
    for row in _json(DOCUMENT_MAPS).get("maps", []):
        if row.get("source_id") == source_id and row.get("page_id") == page_id:
            return row
    return None


def projection(task_id: str, source_workspace) -> dict:
    """Build a read-only projection. It never creates or mutates domain authority."""
    ctx = source_workspace.task_context(task_id)
    task = ctx["task"]
    binding = ctx["binding"]
    region = ctx["region"]
    page = ctx["page"]
    transform = ctx["transform"]
    source = ctx["source"]
    observations = _observations_for_region(region["evidence_region_id"])
    document_map = _document_map(task["source_id"], page["page_id"])

    if not observations:
        observation_state = "OPEN/ND"
    elif any("UNREADABLE" in (row.get("literal_or_value") or "") for row in observations):
        observation_state = "OPEN/ND"
    else:
        observation_state = "DOCUMENTED_PARTIAL_OR_DIRECT"

    return {
        "task": task,
        "binding": binding,
        "region": region,
        "page": page,
        "transform": transform,
        "source": source,
        "observations": observations,
        "document_map": document_map,
        "observation_state": observation_state,
        "structural_geometry_state": "OPEN/ND",
        "structural_geometry_reason": "NO_TRACEABLE_STRUCTURAL_GEOMETRY_BOUND_TO_THIS_EVIDENCE_REGION",
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _observation_cards(rows: list[dict]) -> str:
    if not rows:
        return "<article class='datum open'><h3>OPEN/ND</h3><p>Nessuna Observation registrata per questa EvidenceRegion.</p></article>"
    cards = []
    for row in rows:
        cards.append(
            "<article class='datum' data-observation-id='{oid}'>"
            "<div class='eyebrow'>Observation · {state}</div>"
            "<h3>{otype}</h3>"
            "<p class='literal'>{literal}</p>"
            "<dl><dt>Observation</dt><dd>{oid}</dd>"
            "<dt>EvidenceRegion</dt><dd>{rid}</dd>"
            "<dt>Epistemic ceiling</dt><dd>{ceiling}</dd>"
            "<dt>Binding strutturale</dt><dd>{binding}</dd></dl>"
            "</article>".format(
                oid=_esc(row.get("observation_id")),
                state=_esc(row.get("reading_state")),
                otype=_esc(row.get("observation_type")),
                literal=_esc(row.get("literal_or_value")),
                rid=_esc(row.get("evidence_region_id")),
                ceiling=_esc(row.get("epistemic_ceiling")),
                binding=_esc(row.get("structural_binding") or "NON ASSERTITO"),
            )
        )
    return "".join(cards)


def build_workspace(task_id: str, source_workspace=None) -> str:
    if source_workspace is None:
        import cew_source_evidence_workspace as source_workspace

    try:
        p = projection(task_id, source_workspace)
    except Exception as exc:
        return (
            "<!doctype html><html lang='it'><body><h1>Workspace duale non disponibile</h1>"
            f"<p>{_esc(exc)}</p><p>Fail closed: nessun dato tecnico è stato ricostruito.</p>"
            "<a href='/sources'>Torna alle fonti</a></body></html>"
        )

    task = p["task"]
    binding = p["binding"]
    region = p["region"]
    page = p["page"]
    transform = p["transform"]
    source = p["source"]
    document_map = p["document_map"] or {}
    observations = p["observations"]

    x = max(0.0, min(1.0, float(region["x"]))) * 100
    y = max(0.0, min(1.0, float(region["y"]))) * 100
    width = max(0.0, min(1.0 - x / 100.0, float(region["width"]))) * 100
    height = max(0.0, min(1.0 - y / 100.0, float(region["height"]))) * 100

    unknown_fields = document_map.get("unknown_fields", [])
    unknown_badges = "".join(f"<span class='badge'>{_esc(item)}</span>" for item in unknown_fields[:8])
    if len(unknown_fields) > 8:
        unknown_badges += f"<span class='badge'>+{len(unknown_fields)-8} altri OPEN</span>"

    first_literal = observations[0].get("literal_or_value", "") if observations else ""
    source_id = task["source_id"]
    encoded_task = quote(task_id)
    encoded_source = quote(source_id)

    state_options = "".join(f"<option value='{state}'>{state}</option>" for state in UNCERTAINTY_STATES)

    return f'''<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CEW — Workspace duale { _esc(task_id) }</title>
<style>
:root{{--ink:#17202a;--muted:#5d6875;--line:#d8dde3;--paper:#fff;--bg:#eef2f5;--accent:#173f5f;--warn:#8a4b08;--open:#7a3e00;--ok:#24613e}}
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink)}}a{{color:var(--accent)}}header{{background:#fff;border-bottom:1px solid var(--line)}}.top{{max-width:1700px;margin:auto;padding:12px 18px;display:flex;gap:16px;align-items:center}}.brand{{font-size:12px;font-weight:850;letter-spacing:.05em;color:var(--accent)}}h1{{font-size:22px;margin:2px 0}}h2{{font-size:18px;margin:0}}h3{{font-size:15px;margin:6px 0}}.muted{{color:var(--muted)}}main{{max-width:1700px;margin:auto;padding:14px 18px 28px}}.authority{{background:#fff7e8;border-left:5px solid var(--warn);padding:10px 12px;margin-bottom:12px}}.grid{{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(430px,.85fr);gap:12px;min-height:720px}}.panel{{background:var(--paper);border:1px solid var(--line);border-radius:10px;overflow:hidden;display:flex;flex-direction:column}}.panel-head{{padding:12px 14px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;align-items:center}}.actions{{display:flex;gap:7px;flex-wrap:wrap}}button,.button{{font:inherit;border:1px solid #b8c2ca;border-radius:7px;padding:8px 10px;background:#fff;color:var(--ink);font-weight:700;text-decoration:none;cursor:pointer}}button:focus-visible,a:focus-visible,textarea:focus-visible,select:focus-visible{{outline:3px solid #ffbf47;outline-offset:2px}}iframe{{width:100%;height:100%;min-height:650px;border:0;background:#fff}}.technical{{padding:14px;overflow:auto}}.scope-note{{border:1px solid #efc792;background:#fff8ed;padding:10px;border-radius:8px;margin-bottom:10px}}.region-map{{position:relative;width:170px;aspect-ratio:{float(page['source_width'])}/{float(page['source_height'])};min-height:380px;border:2px solid #697782;background:linear-gradient(#fafafa,#f2f3f4);margin:10px auto 14px}}.region-box{{position:absolute;left:{x:.5f}%;top:{y:.5f}%;width:{width:.5f}%;height:{height:.5f}%;border:3px solid #a12622;background:rgba(161,38,34,.12);min-height:3px}}.caption{{font-size:12px;text-align:center;color:var(--muted)}}.datum{{border:1px solid var(--line);border-radius:8px;padding:10px;margin:9px 0;background:#fff}}.datum.open{{border-left:5px solid var(--warn)}}.eyebrow{{font-size:11px;font-weight:800;letter-spacing:.04em;color:var(--accent)}}.literal{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#f5f7f8;padding:8px;border-radius:6px;overflow-wrap:anywhere}}dl{{display:grid;grid-template-columns:150px 1fr;gap:5px 9px;font-size:12px}}dt{{font-weight:750;color:var(--muted)}}dd{{margin:0;overflow-wrap:anywhere}}.badge{{display:inline-block;font-size:11px;border:1px solid #d6dde2;border-radius:999px;padding:3px 7px;margin:3px 3px 0 0;background:#f7f9fa}}.proposal{{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}}textarea,select{{width:100%;font:inherit;border:1px solid #bcc7cf;border-radius:7px;padding:9px;margin:5px 0 10px}}textarea{{min-height:90px;resize:vertical}}.receipt{{font-size:12px;background:#eef8f1;border-left:4px solid var(--ok);padding:9px;display:none}}.open-state{{font-weight:800;color:var(--open)}}.technical-path{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;overflow-wrap:anywhere;background:#f5f7f8;padding:8px}}@media(max-width:1000px){{.grid{{grid-template-columns:1fr}}iframe{{min-height:560px}}}}
</style></head>
<body data-canonical-write-authorized="false" data-engineering-authority-effect="NONE">
<header><div class="top"><a href="/evidence/review?task={encoded_task}">← Evidence Workspace</a><div><div class="brand">CEW B1.8 · DUAL WORKSPACE · READ ONLY</div><h1>Fonte + rappresentazione tecnica documentale</h1><div class="muted">{_esc(task_id)} · {_esc(source_id)} · {_esc(task.get('source_locator'))}</div></div></div></header>
<main>
<section class="authority"><b>Confine di autorità:</b> il pannello sinistro mostra la fonte verificata o la sua EvidenceRegion; il pannello destro è una proiezione di registri CEW esistenti. <b>Non è una carpenteria ricostruita e non crea identità strutturale.</b> geometry != identity · canonical write = false.</section>
<div class="grid">
<section class="panel" aria-labelledby="source-title"><div class="panel-head"><div><div class="brand">SOURCE PANEL</div><h2 id="source-title">Fonte verificata</h2></div><div class="actions"><button type="button" id="showRegion">Regione verificata</button><button type="button" id="showDrawing">Tavola completa</button><a class="button" href="/api/source/pdf/{encoded_source}" target="_blank" rel="noopener">PDF immutabile</a></div></div><iframe id="sourceFrame" title="Fonte CEW verificata" src="/evidence/review?task={encoded_task}"></iframe></section>
<section class="panel" aria-labelledby="technical-title"><div class="panel-head"><div><div class="brand">TECHNICAL REPRESENTATION PANEL</div><h2 id="technical-title">Proiezione tecnica documentale</h2></div><span class="badge">{_esc(p['observation_state'])}</span></div><div class="technical">
<div class="scope-note" id="structuralGeometryState"><b>Geometria strutturale: <span class="open-state">OPEN/ND</span></b><br>{_esc(p['structural_geometry_reason'])}. Nessuna trave, pilastro, asse o quota geometrica viene dedotta dalla posizione della regione documentale.</div>
<div class="region-map" role="img" aria-label="Posizione normalizzata della EvidenceRegion sulla pagina; non geometria strutturale"><div class="region-box" id="regionBox" title="{_esc(region['evidence_region_id'])}"></div></div><div class="caption">Posizione della EvidenceRegion sulla pagina · NORMALIZED_0_1 · non geometria del modello</div>
{_observation_cards(observations)}
<section><h3>Catena verificabile</h3><div class="technical-path">SourceVersion {_esc(binding['source_version_id'])} → Page {_esc(page['page_id'])} → Transform {_esc(transform['transform_id'])} → EvidenceRegion {_esc(region['evidence_region_id'])} → Observation { _esc(observations[0]['observation_id']) if observations else 'OPEN/ND' }</div><dl><dt>Source</dt><dd>{_esc(source_id)} · {_esc(source.get('status'))}</dd><dt>Page readiness</dt><dd>{_esc(page.get('readiness_state'))}</dd><dt>Region readiness</dt><dd>{_esc(region.get('readiness_state'))}</dd><dt>Binding viewer</dt><dd>{_esc(binding.get('binding_state'))}</dd><dt>DocumentMap</dt><dd>{_esc(document_map.get('document_map_id') or 'OPEN/ND')}</dd><dt>Engineering promotion</dt><dd>false</dd></dl></section>
<section><h3>Campi del documento ancora aperti</h3><div>{unknown_badges or '<span class="badge">OPEN/ND</span>'}</div></section>
<section class="proposal"><h3>Proposta di lettura — sessione locale</h3><p class="muted">Puoi annotare una lettura da sottoporre a verifica. Il testo non modifica Observation, Claim, Entity o altri registri canonici.</p><label for="proposalText"><b>Testo proposto</b></label><textarea id="proposalText">{_esc(first_literal)}</textarea><label for="proposalState"><b>Stato della proposta</b></label><select id="proposalState">{state_options}</select><button type="button" id="saveProposal">Mantieni proposta nella sessione</button><p id="proposalReceipt" class="receipt" role="status"></p></section>
</div></section>
</div></main>
<script>
const TASK_ID={json.dumps(task_id)};const SOURCE_ID={json.dumps(source_id)};const KEY='CEW_B18_DUAL_PROPOSAL:'+TASK_ID;const frame=document.getElementById('sourceFrame');
document.getElementById('showRegion').onclick=()=>{{frame.src='/evidence/review?task='+encodeURIComponent(TASK_ID);}};
document.getElementById('showDrawing').onclick=()=>{{frame.src='/drawings/'+encodeURIComponent(SOURCE_ID);}};
try{{const saved=JSON.parse(sessionStorage.getItem(KEY)||'null');if(saved){{document.getElementById('proposalText').value=saved.text||'';document.getElementById('proposalState').value=saved.state||'OPEN';}}}}catch(_e){{}}
document.getElementById('saveProposal').onclick=()=>{{const payload={{task_id:TASK_ID,text:document.getElementById('proposalText').value,state:document.getElementById('proposalState').value,proposal_only:true,canonical_write:false,engineering_authority_effect:'NONE',saved_at:new Date().toISOString()}};sessionStorage.setItem(KEY,JSON.stringify(payload));const box=document.getElementById('proposalReceipt');box.style.display='block';box.textContent='Proposta mantenuta solo in questa sessione. Nessuna scrittura canonica eseguita.';}};
</script></body></html>'''
