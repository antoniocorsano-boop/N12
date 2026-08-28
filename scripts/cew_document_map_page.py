#!/usr/bin/env python3
from __future__ import annotations

import html

import cew_document_map as document_map
import cew_source_evidence_workspace as source_workspace


def esc(value) -> str:
    return html.escape(str(value or ""))


def build_page(source_id: str) -> str:
    source = source_workspace.maps()["sources"].get(source_id)
    if not source:
        return "<!doctype html><html><body><h1>Tavola non trovata</h1><a href='/drawings'>Torna alle tavole</a></body></html>"

    dm = document_map.document_map(source_id)
    state = dm.get("state") if dm else "UNMAPPED"
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Document Map {esc(source_id)}</title>
<style>
:root{{--ink:#17202a;--muted:#65717e;--line:#d8dde3;--paper:#fff;--bg:#f4f6f8;--accent:#173f5f}}*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}}a{{color:var(--accent)}}header{{background:#fff;border-bottom:1px solid var(--line)}}.top{{max-width:1180px;margin:auto;padding:20px 24px;display:flex;gap:16px;align-items:flex-start}}.back{{font-weight:800;text-decoration:none;padding-top:8px}}.brand{{font-size:11px;font-weight:850;letter-spacing:.08em;color:var(--accent)}}h1{{font-size:30px;margin:4px 0}}.muted{{color:var(--muted)}}main{{max-width:1180px;margin:auto;padding:22px 24px 48px}}.hero{{display:grid;grid-template-columns:minmax(0,1fr) 270px;gap:12px;margin-bottom:14px}}.panel{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px}}.state{{font-weight:850;font-size:13px;background:#eef3f7;border-radius:999px;padding:6px 9px;display:inline-block}}.actions{{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}}.button{{display:inline-block;text-decoration:none;background:var(--accent);color:#fff;padding:8px 11px;border-radius:7px;font-weight:800}}.secondary{{background:#fff;color:var(--accent);box-shadow:inset 0 0 0 1px #b8c5cf}}.rule{{font-size:12px;color:var(--muted);line-height:1.45}}{document_map.CSS}
@media(max-width:800px){{.hero{{grid-template-columns:1fr}}}}
</style></head><body><header><div class="top"><a class="back" href="/drawings/{esc(source_id)}">← Tavola</a><div><div class="brand">CEW · DOCUMENT MAP B1.3 PREPARATION</div><h1>{esc(source_id)}</h1><p class="muted">{esc(source.get('classe','').replace('_',' '))} · {esc(source.get('livello_uso','').replace('_',' '))}</p></div></div></header><main>
<section class="hero"><article class="panel"><h2>Comprensione della tavola</h2><p>CEW separa ciò che è già registrato sul documento da ciò che è stato realmente riconosciuto nel contenuto grafico.</p><div class="actions"><a class="button" href="/drawings/{esc(source_id)}">Apri viewer</a><a class="button secondary" href="/api/source/pdf/{esc(source_id)}" target="_blank" rel="noopener">PDF verificato</a><a class="button secondary" href="/sources/{esc(source_id)}">Provenienza</a></div></article><aside class="panel"><div class="state">DocumentMap {esc(state)}</div><p class="rule">`PARTIAL` non significa tavola incompleta: significa che la comprensione strutturata del contenuto non è ancora stata validata in tutte le sue parti.</p></aside></section>
<section class="panel">{document_map.build_document_map_panel(source_id)}</section>
<section class="panel"><h2>Regola di promozione</h2><p class="rule">OCR, vettori, agenti e convenzioni grafiche possono produrre candidati. Solo una revisione umana esplicita può portarli a `VALIDATED` per uso documentale. Anche allora non diventano automaticamente EvidenceRegion, DOC, binding strutturale o dato canonico.</p></section>
</main></body></html>'''
