#!/usr/bin/env python3
from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path

import cew_source_evidence_workspace as source_workspace

ROOT = Path(__file__).resolve().parents[1]

CSS = """
:root{--ink:#18212b;--muted:#64707d;--line:#d9dfe5;--paper:#fff;--bg:#f4f6f8;--accent:#173f5f;--soft:#eef3f7;--ok:#24613e;--warn:#88500b}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}a{color:inherit}header{background:#fff;border-bottom:1px solid var(--line)}.top{max-width:1240px;margin:auto;padding:22px 28px;display:flex;gap:18px;align-items:flex-start}.back{font-weight:750;color:var(--accent);text-decoration:none;padding-top:7px}.brand{font-size:12px;letter-spacing:.08em;font-weight:850;color:var(--accent)}h1{margin:.25rem 0 .3rem;font-size:clamp(28px,4vw,40px)}h2{margin:0 0 10px}p{line-height:1.45}.muted{color:var(--muted)}main{max-width:1240px;margin:auto;padding:24px 28px 52px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:18px}.stat,.panel,.card{background:#fff;border:1px solid var(--line);border-radius:12px}.stat{padding:14px}.n{font-size:28px;font-weight:850}.panel{padding:17px;margin:16px 0}.notice{border-left:5px solid var(--accent)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}.card{padding:16px;display:flex;flex-direction:column;gap:8px}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.06em;font-weight:800;color:var(--muted)}.title{font-size:20px;font-weight:800}.tags{display:flex;gap:6px;flex-wrap:wrap}.tag{background:var(--soft);border-radius:999px;padding:5px 8px;font-size:12px}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:auto;padding-top:8px}.button{background:var(--accent);color:#fff;text-decoration:none;padding:8px 11px;border-radius:7px;font-weight:750}.secondary{background:#fff;color:var(--accent);box-shadow:inset 0 0 0 1px #b9c7d2}.status{font-weight:750;color:var(--ok)}table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line)}th,td{text-align:left;padding:10px;border-bottom:1px solid #edf0f2;vertical-align:top}th{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}details{margin-top:8px;border-top:1px solid #edf0f2;padding-top:8px}summary{cursor:pointer;font-weight:700;color:var(--muted)}dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 10px;font-size:13px}dt{font-weight:750}dd{margin:0;overflow-wrap:anywhere}.empty{padding:26px;text-align:center;color:var(--muted)}
"""


def esc(value) -> str:
    return html.escape(str(value or ""))


def _human(value: str) -> str:
    return (value or "—").replace("_", " ")


def inventory() -> list[dict]:
    m = source_workspace.maps()
    tasks_by_source: dict[str, list[dict]] = defaultdict(list)
    for task in m["tasks"].values():
        tasks_by_source[task.get("source_id", "")].append(task)

    page_by_source: dict[str, list[dict]] = defaultdict(list)
    for page in m["pages"].values():
        page_by_source[page.get("logical_source_code", "")].append(page)

    regions_by_page: dict[str, list[dict]] = defaultdict(list)
    for region in m["regions"].values():
        regions_by_page[region.get("page_id", "")].append(region)

    derived_by_page: dict[str, list[dict]] = defaultdict(list)
    for asset in m["derived"].values():
        derived_by_page[asset.get("page_id", "")].append(asset)

    result = []
    for source_id, source in sorted(m["sources"].items()):
        pages = page_by_source.get(source_id, [])
        page_ids = {p.get("page_id") for p in pages}
        regions = [r for pid in page_ids for r in regions_by_page.get(pid, [])]
        derived = [a for pid in page_ids for a in derived_by_page.get(pid, [])]
        tasks = tasks_by_source.get(source_id, [])
        open_tasks = [t for t in tasks if (t.get("status") or "").upper() in {"OPEN", "IN_REVIEW", "WAITING_EVIDENCE"}]
        result.append({
            "source_id": source_id,
            "filename": source.get("canonical_filename"),
            "classification": source.get("classe"),
            "level": source.get("livello_uso"),
            "role": source.get("ruolo"),
            "status": source.get("status"),
            "bytes": int(source.get("bytes") or 0),
            "sha256": source.get("sha256"),
            "page_count": len(pages),
            "evidence_count": len(regions),
            "derived_count": len(derived),
            "open_review_count": len(open_tasks),
            "page_registry_ready": bool(pages) and all(p.get("readiness_state") == "READY" for p in pages),
        })
    return result


