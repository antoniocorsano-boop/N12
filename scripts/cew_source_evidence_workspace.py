#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import io
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INDEX = ROOT / "data/canonical/tavole_originali_remote_index_v1.csv"
PAGES = ROOT / "data/canonical/CEW_PAGE_REGISTRY_v1.csv"
TRANSFORMS = ROOT / "data/canonical/CEW_PAGE_TRANSFORM_REGISTRY_v1.csv"
REGIONS = ROOT / "data/canonical/CEW_EVIDENCE_REGION_REGISTRY_v1.csv"
BINDINGS = ROOT / "data/canonical/CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
DERIVED = ROOT / "data/canonical/CEW_DERIVED_ASSET_REGISTRY_v1.csv"
TASKS = ROOT / "data/canonical/CEW_ERW_RESOLUTION_TASKS_v1.csv"
RECEIPT_SCHEMA = ROOT / "automation/CEW_HUMAN_DECISION_RECEIPT_SCHEMA_v1.json"
TARGETS = ROOT / "data/canonical/CEW_PROMOTION_TARGET_REGISTRY_v1.csv"

ARCHIVE_COMMIT = "78c20a52db4f391ce0d13b9705b9f04737e218c9"
ARCHIVE_RAW_BASE = f"https://raw.githubusercontent.com/antoniocorsano-boop/N12/{ARCHIVE_COMMIT}/"
MAX_SOURCE_BYTES = 8 * 1024 * 1024


def rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def maps() -> dict:
    source_rows = rows(SOURCE_INDEX)
    task_rows = rows(TASKS)
    binding_rows = rows(BINDINGS)
    region_rows = rows(REGIONS)
    page_rows = rows(PAGES)
    transform_rows = rows(TRANSFORMS)
    derived_rows = rows(DERIVED)
    return {
        "sources": {r["id"]: r for r in source_rows},
        "tasks": {r["task_id"]: r for r in task_rows},
        "bindings": {r["task_id"]: r for r in binding_rows},
        "regions": {r["evidence_region_id"]: r for r in region_rows},
        "pages": {r["page_id"]: r for r in page_rows},
        "transforms": {r["transform_id"]: r for r in transform_rows},
        "derived": {r["derived_asset_id"]: r for r in derived_rows},
    }


def source_url(source: dict) -> str:
    path = source["remote_path"]
    return ARCHIVE_RAW_BASE + "/".join(quote(part) for part in path.split("/"))


def verify_source_bytes(source: dict, payload: bytes) -> str:
    if not payload:
        raise ValueError("SOURCE_BYTES_EMPTY")
    if len(payload) > MAX_SOURCE_BYTES:
        raise ValueError("SOURCE_BYTES_LIMIT_EXCEEDED")
    digest = hashlib.sha256(payload).hexdigest()
    if digest.lower() != source["sha256"].strip().lower():
        raise ValueError("SOURCE_SHA256_MISMATCH")
    return digest


