#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import html
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

import cew_f7_native_review_service as review_service

ROOT = Path(__file__).resolve().parents[1]
R2HR_ROOT = ROOT / "artifacts" / "cew_r2hr_review"
MANIFEST = R2HR_ROOT / "manifest.json"
TASKS = ROOT / "data/canonical/CEW_ERW_RESOLUTION_TASKS_v1.csv"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
RECEIPT_TYPE = "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1"
ALLOWED_DECISIONS = {
    "SUPPORTED_CONTINUITY_HYPOTHESIS",
    "REJECTED_CONTINUITY_HYPOTHESIS",
    "UNRESOLVED_FROM_CURRENT_VIEW",
}
AUTHORITY_FALSE_FIELDS = (
    "supported_continuity_hypothesis_is_geometry",
    "human_review_is_bridge_acceptance",
    "bridge_candidate_authorized",
    "geometry_materialization_authorized",
    "r2c_scene_adapter_authorized",
    "technical_identity_authorized",
    "structural_identity_authorized",
    "canonical_write_authorized",
)
_original_process_receipt = review_service.process_receipt
_installed = False


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"R2HR_RUNTIME_ARTIFACT_MISSING:{path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _runtime_revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("CEW_RUNTIME_REVISION")
        or "LOCAL"
    ).strip().lower()


def _task_map() -> dict[str, dict[str, str]]:
    with TASKS.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        locator = (row.get("source_locator") or "").strip()
        region_suffix = locator.split("/")[-1]
        if region_suffix:
            result[f"CEW-N12-REG-{region_suffix}"] = row
    return result