def _metrics(items: list[dict]) -> dict:
    return {
        "registered": len(items),
        "immutable": sum(1 for x in items if x["status"] == "DOC_PRIMARY_IMMUTABLE"),
        "mapped_pages": sum(x["page_count"] for x in items),
        "evidence": sum(x["evidence_count"] for x in items),
        "reviews": sum(x["open_review_count"] for x in items),
    }


def _header(title: str, subtitle: str, back_href: str = "/", back_label: str = "Progetto N12") -> str:
    return f'''<header><div class="top"><a class="back" href="{esc(back_href)}">← {esc(back_label)}</a><div><div class="brand">CEW · DOCUMENT & DRAWING WORKSPACE</div><h1>{esc(title)}</h1><p class="muted">{esc(subtitle)}</p></div></div></header>'''


def build_document_library() -> str:
    items = inventory()
    metrics = _metrics(items)
    cards = []
    for item in items:
        cards.append(f'''<article class="card"><div class="eyebrow">Documento primario registrato</div><div class="title">{esc(item['source_id'])}</div><p><b>{esc(_human(item['classification']))}</b><br>{esc(_human(item['role']))}</p><div class="tags"><span class="tag">{esc(_human(item['level']))}</span><span class="tag">{item['page_count']} pagine mappate</span><span class="tag">{item['evidence_count']} evidenze</span><span class="tag">{item['open_review_count']} revisioni</span></div><div class="actions"><a class="button" href="/drawings/{esc(item['source_id'])}">Apri scheda tavola</a><a class="button secondary" href="/sources/{esc(item['source_id'])}">Fonte e provenienza</a></div><details><summary>Identità tecnica</summary><dl><dt>File</dt><dd>{esc(item['filename'])}</dd><dt>Stato</dt><dd>{esc(item['status'])}</dd><dt>SHA-256</dt><dd>{esc(item['sha256'])}</dd></dl></details></article>''')
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Documenti</title><style>{CSS}</style></head><body>{_header('Documenti del progetto','Patrimonio documentale attualmente registrato e collegato alla catena CEW.')}
<main><div class="stats"><div class="stat"><div class="n">{metrics['registered']}</div><div>documenti registrati</div></div><div class="stat"><div class="n">{metrics['immutable']}</div><div>fonti primarie immutabili</div></div><div class="stat"><div class="n">{metrics['mapped_pages']}</div><div>pagine già mappate</div></div><div class="stat"><div class="n">{metrics['evidence']}</div><div>regioni di evidenza</div></div></div>
<section class="panel notice"><b>Stato del catalogo.</b> Il registro operativo corrente contiene principalmente tavole originali. Relazioni di calcolo, fotografie, rilievi e prove saranno aggiunti al catalogo generale solo quando esisterà un registro governato: CEW non li inventa dalla struttura del repository.</section>
<section><h2>Patrimonio registrato</h2><div class="grid">{''.join(cards) if cards else '<div class="empty">Nessun documento registrato.</div>'}</div></section></main></body></html>'''


def build_drawing_register() -> str:
    items = inventory()
    metrics = _metrics(items)
    rows_html = []
    for item in items:
        page_state = "READY" if item["page_registry_ready"] else ("NON MAPPATA" if item["page_count"] == 0 else "PARZIALE")
        rows_html.append(f'''<tr><td><b>{esc(item['source_id'])}</b><br><span class="muted">{esc(item['filename'])}</span></td><td>{esc(_human(item['classification']))}</td><td>{esc(_human(item['level']))}</td><td>{esc(_human(item['role']))}</td><td><span class="status">{esc(item['status'])}</span></td><td>{item['page_count']} · {esc(page_state)}</td><td>{item['evidence_count']}</td><td>{item['open_review_count']}</td><td><a class="button" href="/drawings/{esc(item['source_id'])}">Apri</a></td></tr>''')
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Tavole</title><style>{CSS}</style></head><body>{_header('Tavole di progetto','Indice professionale degli elaborati grafici originali e del loro stato di comprensione.')}
<main><div class="stats"><div class="stat"><div class="n">{metrics['registered']}</div><div>tavole registrate</div></div><div class="stat"><div class="n">{metrics['mapped_pages']}</div><div>pagine mappate</div></div><div class="stat"><div class="n">{metrics['evidence']}</div><div>evidenze localizzate</div></div><div class="stat"><div class="n">{metrics['reviews']}</div><div>revisioni aperte</div></div></div>
<section class="panel notice"><b>Regola di lettura.</b> Una tavola può essere fonte primaria anche se la sua Page/DocumentMap non è ancora completa. “Non mappata” significa lavoro documentale da fare, non assenza del documento.</section>
<section><table><thead><tr><th>Tavola</th><th>Classe</th><th>Livello</th><th>Ruolo</th><th>Fonte</th><th>Pagine</th><th>Evidenze</th><th>Revisioni</th><th></th></tr></thead><tbody>{''.join(rows_html)}</tbody></table></section></main></body></html>'''


