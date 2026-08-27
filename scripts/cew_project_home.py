#!/usr/bin/env python3
from __future__ import annotations

import html
from urllib.parse import quote


def esc(value) -> str:
    return html.escape(str(value or ""))


def _attention_title(task: dict) -> str:
    domain = (task.get("domain") or "").strip()
    if domain == "REINFORCEMENT_SOURCE_BINDING":
        return "Verifica il collegamento tra dettaglio e modello strutturale"
    if domain == "REINFORCEMENT":
        unknown = (task.get("unknown_claims") or "").lower()
        if "dimension" in unknown:
            return "Completa le quote dell’armatura documentata"
        return "Completa quantità e diametro dell’armatura"
    return "Rivedi una evidenza strutturale"


def _attention_unknown(task: dict) -> str:
    raw = (task.get("unknown_claims") or "").strip()
    replacements = {
        "quantity ND;diameter ND": "quantità e diametro non ancora determinati",
        "missing dimensions ND": "quote mancanti da verificare",
        "member-specific reinforcement ND;direct source binding ND": "armatura specifica e collegamento diretto al membro non ancora determinati",
    }
    return replacements.get(raw, raw or "informazione da completare")


def _phase_status(raw: str) -> str:
    value = (raw or "").upper()
    if "PROJECT_HOME_V2_IN_PROGRESS" in value or "IN_PROGRESS" in value:
        return "In sviluppo nel prodotto"
    if "ENGINE_AVAILABLE" in value or "ENGINE_FOUNDATION_PRESENT" in value or "CANONICAL_MODEL_ENGINE_AVAILABLE" in value:
        return "Base tecnica disponibile · esperienza integrata da completare"
    if "LEGACY_PROTOTYPE" in value:
        return "Percorso corrente da realizzare"
    if "PLANNED" in value:
        return "Da attivare"
    return "Disponibilità da verificare"


def build_project_home(state: dict, issues: dict, tasks: list[dict], terminology: dict, lifecycle: dict) -> str:
    project = state.get("reference_project", "—")
    engineering = state.get("engineering_state", {})
    calculation_ready = engineering.get("calculation_model_ready") is True
    phase_projection = {p.get("phase_id"): p for p in engineering.get("phase_projection", [])}
    phase_templates = {p.get("phase_id"): p for p in lifecycle.get("phase_templates", [])}
    groups = terminology.get("lifecycle_groups", [])

    issue_rows = issues.get("issues", [])
    open_issues = [i for i in issue_rows if i.get("state") not in {"RESOLVED", "SUPERSEDED"}]
    blocking = [i for i in open_issues if i.get("impact") in {"BLOCKING", "LOCAL_BLOCKING"}]

    attention_cards = []
    for task in tasks:
        if (task.get("status") or "").upper() not in {"OPEN", "IN_REVIEW", "WAITING_EVIDENCE"}:
            continue
        attention_cards.append(f"""
        <article class="attention-card">
          <div class="eyebrow">Revisione evidenza · {esc(task.get('source_id'))}</div>
          <h3>{esc(_attention_title(task))}</h3>
          <p><b>Da completare:</b> {esc(_attention_unknown(task))}</p>
          <a class="button" href="/review/f7?task={quote(task.get('task_id',''))}">Rivedi evidenza</a>
          <details><summary>Dettagli tecnici</summary>
            <dl><dt>Localizzazione fonte</dt><dd>{esc(task.get('source_locator'))}</dd>
            <dt>Dato già noto</dt><dd>{esc(task.get('known_claims'))}</dd>
            <dt>ID attività</dt><dd>{esc(task.get('task_id'))}</dd>
            <dt>ID questione</dt><dd>{esc(task.get('residual_id'))}</dd></dl>
          </details>
        </article>""")
    if not attention_cards:
        attention_cards.append("<article class='attention-card'><h3>Nessuna revisione evidenza aperta</h3><p>Le questioni tecniche restano comunque consultabili nei dettagli e nell’audit.</p></article>")

    lifecycle_groups = []
    for group in groups:
        cards = []
        for pid in group.get("phases", []):
            projection = phase_projection.get(pid, {})
            template = phase_templates.get(pid, {})
            title = projection.get("title") or template.get("name") or pid
            cards.append(f"""
            <div class="phase-card">
              <div class="phase-id">{esc(pid)}</div>
              <b>{esc(title)}</b>
              <span>{esc(_phase_status(projection.get('workspace_status','')))}</span>
            </div>""")
        lifecycle_groups.append(f"<section class='life-group'><h3>{esc(group.get('label'))}</h3><div class='phase-grid'>{''.join(cards)}</div></section>")

    nav = "".join(
        f"<span class='nav-chip'>{esc(item.get('label'))}</span>" for item in terminology.get("navigation", [])
    )
    readiness_class = "ready" if calculation_ready else "warning"
    readiness_text = "Modello di calcolo pronto per autorizzazione" if calculation_ready else "Modello di calcolo non ancora autorizzabile"
    readiness_detail = (
        "I gate ingegneristici risultano pronti per la successiva decisione autorizzativa."
        if calculation_ready
        else "Restano informazioni o decisioni ingegneristiche da completare prima della proiezione nel solver."
    )

    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Progetto {esc(project)}</title>
