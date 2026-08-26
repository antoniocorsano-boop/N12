from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.cew_graphic_review import workspace

BROWSER_SCHEMA = "CEW-GRAPHIC-REVIEW-BROWSER-v1"
DECISION_SCHEMA = "CEW-GRAPHIC-REVIEW-DECISIONS-v1"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _project_locator(package: dict[str, Any]) -> dict[str, Any]:
    for evidence in package["case"].get("evidence", []):
        if evidence.get("label") == "Project source region":
            locator = evidence.get("locator")
            if isinstance(locator, str):
                return json.loads(locator)
            if isinstance(locator, dict):
                return locator
    raise ValueError("review package has no project source-region locator")


def build_browser_manifest(
    *,
    project_db: Path,
    fabric_db: Path,
    review_db: Path,
    project_id: str,
    candidate_package: dict[str, Any],
    context: dict[str, Any],
    image_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    if candidate_package.get("work_item_id") != "DOC-003":
        raise ValueError("candidate package must be a DOC-003 review package")
    image_map = image_map or {}
    cases: list[dict[str, Any]] = []
    for candidate in candidate_package.get("candidates", []):
        observation_id = candidate.get("observation_id")
        if not observation_id:
            raise ValueError("candidate is missing observation_id")
        packaged = workspace.build_case(
            project_db=project_db,
            fabric_db=fabric_db,
            review_db=review_db,
            project_id=project_id,
            observation_id=observation_id,
            context=context,
        )
        locator = _project_locator(packaged)
        source_sha = packaged["graphic"]["source_sha256"]
        cases.append(
            {
                "case_id": packaged["case"]["provenance"]["case_id"],
                "candidate_fingerprint": packaged["graphic"]["candidate_fingerprint"],
                "observation_id": packaged["graphic"]["observation_id"],
                "source_sha256": source_sha,
                "page": locator.get("page"),
                "bbox_native": locator.get("bbox_native"),
                "image_path": image_map.get(source_sha),
                "candidate_summary": packaged["case"]["candidate_summary"],
                "evidence": packaged["case"].get("evidence", []),
                "shared_knowledge": packaged["shared_knowledge"],
                "allowed_label_verdicts": packaged["allowed_label_verdicts"],
                "semantic_authority": packaged["semantic_authority"],
            }
        )
    return {
        "schema_version": BROWSER_SCHEMA,
        "project_id": project_id,
        "candidate_count": len(cases),
        "source_review_package_fingerprint": candidate_package.get("review_package_fingerprint"),
        "context": context,
        "cases": cases,
        "semantic_authority": "PROJECT_HUMAN_REVIEW",
        "decision_export_schema": DECISION_SCHEMA,
        "automatic_semantic_promotion": "DISABLED",
        "automatic_generalization": "DISABLED",
    }


def render_html(manifest: dict[str, Any]) -> str:
    embedded = json.dumps(manifest, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CEW Graphic Review — {manifest['project_id']}</title>
<style>
:root {{ font-family: system-ui, sans-serif; color-scheme: light dark; }}
body {{ margin: 0; background: Canvas; color: CanvasText; }}
header {{ position: sticky; top: 0; z-index: 10; padding: 14px 18px; border-bottom: 1px solid color-mix(in srgb, CanvasText 18%, transparent); background: Canvas; }}
header h1 {{ margin: 0 0 4px; font-size: 20px; }}
header p {{ margin: 0; opacity: .75; font-size: 13px; }}
main {{ max-width: 1180px; margin: 0 auto; padding: 18px; display: grid; gap: 18px; }}
.card {{ border: 1px solid color-mix(in srgb, CanvasText 20%, transparent); border-radius: 12px; overflow: hidden; }}
.card-grid {{ display: grid; grid-template-columns: minmax(320px,1.1fr) minmax(320px,.9fr); }}
.visual {{ padding: 14px; border-right: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }}
.visual canvas {{ width: 100%; height: 360px; border-radius: 8px; background: #f5f5f5; }}
.panel {{ padding: 14px; display: grid; gap: 12px; align-content: start; }}
.meta {{ font-size: 12px; opacity: .72; overflow-wrap: anywhere; }}
.suggestion {{ border-left: 3px solid currentColor; padding: 8px 10px; background: color-mix(in srgb, CanvasText 5%, transparent); margin: 6px 0; }}
.suggestion strong {{ display: block; }}
.layers {{ font-size: 12px; opacity: .75; }}
.conflict {{ font-weight: 700; }}
label {{ display: grid; gap: 5px; font-size: 13px; }}
input, select, textarea {{ font: inherit; padding: 8px; border-radius: 6px; border: 1px solid color-mix(in srgb, CanvasText 25%, transparent); background: Canvas; color: CanvasText; }}
textarea {{ min-height: 72px; resize: vertical; }}
.actions {{ max-width: 1180px; margin: 0 auto; padding: 0 18px 24px; }}
button {{ padding: 10px 16px; font: inherit; font-weight: 650; cursor: pointer; }}
.badge {{ display: inline-block; padding: 2px 7px; border: 1px solid currentColor; border-radius: 999px; font-size: 11px; }}
@media (max-width: 760px) {{ .card-grid {{ grid-template-columns: 1fr; }} .visual {{ border-right: 0; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }} }}
</style>
</head>
<body>
<header>
  <h1>CEW Graphic Review · {manifest['project_id']}</h1>
  <p>Conoscenza condivisa = suggerimento. Autorità semantica = revisione umana del progetto. Nessuna generalizzazione automatica.</p>
</header>
<main id="cases"></main>
<div class="actions"><button id="export">Esporta decisioni JSON</button></div>
<script id="review-data" type="application/json">{embedded}</script>
<script>
const DATA = JSON.parse(document.getElementById('review-data').textContent);
const root = document.getElementById('cases');

function esc(value) {{
  return String(value ?? '').replace(/[&<>\"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[ch]));
}}
function suggestionHtml(item) {{
  const conflict = item.conflict ? '<span class="conflict">CONFLITTO</span>' : '';
  const layers = (item.layers || []).map(esc).join(' · ');
  return `<div class="suggestion"><strong>${{esc(item.meaning)}} · ${{Number(item.calibrated_score).toFixed(3)}}</strong><div class="layers">${{layers}} ${{conflict}}</div><div class="meta">supporto +${{item.positive_weight}} / −${{item.negative_weight}} / ?${{item.uncertain_weight}}</div></div>`;
}}
function drawCrop(canvas, entry) {{
  if (!entry.image_path || !Array.isArray(entry.bbox_native)) {{
    const ctx = canvas.getContext('2d'); ctx.fillStyle='#666'; ctx.font='16px system-ui'; ctx.fillText('Raster non disponibile in questo pacchetto', 20, 40); return;
  }}
  const img = new Image();
  img.onload = () => {{
    const [x0,y0,x1,y1] = entry.bbox_native.map(Number);
    const bw = Math.max(1, Math.abs(x1-x0)), bh = Math.max(1, Math.abs(y1-y0));
    const pad = Math.max(55, Math.min(220, Math.max(bw,bh)*2.2));
    const sx = Math.max(0, Math.min(x0,x1)-pad), sy = Math.max(0, Math.min(y0,y1)-pad);
    const ex = Math.min(img.naturalWidth, Math.max(x0,x1)+pad), ey = Math.min(img.naturalHeight, Math.max(y0,y1)+pad);
    const sw = Math.max(1, ex-sx), sh = Math.max(1, ey-sy);
    canvas.width=900; canvas.height=520;
    const ctx=canvas.getContext('2d'); ctx.fillStyle='#fff'; ctx.fillRect(0,0,canvas.width,canvas.height);
    const scale=Math.min(canvas.width/sw, canvas.height/sh); const dw=sw*scale, dh=sh*scale; const ox=(canvas.width-dw)/2, oy=(canvas.height-dh)/2;
    ctx.drawImage(img,sx,sy,sw,sh,ox,oy,dw,dh);
    ctx.strokeStyle='#d00'; ctx.lineWidth=3;
    ctx.strokeRect(ox+(Math.min(x0,x1)-sx)*scale, oy+(Math.min(y0,y1)-sy)*scale, bw*scale, bh*scale);
  }};
  img.onerror = () => {{ const ctx=canvas.getContext('2d'); ctx.fillStyle='#900'; ctx.font='16px system-ui'; ctx.fillText('Immagine non caricabile: '+entry.image_path,20,40); }};
  img.src = entry.image_path;
}}

DATA.cases.forEach((entry, index) => {{
  const suggestions = entry.shared_knowledge?.candidates || [];
  const options = entry.allowed_label_verdicts.map(v => `<option value="${{esc(v)}}">${{esc(v)}}</option>`).join('');
  const card=document.createElement('section'); card.className='card'; card.dataset.caseId=entry.case_id;
  card.innerHTML=`<div class="card-grid"><div class="visual"><canvas></canvas><div class="meta">Caso ${{index+1}}/${{DATA.candidate_count}} · pagina ${{esc(entry.page)}} · ${{esc(entry.candidate_fingerprint)}}</div></div><div class="panel"><div><span class="badge">${{esc(entry.semantic_authority)}}</span><h2>Significato del simbolo/segno</h2><div class="meta">${{esc(entry.candidate_summary)}}</div></div><div><strong>Conoscenza disponibile</strong>${{suggestions.length ? suggestions.map(suggestionHtml).join('') : '<p class="meta">Nessun significato trasferibile: serve etichetta umana locale.</p>'}}</div><label>Significato<input data-field="meaning" placeholder="es. COLUMN_PLAN_MARKER"></label><label>Esito<select data-field="verdict"><option value="">— scegli —</option>${{options}}</select></label><label>Revisore<input data-field="reviewer"></label><label>Motivazione<textarea data-field="rationale"></textarea></label></div></div>`;
  root.appendChild(card); drawCrop(card.querySelector('canvas'), entry);
}});

document.getElementById('export').addEventListener('click', () => {{
  const decisions=[];
  document.querySelectorAll('.card').forEach(card => {{
    const value = name => card.querySelector(`[data-field="${{name}}"]`).value.trim();
    const meaning=value('meaning'), verdict=value('verdict'), reviewer=value('reviewer'), rationale=value('rationale');
    if (meaning || verdict || reviewer || rationale) decisions.push({{case_id:card.dataset.caseId,meaning,verdict,reviewer,rationale}});
  }});
  if (!decisions.length) {{ alert('Nessuna decisione compilata.'); return; }}
  const invalid=decisions.find(d => !d.meaning || !d.verdict || !d.reviewer || !d.rationale);
  if (invalid) {{ alert('Completa significato, esito, revisore e motivazione per ogni caso compilato.'); return; }}
  const payload={{schema_version:'{DECISION_SCHEMA}',project_id:DATA.project_id,source_review_package_fingerprint:DATA.source_review_package_fingerprint,decisions}};
  const blob=new Blob([JSON.stringify(payload,null,2)],{{type:'application/json'}}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=`${{DATA.project_id}}_graphic_review_decisions.json`; a.click(); URL.revokeObjectURL(a.href);
}});
</script>
</body>
</html>
"""


def apply_decision_batch(
    *,
    project_db: Path,
    fabric_db: Path,
    review_db: Path,
    decision_batch: dict[str, Any],
) -> dict[str, Any]:
    if decision_batch.get("schema_version") != DECISION_SCHEMA:
        raise ValueError("unsupported decision batch schema")
    decisions = decision_batch.get("decisions") or []
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for decision in decisions:
        case_id = str(decision.get("case_id", "")).strip()
        if not case_id or case_id in seen:
            raise ValueError("decision batch contains missing or duplicate case_id")
        seen.add(case_id)
        results.append(
            workspace.submit_label(
                project_db=project_db,
                fabric_db=fabric_db,
                review_db=review_db,
                case_id=case_id,
                meaning=str(decision.get("meaning", "")),
                verdict=str(decision.get("verdict", "")),
                reviewer=str(decision.get("reviewer", "")),
                rationale=str(decision.get("rationale", "")),
            )
        )
    return {
        "status": "PASS",
        "decision_count": len(results),
        "results": results,
        "canonical_promotion": "DISABLED",
        "automatic_generalization": "DISABLED",
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Reusable CEW browser shell for cross-project graphic review")
    sub = p.add_subparsers(dest="cmd", required=True)

    build = sub.add_parser("build")
    build.add_argument("--project-db", type=Path, required=True)
    build.add_argument("--fabric-db", type=Path, required=True)
    build.add_argument("--review-db", type=Path, required=True)
    build.add_argument("--project-id", required=True)
    build.add_argument("--candidate-package", type=Path, required=True)
    build.add_argument("--context", default="{}")
    build.add_argument("--image-map", default="{}")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--manifest-output", type=Path)

    apply = sub.add_parser("apply")
    apply.add_argument("--project-db", type=Path, required=True)
    apply.add_argument("--fabric-db", type=Path, required=True)
    apply.add_argument("--review-db", type=Path, required=True)
    apply.add_argument("--decisions", type=Path, required=True)

    a = p.parse_args()
    if a.cmd == "build":
        manifest = build_browser_manifest(
            project_db=a.project_db,
            fabric_db=a.fabric_db,
            review_db=a.review_db,
            project_id=a.project_id,
            candidate_package=_read_json(a.candidate_package),
            context=json.loads(a.context),
            image_map=json.loads(a.image_map),
        )
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(render_html(manifest), encoding="utf-8")
        if a.manifest_output:
            a.manifest_output.parent.mkdir(parents=True, exist_ok=True)
            a.manifest_output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": "PASS", "candidate_count": manifest["candidate_count"], "output": str(a.output), "canonical_promotion": "DISABLED"}))
    else:
        print(json.dumps(apply_decision_batch(project_db=a.project_db, fabric_db=a.fabric_db, review_db=a.review_db, decision_batch=_read_json(a.decisions)), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