def build_drawing_card(source_id: str) -> str:
    items = {x["source_id"]: x for x in inventory()}
    item = items.get(source_id)
    if not item:
        return "<!doctype html><html><body><h1>Tavola non trovata</h1><a href='/drawings'>Torna alle tavole</a></body></html>"
    m = source_workspace.maps()
    task_cards = []
    for task in m["tasks"].values():
        if task.get("source_id") != source_id:
            continue
        if (task.get("status") or "").upper() not in {"OPEN", "IN_REVIEW", "WAITING_EVIDENCE"}:
            continue
        task_cards.append(f'''<article class="card"><div class="eyebrow">Evidenza collegata</div><div class="title">{esc(task.get('source_locator'))}</div><p>{esc(task.get('known_claims'))}</p><div class="actions"><a class="button" href="/evidence/review?task={esc(task.get('task_id'))}">Apri evidenza</a></div></article>''')
    page_state = "Page registry READY" if item["page_registry_ready"] else "Page registry da completare"
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — {esc(source_id)}</title><style>{CSS}</style></head><body>{_header(source_id,f"{_human(item['classification'])} · {_human(item['level'])}",'/drawings','Tavole')}
<main><section class="panel notice"><b>Fonte primaria:</b> {esc(item['status'])}. La scheda mostra lo stato documentale corrente; i controlli avanzati di viewer/rotazione/overlay sono la slice B1.2 e non modificano la SourceVersion.</section>
<div class="grid"><article class="card"><div class="eyebrow">Documento</div><div class="title">{esc(item['filename'])}</div><p>{esc(_human(item['role']))}</p><div class="tags"><span class="tag">{esc(page_state)}</span><span class="tag">{item['evidence_count']} evidenze</span><span class="tag">{item['derived_count']} ausili derivati</span></div><div class="actions"><a class="button" href="/api/source/pdf/{esc(source_id)}" target="_blank" rel="noopener">Apri PDF verificato</a><a class="button secondary" href="/sources/{esc(source_id)}">Provenienza</a></div></article><article class="card"><div class="eyebrow">Stato di comprensione</div><div class="title">Document Map</div><p>Non ancora modellata come oggetto governato per questa tavola. B1.3 introdurrà titolo/scala/orientamento/dettagli/abachi/esplosi e regioni non comprese come stati espliciti.</p></article></div>
<section><h2>Evidenze collegate</h2><div class="grid">{''.join(task_cards) if task_cards else '<div class="panel">Nessuna EvidenceRegion/revisione collegata nel registro corrente.</div>'}</div></section></main></body></html>'''