<style>
:root{{--ink:#17202a;--muted:#5d6875;--line:#d8dde3;--paper:#fff;--bg:#f4f6f8;--accent:#173f5f;--warn:#8a4b08;--warnbg:#fff7e8;--ok:#286044;--okbg:#edf8f1}}
*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}}a{{color:inherit}}header{{background:var(--paper);border-bottom:1px solid var(--line)}}.top{{max-width:1200px;margin:auto;padding:24px 28px;display:flex;justify-content:space-between;gap:20px;align-items:flex-start}}.brand{{font-size:13px;font-weight:800;letter-spacing:.08em;color:var(--accent)}}h1{{margin:.25rem 0 .25rem;font-size:clamp(28px,4vw,42px)}}.subtitle{{color:var(--muted);margin:0}}main{{max-width:1200px;margin:auto;padding:24px 28px 48px}}.toolbar{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}button,.button{{border:0;border-radius:8px;background:var(--accent);color:white;padding:10px 14px;font-weight:750;text-decoration:none;display:inline-block}}.text-link{{padding:9px 0;font-weight:700;color:var(--accent)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}.panel,.attention-card,.life-group{{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:18px}}.readiness{{border-left:5px solid}}.readiness.warning{{border-left-color:var(--warn);background:var(--warnbg)}}.readiness.ready{{border-left-color:var(--ok);background:var(--okbg)}}.metric{{font-size:30px;font-weight:800}}.muted{{color:var(--muted)}}section{{margin:24px 0}}h2{{font-size:22px;margin-bottom:12px}}h3{{margin:.3rem 0 .5rem}}.eyebrow,.phase-id{{font-size:12px;text-transform:uppercase;letter-spacing:.06em;font-weight:800;color:var(--muted)}}.attention-card p{{min-height:48px}}details{{margin-top:12px;border-top:1px solid #edf0f2;padding-top:10px}}summary{{cursor:pointer;font-weight:700;color:var(--muted)}}dl{{display:grid;grid-template-columns:max-content 1fr;gap:5px 12px;font-size:13px}}dt{{font-weight:750}}dd{{margin:0;overflow-wrap:anywhere}}.phase-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}}.phase-card{{border:1px solid #e1e5e9;border-radius:9px;padding:11px;display:flex;flex-direction:column;gap:5px}}.phase-card span{{font-size:12px;color:var(--muted)}}.nav-chips{{display:flex;gap:8px;flex-wrap:wrap}}.nav-chip{{background:#eef2f5;border-radius:999px;padding:7px 10px;font-size:13px;font-weight:650}}.authority{{border-left:5px solid var(--accent)}}
</style></head><body><header><div class="top"><div><div class="brand">CEW · CIVIL EXISTING WORKFLOW</div><h1>Progetto {esc(project)}</h1><p class="subtitle">Valutazione strutturale dell’esistente · ambiente di lavoro dell’ingegnere</p></div><div class="toolbar"><a class="text-link" href="/technical/control-room">Dettagli tecnici e audit</a><form method="post" action="/logout"><button>Esci</button></form></div></div></header><main>
<section><h2>Stato del lavoro</h2><div class="grid"><div class="panel readiness {readiness_class}"><div class="eyebrow">Prontezza per il calcolo</div><h3>{esc(readiness_text)}</h3><p>{esc(readiness_detail)}</p></div><div class="panel"><div class="eyebrow">Questioni aperte</div><div class="metric">{len(open_issues)}</div><p class="muted">di cui {len(blocking)} con impatto bloccante o locale</p></div><div class="panel"><div class="eyebrow">Revisioni evidenza disponibili</div><div class="metric">{len(attention_cards)}</div><p class="muted">azioni umane disponibili senza scrittura canonica automatica</p></div></div></section>
<section><h2>Cosa richiede attenzione</h2><p class="muted">CEW mostra prima le domande ingegneristiche. Gli identificativi interni restano nei dettagli tecnici.</p><div class="grid">{''.join(attention_cards)}</div></section>
<section><h2>Percorso di valutazione</h2><p class="muted">Il percorso P0–P16 organizza il lavoro, ma non sostituisce i gate ingegneristici e non mostra un avanzamento numerico artificiale.</p>{''.join(lifecycle_groups)}</section>
<section><h2>Accessi di lavoro</h2><div class="panel"><div class="nav-chips">{nav}</div><p class="muted">Le aree diventano operative progressivamente nei work package successivi; la disponibilità tecnica non equivale alla validazione professionale del workflow.</p></div></section>
<section><div class="panel authority"><h2>Autorità professionale</h2><p>CEW prepara, collega, controlla e rende tracciabile il lavoro. Le decisioni professionali restano dell’ingegnere responsabile. Una revisione evidenza può produrre una receipt o un candidato governato, ma <b>non modifica automaticamente i dati ingegneristici approvati</b>.</p></div></section>
</main></body></html>'''