def status() -> dict[str, Any]:
    try:
        manifest = _load(MANIFEST)
    except ValueError as exc:
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": str(exc),
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    runtime_revision = _runtime_revision()
    candidate = str(manifest.get("candidate_head_sha", "")).lower()
    if not SHA40.fullmatch(candidate):
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_CANDIDATE_HEAD_INVALID",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    if runtime_revision != "LOCAL" and candidate != runtime_revision:
        return {
            "state": "STALE_REVISION_REJECTED",
            "reason": "R2HR_RUNTIME_REVISION_MISMATCH",
            "candidate_head_sha": candidate,
            "runtime_revision": runtime_revision,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    return {
        "state": "READY_IN_SYSTEM",
        "candidate_head_sha": candidate,
        "build_revision": manifest.get("build_revision"),
        "region_coverage": manifest.get("region_coverage"),
        "gap_hypothesis_total": manifest.get("gap_hypothesis_total"),
        "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
        "submission_mode": "AUTHENTICATED_CEW_RUNTIME_APPEND_ONLY",
        "download_required": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _region_entries() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    manifest = _load(MANIFEST)
    entries: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for entry in manifest.get("regions", []):
        template = _load(R2HR_ROOT / entry["receipt_template_filename"])
        entries.append((entry, template))
    return entries


def _template_for_region(region_id: str) -> dict[str, Any]:
    for _entry, template in _region_entries():
        if template.get("evidence_region_id") == region_id:
            return template
    raise ValueError("R2HR_REGION_NOT_FOUND")


def _data_uri(path: Path) -> str:
    raw = path.read_bytes()
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def _overlay_svg(gaps: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for gap in gaps:
        a = gap["bridge_endpoints_normalized"]["a"]
        b = gap["bridge_endpoints_normalized"]["b"]
        tier = gap["review_tier"]
        css = "r2hr-high" if tier == "HIGH_CONTRAST_REVIEW" else "r2hr-standard"
        gap_id = html.escape(gap["gap_hypothesis_id"], quote=True)
        parts.append(
            f'<g class="r2hr-gap {css}" data-gap-id="{gap_id}">'
            f'<line x1="{float(a[0]):.8f}" y1="{float(a[1]):.8f}" x2="{float(b[0]):.8f}" y2="{float(b[1]):.8f}" vector-effect="non-scaling-stroke" />'
            f'<circle cx="{float(a[0]):.8f}" cy="{float(a[1]):.8f}" r="0.007" vector-effect="non-scaling-stroke" />'
            f'<circle cx="{float(b[0]):.8f}" cy="{float(b[1]):.8f}" r="0.007" vector-effect="non-scaling-stroke" />'
            "</g>"
        )
    return "".join(parts)


def _gap_cards(gaps: list[dict[str, Any]]) -> str:
    cards: list[str] = []
    for index, gap in enumerate(gaps, start=1):
        gid = html.escape(gap["gap_hypothesis_id"], quote=True)
        tier = html.escape(gap["review_tier"])
        m = gap["metric_snapshot"]
        cards.append(
            f'''<article class="r2hr-card" data-gap-id="{gid}">
<h4>{index}. <code>{gid}</code></h4>
<p><strong>{tier}</strong> · supporto {m['r2s_cross_scale_min_support_fraction']} · continuità {m['r2s_cross_scale_min_longest_run_fraction']} · contrasto {m['cross_scale_min_support_contrast']}</p>
<label>Decisione<select class="r2hr-decision"><option value="">— seleziona —</option><option value="SUPPORTED_CONTINUITY_HYPOTHESIS">Continuità supportata</option><option value="REJECTED_CONTINUITY_HYPOTHESIS">Continuità respinta</option><option value="UNRESOLVED_FROM_CURRENT_VIEW">Irrisolta con la vista corrente</option></select></label>
<label>Motivazione<textarea class="r2hr-rationale" maxlength="4000" placeholder="Descrivi ciò che osservi nella fonte e il motivo della decisione."></textarea></label>
</article>'''
        )
    return "".join(cards)


def render_panel() -> str:
    current = status()
    if current["state"] != "READY_IN_SYSTEM":
        return (
            '<section id="r2hr-system-review" class="r2hr-shell r2hr-blocked">'
            '<h2>Revisione R2HR nel sistema</h2>'
            '<p><strong>Non disponibile:</strong> ' + html.escape(str(current.get("reason", current["state"]))) + '.</p>'
            '<p>Fail closed: nessuna decisione viene raccolta e nessuna autorità viene modificata.</p></section>'
        )

    task_map = _task_map()
    sections: list[str] = []
    templates: dict[str, Any] = {}
    for entry, template in _region_entries():
        region = str(template["evidence_region_id"])
        gaps = list(template.get("gaps") or [])
        task = task_map.get(region, {})
        task_id = task.get("task_id", "")
        templates[region] = template
        crop = _data_uri(R2HR_ROOT / entry["source_crop_filename"])
        if gaps:
            review = _gap_cards(gaps)
            action = f'''<div class="r2hr-reviewer"><label>Revisore<input class="r2hr-reviewer-label" maxlength="200" autocomplete="name"></label><label class="r2hr-check"><input class="r2hr-attestation" type="checkbox"> Attesto di aver esaminato direttamente la sorgente visualizzata e che queste sono le mie decisioni.</label><button class="r2hr-submit" type="button">Registra revisione nel sistema</button><pre class="r2hr-result">Nessuna revisione registrata.</pre></div>'''
        else:
            review = '<p class="r2hr-none"><strong>Nessuna ipotesi di gap da classificare in questa regione.</strong></p>'
            action = ""
        sections.append(
            f'''<section class="r2hr-region" data-region-id="{html.escape(region, quote=True)}" data-task-id="{html.escape(task_id, quote=True)}">
<h3>{html.escape(region)} <span>{len(gaps)} gap</span></h3>
<p class="r2hr-meta">Task {html.escape(task_id or 'ND')} · SourceVersion <code>{html.escape(template['source_version_id'])}</code></p>
<div class="r2hr-viewport"><img src="{crop}" alt="Sorgente raster della {html.escape(region)}"><svg viewBox="0 0 1 1" preserveAspectRatio="none" aria-hidden="true">{_overlay_svg(gaps)}</svg></div>
{review}{action}</section>'''
        )

    embedded = json.dumps(templates, ensure_ascii=False).replace("</", "<\\/")
    return f'''
<section id="r2hr-system-review" class="r2hr-shell">
<style>
.r2hr-shell{{max-width:1500px;margin:22px auto;padding:18px;background:#fff;border:2px solid #173f5f;border-radius:12px;color:#17202a}}
.r2hr-shell h2{{margin-top:0}}.r2hr-authority{{border-left:5px solid #8a4b08;background:#fff7e8;padding:10px 12px;margin:12px 0}}
.r2hr-region{{border-top:1px solid #d8dde3;padding-top:18px;margin-top:20px}}.r2hr-region h3{{display:flex;gap:12px;align-items:center}}.r2hr-region h3 span{{font-size:.75rem;border:1px solid #aab5be;border-radius:999px;padding:3px 8px}}
.r2hr-meta{{color:#5d6875;font-size:.9rem}}.r2hr-viewport{{position:relative;overflow:auto;background:#111;border:1px solid #697782;max-height:70vh}}.r2hr-viewport img{{display:block;width:100%;height:auto}}.r2hr-viewport svg{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}
.r2hr-gap line{{fill:none;stroke-width:3px}}.r2hr-gap circle{{fill:none;stroke-width:2px}}.r2hr-high line,.r2hr-high circle{{stroke:#ff2d55;stroke-dasharray:10 7}}.r2hr-standard line,.r2hr-standard circle{{stroke:#00b7ff;stroke-dasharray:3 7;opacity:.8}}
.r2hr-card{{border:1px solid #d8dde3;border-radius:8px;padding:12px;margin:12px 0}}.r2hr-card label,.r2hr-reviewer label{{display:block;font-weight:650;margin:10px 0}}.r2hr-card select,.r2hr-card textarea,.r2hr-reviewer input{{width:100%;box-sizing:border-box;padding:9px;font:inherit}}.r2hr-card textarea{{min-height:85px;resize:vertical}}.r2hr-check{{display:flex!important;gap:8px;align-items:flex-start}}.r2hr-check input{{width:auto!important}}.r2hr-submit{{padding:10px 14px;font-weight:750}}.r2hr-result{{white-space:pre-wrap;background:#eef2f5;padding:10px;border-radius:7px}}.r2hr-none{{padding:12px;background:#eef8f1}}
</style>
<h2>R2HR · Revisione umana delle ipotesi di continuità</h2>
<div class="r2hr-authority"><strong>Operazione interna CEW.</strong> Nessun file deve essere scaricato. La revisione viene registrata nell'audit append-only del sistema. Anche una decisione “supportata” resta <code>HUMAN_REVIEW_EVIDENCE_ONLY</code>: non accetta geometria, non abilita R2C e non scrive nel canonico.</div>
<p>Candidate head <code>{html.escape(str(current['candidate_head_sha']))}</code> · 10 gap totali · revisione vincolata alla stessa revisione runtime.</p>
{''.join(sections)}
<script id="r2hrSystemTemplates" type="application/json">{embedded}</script>
<script>
(()=>{{
const templates=JSON.parse(document.getElementById('r2hrSystemTemplates').textContent);
for(const regionEl of document.querySelectorAll('.r2hr-region')){{
 const button=regionEl.querySelector('.r2hr-submit'); if(!button) continue;
 button.addEventListener('click',async()=>{{
  const box=regionEl.querySelector('.r2hr-result'); const region=regionEl.dataset.regionId; const template=templates[region];
  try{{
   const reviewer=regionEl.querySelector('.r2hr-reviewer-label').value.trim(); const attested=regionEl.querySelector('.r2hr-attestation').checked;
   if(!reviewer) throw new Error('Inserisci il revisore.'); if(!attested) throw new Error('È richiesta l’attestazione del revisore.');
   const decisions=[...regionEl.querySelectorAll('.r2hr-card')].map((card,index)=>{{
    const base=template.gaps.find(g=>g.gap_hypothesis_id===card.dataset.gapId); const decision=card.querySelector('.r2hr-decision').value; const rationale=card.querySelector('.r2hr-rationale').value.trim();
    if(!decision) throw new Error(`Seleziona la decisione per il gap ${{index+1}}.`); if(!rationale) throw new Error(`Inserisci la motivazione per il gap ${{index+1}}.`);
    return {{gap_hypothesis_id:base.gap_hypothesis_id,review_tier:base.review_tier,decision,rationale,candidate_ids:base.candidate_ids,bridge_endpoints_normalized:base.bridge_endpoints_normalized,metric_snapshot:base.metric_snapshot,decision_authority:'HUMAN_REVIEW_EVIDENCE_ONLY',decision_is_geometry_acceptance:false}};
   }});
   const receipt={{schema_version:'1.0',receipt_type:'CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1',candidate_head_sha:template.candidate_head_sha,build_revision:template.build_revision,evidence_region_id:template.evidence_region_id,source_code:template.source_code,source_version_id:template.source_version_id,source_sha256:template.source_sha256,page_id:template.page_id,transform_id:template.transform_id,reviewer_label:reviewer,reviewer_attestation:true,reviewed_at:new Date().toISOString(),decisions,receipt_authority:'HUMAN_REVIEW_EVIDENCE_ONLY',supported_continuity_hypothesis_is_geometry:false,human_review_is_bridge_acceptance:false,bridge_candidate_authorized:false,geometry_materialization_authorized:false,r2c_scene_adapter_authorized:false,technical_identity_authorized:false,structural_identity_authorized:false,canonical_write_authorized:false,engineering_authority_effect:'NONE'}};
   box.textContent='Registrazione CEW in corso…';
   const response=await fetch('/api/f7/receipt',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(receipt)}}); const data=await response.json(); box.textContent=JSON.stringify(data,null,2);
   if(!response.ok||data.state!=='R2HR_REVIEW_EVIDENCE_RECORDED') throw new Error(data.detail||data.reason||data.state||'Registrazione rifiutata');
   button.disabled=true; regionEl.querySelectorAll('select,textarea,input').forEach(el=>el.disabled=true);
  }}catch(error){{box.textContent='R2HR non registrata: '+error.message;}}
 }});
}}
}})();
</script>
</section>'''


def _validate_receipt(receipt: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    if set(receipt) != {
        "schema_version", "receipt_type", "candidate_head_sha", "build_revision", "evidence_region_id",
        "source_code", "source_version_id", "source_sha256", "page_id", "transform_id", "reviewer_label",
        "reviewer_attestation", "reviewed_at", "decisions", "receipt_authority",
        "supported_continuity_hypothesis_is_geometry", "human_review_is_bridge_acceptance",
        "bridge_candidate_authorized", "geometry_materialization_authorized", "r2c_scene_adapter_authorized",
        "technical_identity_authorized", "structural_identity_authorized", "canonical_write_authorized",
        "engineering_authority_effect",
    }:
        raise ValueError("R2HR_RECEIPT_FIELD_SET_MISMATCH")
    if receipt.get("schema_version") != "1.0" or receipt.get("receipt_type") != RECEIPT_TYPE:
        raise ValueError("R2HR_RECEIPT_TYPE_INVALID")
    region = str(receipt.get("evidence_region_id", ""))
    template = _template_for_region(region)
    runtime_revision = _runtime_revision()
    if runtime_revision != "LOCAL" and receipt.get("candidate_head_sha") != runtime_revision:
        raise ValueError("R2HR_RUNTIME_REVISION_MISMATCH")
    for key in ("candidate_head_sha", "build_revision", "evidence_region_id", "source_code", "source_version_id", "source_sha256", "page_id", "transform_id"):
        if receipt.get(key) != template.get(key):
            raise ValueError(f"R2HR_TEMPLATE_IDENTITY_MISMATCH:{key}")
    reviewer = str(receipt.get("reviewer_label", "")).strip()
    if not reviewer or len(reviewer) > 200 or receipt.get("reviewer_attestation") is not True:
        raise ValueError("R2HR_REVIEWER_ATTESTATION_INVALID")
    if receipt.get("receipt_authority") != "HUMAN_REVIEW_EVIDENCE_ONLY" or receipt.get("engineering_authority_effect") != "NONE":
        raise ValueError("R2HR_AUTHORITY_DRIFT")
    for key in AUTHORITY_FALSE_FIELDS:
        if receipt.get(key) is not False:
            raise ValueError(f"R2HR_AUTHORITY_DRIFT:{key}")

    supplied = {row.get("gap_hypothesis_id"): row for row in receipt.get("decisions") or []}
    expected = {row["gap_hypothesis_id"]: row for row in template.get("gaps") or []}
    if not expected or set(supplied) != set(expected):
        raise ValueError("R2HR_GAP_RETENTION_MISMATCH")
    for gap_id, base in expected.items():
        row = supplied[gap_id]
        if row.get("review_tier") != base["review_tier"] or row.get("candidate_ids") != base["candidate_ids"] or row.get("bridge_endpoints_normalized") != base["bridge_endpoints_normalized"] or row.get("metric_snapshot") != base["metric_snapshot"]:
            raise ValueError(f"R2HR_GAP_EVIDENCE_DRIFT:{gap_id}")
        if row.get("decision") not in ALLOWED_DECISIONS or not str(row.get("rationale", "")).strip():
            raise ValueError(f"R2HR_HUMAN_DECISION_INCOMPLETE:{gap_id}")
        if row.get("decision_authority") != "HUMAN_REVIEW_EVIDENCE_ONLY" or row.get("decision_is_geometry_acceptance") is not False:
            raise ValueError(f"R2HR_DECISION_AUTHORITY_DRIFT:{gap_id}")
    task = _task_map().get(region)
    if not task:
        raise ValueError("R2HR_TASK_BINDING_MISSING")
    return template, task


def process_r2hr_receipt(receipt: dict[str, Any], receipt_store: Path) -> dict[str, Any]:
    try:
        _template, task = _validate_receipt(receipt)
        decision_id = f"R2HR-{receipt['evidence_region_id']}-{receipt['candidate_head_sha'][:12]}-{uuid.uuid4().hex[:12]}"
        audit_record = {
            "decision_id": decision_id,
            "task_id": task["task_id"],
            "residual_id": task["residual_id"],
            "timestamp": receipt["reviewed_at"],
            "receipt_type": "CEW_RUNTIME_R2HR_AUDIT_v1",
            "human_review_receipt": receipt,
            "authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
        audit = review_service.persist_runtime_receipt(audit_record, receipt_store)
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "state": "RECEIPT_REJECTED",
            "reason_codes": ["R2HR_SYSTEM_REVIEW_REJECTED"],
            "detail": str(exc),
            "canonical_write_authorized": False,
            "canonical_write_performed": False,
            "engineering_authority_effect": "NONE",
        }
    return {
        "state": "R2HR_REVIEW_EVIDENCE_RECORDED",
        "runtime_receipt": audit,
        "task_id": task["task_id"],
        "residual_id": task["residual_id"],
        "evidence_region_id": receipt["evidence_region_id"],
        "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
        "human_review_is_bridge_acceptance": False,
        "r2c_scene_adapter_authorized": False,
        "canonical_write_authorized": False,
        "canonical_write_performed": False,
        "engineering_authority_effect": "NONE",
    }


def _dispatch_process_receipt(receipt: dict, receipt_store: Path) -> dict:
    if isinstance(receipt, dict) and receipt.get("receipt_type") == RECEIPT_TYPE:
        return process_r2hr_receipt(receipt, receipt_store)
    return _original_process_receipt(receipt, receipt_store)


def install() -> None:
    global _installed
    if _installed:
        return
    review_service.process_receipt = _dispatch_process_receipt
    _installed = True