def fetch_verified_source(source_id: str, timeout: int = 15) -> tuple[bytes, dict]:
    m = maps()
    source = m["sources"].get(source_id)
    if not source:
        raise KeyError("SOURCE_NOT_FOUND")
    if source.get("status") != "DOC_PRIMARY_IMMUTABLE":
        raise ValueError("SOURCE_NOT_IMMUTABLE")
    request = Request(source_url(source), headers={"User-Agent": "CEW/1 source-integrity-reader"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read(MAX_SOURCE_BYTES + 1)
    verify_source_bytes(source, payload)
    return payload, source


def _clip_for_scale(region: dict, page_rect, scale: str):
    import fitz
    scale = scale.upper()
    if scale == "MACRO":
        return page_rect, 42

    x = float(region["x"])
    y = float(region["y"])
    w = float(region["width"])
    h = float(region["height"])
    if region.get("coordinate_space") != "NORMALIZED_0_1":
        raise ValueError("UNSUPPORTED_REGION_COORDINATE_SPACE")

    if scale == "MICRO":
        pad_x = max(0.01, w * 0.03)
        pad_y = max(0.008, h * 0.10)
        dpi = 220
    elif scale == "MESO":
        pad_x = max(0.03, w * 0.10)
        pad_y = max(0.035, h * 0.55)
        dpi = 145
    else:
        raise ValueError("UNKNOWN_SOURCE_SCALE")

    x0 = max(0.0, x - pad_x) * page_rect.width
    y0 = max(0.0, y - pad_y) * page_rect.height
    x1 = min(1.0, x + w + pad_x) * page_rect.width
    y1 = min(1.0, y + h + pad_y) * page_rect.height
    clip = fitz.Rect(x0, y0, x1, y1) & page_rect
    if clip.is_empty or clip.width <= 0 or clip.height <= 0:
        raise ValueError("EMPTY_RENDER_CLIP")
    return clip, dpi


def render_verified_pdf(payload: bytes, region: dict, page_index: int, scale: str) -> bytes:
    import fitz
    with fitz.open(stream=payload, filetype="pdf") as doc:
        if page_index < 0 or page_index >= doc.page_count:
            raise ValueError("PAGE_INDEX_OUT_OF_RANGE")
        page = doc.load_page(page_index)
        clip, dpi = _clip_for_scale(region, page.rect, scale)
        pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False)
        return pix.tobytes("png")


def task_context(task_id: str) -> dict:
    m = maps()
    task = m["tasks"].get(task_id)
    binding = m["bindings"].get(task_id)
    if not task or not binding:
        raise KeyError("TASK_BINDING_NOT_FOUND")
    region = m["regions"].get(binding["evidence_region_id"])
    page = m["pages"].get(binding["page_id"])
    transform = m["transforms"].get(binding["transform_id"])
    if not region or not page or not transform:
        raise KeyError("F2_PROVENANCE_CHAIN_INCOMPLETE")
    if any(x.get("readiness_state") != "READY" for x in (region, page, transform)):
        raise ValueError("F2_PROVENANCE_NOT_READY")
    source = m["sources"].get(task["source_id"])
    if not source:
        raise KeyError("PRIMARY_SOURCE_NOT_REGISTERED")
    derived = m["derived"].get(region.get("derived_asset_id", ""))
    return {"task": task, "binding": binding, "region": region, "page": page, "transform": transform, "source": source, "derived": derived}


def render_task_source(task_id: str, scale: str) -> tuple[bytes, dict]:
    ctx = task_context(task_id)
    payload, source = fetch_verified_source(ctx["task"]["source_id"])
    png = render_verified_pdf(payload, ctx["region"], int(ctx["page"]["page_index"]), scale)
    return png, {**ctx, "verified_sha256": source["sha256"], "scale": scale.upper()}


def _task_title(task: dict) -> str:
    domain = (task.get("domain") or "").strip()
    if domain == "REINFORCEMENT_SOURCE_BINDING":
        return "Verifica il collegamento tra dettaglio e modello strutturale"
    if domain == "REINFORCEMENT":
        if "dimension" in (task.get("unknown_claims") or "").lower():
            return "Completa le quote dell’armatura documentata"
        return "Completa quantità e diametro dell’armatura"
    return "Rivedi una evidenza strutturale"


def _human_unknown(raw: str) -> str:
    return {
        "quantity ND;diameter ND": "quantità e diametro non ancora determinati",
        "missing dimensions ND": "quote mancanti da verificare",
        "member-specific reinforcement ND;direct source binding ND": "armatura specifica e collegamento diretto al membro non ancora determinati",
    }.get((raw or "").strip(), raw or "informazione da verificare")


def build_source_hub() -> str:
    m = maps()
    tasks_by_source: dict[str, list[dict]] = {}
    for task in m["tasks"].values():
        if task.get("status") in {"OPEN", "IN_REVIEW", "WAITING_EVIDENCE"}:
            tasks_by_source.setdefault(task["source_id"], []).append(task)

    cards = []
    for sid, source in m["sources"].items():
        linked = tasks_by_source.get(sid, [])
        evidence_count = sum(1 for t in linked if t["task_id"] in m["bindings"])
        review_text = f"{len(linked)} revisioni aperte" if linked else "Nessuna revisione aperta"
        evidence_action = f"<a class='secondary' href='/sources/{html.escape(sid)}#evidenze'>Vedi evidenze</a>" if evidence_count else ""
        cards.append(f'''<article class="source-card"><div class="eyebrow">Fonte primaria immutabile</div><h2>{html.escape(sid)}</h2><p><b>{html.escape(source['classe'].replace('_',' '))}</b> · {html.escape(source['livello_uso'].replace('_',' '))}</p><p class="muted">{html.escape(review_text)}</p><div class="actions"><a class="button" href="/sources/{html.escape(sid)}">Apri fonte</a>{evidence_action}</div><details><summary>Identità tecnica</summary><dl><dt>File</dt><dd>{html.escape(source['canonical_filename'])}</dd><dt>SHA-256</dt><dd>{html.escape(source['sha256'])}</dd><dt>Archivio</dt><dd>{html.escape(source['remote_path'])}</dd><dt>Stato</dt><dd>{html.escape(source['status'])}</dd></dl></details></article>''')
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Fonti</title><style>{BASE_CSS}</style></head><body><header><div class="top"><a href="/">← Progetto N12</a><div><div class="brand">CEW · SOURCE HUB</div><h1>Fonti del progetto</h1><p class="muted">Documenti originali, identità immutabile e revisioni che dipendono da ciascuna fonte.</p></div></div></header><main><section class="notice"><b>Autorità della fonte:</b> il PDF verificato è la fonte primaria. Le immagini generate da CEW sono solo ausili di lettura riproducibili.</section><div class="source-grid">{''.join(cards)}</div></main></body></html>'''


def build_source_detail(source_id: str) -> str:
    m = maps()
    source = m["sources"].get(source_id)
    if not source:
        return "<!doctype html><html><body><h1>Fonte non trovata</h1><a href='/sources'>Torna alle fonti</a></body></html>"
    tasks = [t for t in m["tasks"].values() if t.get("source_id") == source_id and t.get("status") in {"OPEN", "IN_REVIEW", "WAITING_EVIDENCE"}]
    review_cards = []
    for task in tasks:
        binding = m["bindings"].get(task["task_id"])
        provenance = "Catena F2 pronta" if binding and binding.get("binding_state") == "READY" else "Provenienza da verificare"
        review_cards.append(f'''<article class="review-card"><div class="eyebrow">{html.escape(provenance)}</div><h3>{html.escape(_task_title(task))}</h3><p><b>Da verificare:</b> {html.escape(_human_unknown(task.get('unknown_claims','')))}</p><a class="button" href="/evidence/review?task={quote(task['task_id'])}">Apri Evidence Workspace</a></article>''')
    if not review_cards:
        review_cards.append("<article class='review-card'><h3>Nessuna revisione evidenza aperta</h3></article>")
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — {html.escape(source_id)}</title><style>{BASE_CSS}</style></head><body><header><div class="top"><a href="/sources">← Fonti</a><div><div class="brand">CEW · SOURCE HUB</div><h1>{html.escape(source_id)}</h1><p>{html.escape(source['classe'].replace('_',' '))} · {html.escape(source['ruolo'].replace('_',' '))}</p></div></div></header><main><section class="notice"><b>Fonte primaria immutabile.</b> CEW recupera il PDF dal commit archivio fissato e ne verifica SHA-256 prima della visualizzazione o del rendering.</section><section class="panel"><h2>Documento originale</h2><a class="button" href="/api/source/pdf/{html.escape(source_id)}" target="_blank" rel="noopener">Apri PDF verificato</a><details><summary>Provenienza tecnica</summary><dl><dt>Commit archivio</dt><dd>{ARCHIVE_COMMIT}</dd><dt>Percorso</dt><dd>{html.escape(source['remote_path'])}</dd><dt>SHA-256</dt><dd>{html.escape(source['sha256'])}</dd><dt>Git blob</dt><dd>{html.escape(source['git_blob_sha'])}</dd></dl></details></section><section id="evidenze"><h2>Evidenze e revisioni collegate</h2><div class="source-grid">{''.join(review_cards)}</div></section></main></body></html>'''


def build_evidence_workspace(task_id: str) -> str:
    try:
        ctx = task_context(task_id)
    except Exception as exc:
        return f"<!doctype html><html><body><h1>Evidenza non disponibile</h1><p>{html.escape(str(exc))}</p><a href='/sources'>Torna alle fonti</a></body></html>"
    task, binding, region, page, source = ctx["task"], ctx["binding"], ctx["region"], ctx["page"], ctx["source"]
    schema = load_json(RECEIPT_SCHEMA)
    active_targets = [r for r in rows(TARGETS) if r.get("status") == "ACTIVE"]
    target_options = "".join(f"<option value='{html.escape(t['target_id'])}'>{html.escape(t['target_class'])}</option>" for t in active_targets)
    outcomes = "".join(f"<option value='{html.escape(x)}'>{html.escape(x)}</option>" for x in schema["allowed_outcomes"])
    states = "".join(f"<option value='{html.escape(x)}'>{html.escape(x)}</option>" for x in schema["allowed_requested_states"])
    meta = json.dumps({"task_id": task_id, "residual_id": task["residual_id"], "evidence_regions": [binding["evidence_region_id"]], "source_versions": [binding["source_version_id"]], "ack": schema["authority_acknowledgement_exact"]}, ensure_ascii=False)
    linked_state = "Nessun elemento strutturale collegato" if not task.get("model_entities") else f"Elemento collegato: {html.escape(task['model_entities'])}"
    if task_id == "ERW-N12-004":
        linked_state = "Relazione fonte-modello: UNBOUND. CEW non seleziona automaticamente il membro più vicino."
    ceiling = task.get("epistemic_ceiling", "")
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Evidenza</title><style>{BASE_CSS}.workspace{{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(330px,.65fr);gap:18px}}@media(max-width:900px){{.workspace{{grid-template-columns:1fr}}}}.scale-tabs{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}}.scale-tabs button{{background:#eef2f5;color:#173f5f}}.viewer{{background:#20252b;border-radius:10px;padding:8px;min-height:320px;display:flex;align-items:center;justify-content:center}}.viewer img{{max-width:100%;max-height:72vh;background:white}}textarea{{width:100%;min-height:120px}}input,select,textarea{{box-sizing:border-box;padding:9px;margin-top:4px}}label{{display:block;font-weight:700;margin-top:12px}}.check{{display:flex;gap:8px;align-items:flex-start;font-weight:500}}.check input{{width:auto}}pre{{white-space:pre-wrap;background:#111827;color:#eef2ff;padding:12px;border-radius:8px}}</style></head><body><header><div class="top"><a href="/sources/{html.escape(task['source_id'])}">← {html.escape(task['source_id'])}</a><div><div class="brand">CEW · EVIDENCE WORKSPACE</div><h1>{html.escape(_task_title(task))}</h1><p class="muted">Fonte {html.escape(task['source_id'])} · revisione diretta della documentazione primaria</p></div></div></header><main><section class="notice"><b>Autorità:</b> il PDF verificato è la fonte primaria; MICRO, MESO e MACRO sono ausili di lettura derivati dalla stessa Page/Transform/EvidenceRegion. La revisione non è una scrittura canonica.</section><div class="workspace"><div><section class="panel"><h2>Fonte e contesto</h2><div class="scale-tabs"><button onclick="scale('MICRO')">MICRO · dettaglio</button><button onclick="scale('MESO')">MESO · contesto vicino</button><button onclick="scale('MACRO')">MACRO · tavola</button><a class="secondary" href="/api/source/pdf/{html.escape(task['source_id'])}" target="_blank" rel="noopener">PDF originale</a></div><div class="viewer"><img id="sourceImage" alt="Rendering verificato della fonte" src="/api/source/render?task={quote(task_id)}&scale=MICRO"></div><p id="scaleNote" class="muted">MICRO — regione di evidenza con piccolo margine di lettura.</p></section><section class="panel"><h2>Contesto ingegneristico</h2><p><b>Già documentato:</b> {html.escape(task.get('known_claims',''))}</p><p><b>Da verificare:</b> {html.escape(_human_unknown(task.get('unknown_claims','')))}</p><p><b>Conflitti o limiti:</b> {html.escape(task.get('conflicts','') or 'nessuno stabilito')}</p><p><b>Collegamento al modello:</b> {linked_state}</p><p><b>Stato massimo ammissibile:</b> {html.escape(ceiling)}</p></section></div><div><section class="panel"><h2>Registra la tua osservazione</h2><p class="muted">Scrivi in linguaggio tecnico naturale ciò che osservi. Non è richiesta alcuna sintassi per il parser.</p><label>Revisore<input id="reviewer" autocomplete="name"></label><label>Esito<select id="outcome"><option value="">— scegli —</option>{outcomes}</select></label><label>Osservazione<textarea id="observation" placeholder="Descrivi ciò che leggi direttamente nella fonte."></textarea></label><label class="check"><input type="checkbox" id="direct">Ho verificato direttamente la fonte primaria.</label><label>Stato epistemico richiesto<select id="epistemic"><option value="">— scegli —</option>{states}</select></label><label>Target<select id="target"><option value="">— nessun target —</option>{target_options}</select></label><label>ID approvazione riapertura (solo se richiesto)<input id="reopen"></label><label class="check"><input type="checkbox" id="ack">Confermo la mia revisione e comprendo che non è una scrittura canonica.</label><button id="submit">Invia revisione a CEW</button><pre id="result">Nessuna receipt inviata.</pre></section><details class="panel"><summary>Provenienza tecnica</summary><dl><dt>SourceVersion</dt><dd>{html.escape(binding['source_version_id'])}</dd><dt>Page</dt><dd>{html.escape(page['page_id'])}</dd><dt>Transform</dt><dd>{html.escape(binding['transform_id'])}</dd><dt>EvidenceRegion</dt><dd>{html.escape(region['evidence_region_id'])}</dd><dt>Coordinate</dt><dd>{html.escape(region['coordinate_space'])}: x={html.escape(region['x'])}, y={html.escape(region['y'])}, w={html.escape(region['width'])}, h={html.escape(region['height'])}</dd><dt>SHA-256 PDF</dt><dd>{html.escape(source['sha256'])}</dd></dl></details></div></div></main><script>const META={meta};function val(id){{return document.getElementById(id).value.trim()}}function scale(s){{document.getElementById('sourceImage').src='/api/source/render?task='+encodeURIComponent(META.task_id)+'&scale='+s+'&v='+Date.now();document.getElementById('scaleNote').textContent={{MICRO:'MICRO — regione di evidenza con piccolo margine di lettura.',MESO:'MESO — regione più contesto grafico vicino.',MACRO:'MACRO — pagina completa della fonte.'}}[s]}}document.getElementById('submit').onclick=async()=>{{const outcome=val('outcome'),target=val('target'),state=val('epistemic');const receipt={{schema_version:'1.0',decision_id:`HUMAN-${{META.task_id}}-${{Date.now()}}`,task_id:META.task_id,residual_id:META.residual_id,review_mode:'HUMAN_REVIEW',reviewer:val('reviewer'),timestamp:new Date().toISOString(),outcome,human_observation:val('observation'),evidence_regions:META.evidence_regions,source_versions:META.source_versions,direct_primary_evidence_observed:document.getElementById('direct').checked,requested_epistemic_state:state,target_id:target,reopen_approval_id:val('reopen'),authority_acknowledgement:document.getElementById('ack').checked?META.ack:''}};const box=document.getElementById('result');if(!receipt.reviewer||!outcome||!state||!document.getElementById('ack').checked){{box.textContent='Completa revisore, esito, stato epistemico e attestazione.';return}}if(outcome==='CONFIRMED'&&(!receipt.human_observation||!receipt.direct_primary_evidence_observed||!target)){{box.textContent='Una conferma richiede osservazione, verifica diretta e target.';return}}if(outcome!=='CONFIRMED'&&target){{box.textContent='Un esito non promotivo non può selezionare un target.';return}}box.textContent='Validazione CEW in corso…';try{{const r=await fetch('/api/f7/receipt',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(receipt)}});box.textContent=JSON.stringify(await r.json(),null,2)}}catch(e){{box.textContent='Errore di comunicazione: '+e}}}};</script></body></html>'''


BASE_CSS = """
:root{--ink:#17202a;--muted:#5d6875;--line:#d8dde3;--paper:#fff;--bg:#f4f6f8;--accent:#173f5f}*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}a{color:inherit}header{background:var(--paper);border-bottom:1px solid var(--line)}.top{max-width:1200px;margin:auto;padding:22px 28px;display:flex;gap:22px;align-items:flex-start}.top>a{font-weight:750;color:var(--accent);white-space:nowrap}.brand,.eyebrow{font-size:12px;font-weight:800;letter-spacing:.07em;color:var(--accent);text-transform:uppercase}h1{margin:.25rem 0}main{max-width:1200px;margin:auto;padding:24px 28px 48px}.muted{color:var(--muted)}.notice,.panel,.source-card,.review-card{background:white;border:1px solid var(--line);border-radius:12px;padding:17px;margin-bottom:14px}.notice{border-left:5px solid var(--accent)}.source-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}.source-card h2{margin:.25rem 0}.actions{display:flex;gap:8px;flex-wrap:wrap}.button,.secondary,button{display:inline-block;padding:9px 13px;border-radius:8px;text-decoration:none;font-weight:750;border:0;cursor:pointer}.button,button{background:var(--accent);color:white}.secondary{background:#eef2f5;color:var(--accent)}details{margin-top:12px}summary{cursor:pointer;font-weight:700;color:var(--muted)}dl{display:grid;grid-template-columns:max-content 1fr;gap:5px 12px;font-size:13px}dt{font-weight:750}dd{margin:0;overflow-wrap:anywhere}
"""
