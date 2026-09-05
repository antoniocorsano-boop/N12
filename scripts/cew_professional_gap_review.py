#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "artifacts" / "cew_r2hr_review"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_DECISIONS = {
    "SUPPORTED_CONTINUITY_HYPOTHESIS",
    "REJECTED_CONTINUITY_HYPOTHESIS",
    "UNRESOLVED_FROM_CURRENT_VIEW",
}
FALSE_AUTHORITY_KEYS = (
    "supported_continuity_hypothesis_is_geometry",
    "human_review_is_bridge_acceptance",
    "bridge_candidate_authorized",
    "geometry_materialization_authorized",
    "r2c_scene_adapter_authorized",
    "technical_identity_authorized",
    "structural_identity_authorized",
    "canonical_write_authorized",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_revision() -> str | None:
    value = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("CEW_RUNTIME_REVISION")
        or ""
    ).strip().lower()
    return value if SHA40.fullmatch(value) else None


def status() -> dict[str, Any]:
    if not MANIFEST.is_file():
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_MANIFEST_NOT_BUILT",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    try:
        manifest = _load(MANIFEST)
    except Exception:
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_MANIFEST_INVALID",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    if manifest.get("package_contract") != "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_RECEIPT_PACKAGE_v1":
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_CONTRACT_MISMATCH",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    if manifest.get("region_coverage") != "4/4" or manifest.get("gap_hypothesis_total") != 10:
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_COVERAGE_MISMATCH",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    if manifest.get("decision_state") != "HUMAN_GAP_REVIEW_PACKAGE_READY_RECEIPT_NOT_YET_PRODUCED":
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_PACKAGE_STATE_NOT_REVIEWABLE",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    for key in FALSE_AUTHORITY_KEYS:
        if manifest.get(key) is not False:
            return {
                "state": "UNAVAILABLE_FAIL_CLOSED",
                "reason": f"R2HR_AUTHORITY_DRIFT:{key}",
                "canonical_write_authorized": False,
                "engineering_authority_effect": "NONE",
            }
    current = runtime_revision()
    candidate = str(manifest.get("candidate_head_sha", "")).lower()
    if current and candidate != current:
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_RUNTIME_REVISION_MISMATCH",
            "candidate_head_sha": candidate,
            "runtime_revision": current,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    region_rows = manifest.get("regions") or []
    if {row.get("evidence_region_id") for row in region_rows} != EXPECTED_REGIONS:
        return {
            "state": "UNAVAILABLE_FAIL_CLOSED",
            "reason": "R2HR_REGION_SET_MISMATCH",
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
    return {
        "state": "READY",
        "candidate_head_sha": candidate,
        "region_coverage": "4/4",
        "gap_hypothesis_total": 10,
        "regions": [
            {
                "evidence_region_id": row["evidence_region_id"],
                "gap_count": int(row["gap_count"]),
            }
            for row in region_rows
        ],
        "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
        "geometry_materialization_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
    }


def _manifest_region(region_id: str) -> dict[str, Any]:
    state = status()
    if state["state"] != "READY":
        raise ValueError(state.get("reason", "R2HR_UNAVAILABLE"))
    manifest = _load(MANIFEST)
    rows = [row for row in manifest["regions"] if row["evidence_region_id"] == region_id]
    if len(rows) != 1:
        raise ValueError("R2HR_REGION_NOT_FOUND")
    return rows[0]


def template(region_id: str) -> dict[str, Any]:
    if region_id not in EXPECTED_REGIONS:
        raise ValueError("R2HR_REGION_NOT_ALLOWED")
    row = _manifest_region(region_id)
    path = ASSET_ROOT / row["receipt_template_filename"]
    if not path.is_file():
        raise ValueError("R2HR_TEMPLATE_MISSING")
    payload = _load(path)
    if payload.get("evidence_region_id") != region_id or payload.get("template_state") != "UNREVIEWED":
        raise ValueError("R2HR_TEMPLATE_IDENTITY_MISMATCH")
    current = runtime_revision()
    if current and payload.get("candidate_head_sha") != current:
        raise ValueError("R2HR_TEMPLATE_RUNTIME_REVISION_MISMATCH")
    return payload


def source_crop_path(region_id: str) -> Path:
    row = _manifest_region(region_id)
    path = (ASSET_ROOT / row["source_crop_filename"]).resolve()
    root = ASSET_ROOT.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("R2HR_ASSET_PATH_REJECTED") from exc
    if not path.is_file():
        raise ValueError("R2HR_SOURCE_CROP_MISSING")
    return path


def _same_json_value(actual: Any, expected: Any) -> bool:
    return json.dumps(actual, sort_keys=True, separators=(",", ":")) == json.dumps(expected, sort_keys=True, separators=(",", ":"))


def validate_receipt(receipt: dict[str, Any], expected_template: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ValueError("R2HR_RECEIPT_OBJECT_REQUIRED")
    required = {
        "schema_version",
        "receipt_type",
        "candidate_head_sha",
        "build_revision",
        "evidence_region_id",
        "source_code",
        "source_version_id",
        "source_sha256",
        "page_id",
        "transform_id",
        "reviewer_label",
        "reviewer_attestation",
        "reviewed_at",
        "decisions",
        "receipt_authority",
        *FALSE_AUTHORITY_KEYS,
        "engineering_authority_effect",
    }
    if set(receipt) != required:
        raise ValueError("R2HR_RECEIPT_FIELD_SET_MISMATCH")
    if receipt["schema_version"] != "1.0" or receipt["receipt_type"] != "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1":
        raise ValueError("R2HR_RECEIPT_TYPE_MISMATCH")
    for key in (
        "candidate_head_sha",
        "build_revision",
        "evidence_region_id",
        "source_code",
        "source_version_id",
        "source_sha256",
        "page_id",
        "transform_id",
    ):
        if receipt.get(key) != expected_template.get(key):
            raise ValueError(f"R2HR_RECEIPT_PROVENANCE_MISMATCH:{key}")
    current = runtime_revision()
    if current and receipt["candidate_head_sha"] != current:
        raise ValueError("R2HR_RECEIPT_RUNTIME_REVISION_MISMATCH")
    label = receipt.get("reviewer_label")
    if not isinstance(label, str) or not label.strip() or len(label.strip()) > 200:
        raise ValueError("R2HR_REVIEWER_LABEL_INVALID")
    if receipt.get("reviewer_attestation") is not True:
        raise ValueError("R2HR_REVIEWER_ATTESTATION_REQUIRED")
    reviewed_at = receipt.get("reviewed_at")
    if not isinstance(reviewed_at, str):
        raise ValueError("R2HR_REVIEWED_AT_INVALID")
    try:
        datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("R2HR_REVIEWED_AT_INVALID") from exc
    if receipt.get("receipt_authority") != "HUMAN_REVIEW_EVIDENCE_ONLY":
        raise ValueError("R2HR_RECEIPT_AUTHORITY_INVALID")
    for key in FALSE_AUTHORITY_KEYS:
        if receipt.get(key) is not False:
            raise ValueError(f"R2HR_RECEIPT_AUTHORITY_DRIFT:{key}")
    if receipt.get("engineering_authority_effect") != "NONE":
        raise ValueError("R2HR_ENGINEERING_AUTHORITY_EFFECT_FORBIDDEN")

    expected_gaps = {row["gap_hypothesis_id"]: row for row in expected_template.get("gaps") or []}
    decisions = receipt.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != len(expected_gaps):
        raise ValueError("R2HR_DECISION_COUNT_MISMATCH")
    seen: set[str] = set()
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ValueError("R2HR_DECISION_OBJECT_REQUIRED")
        gap_id = decision.get("gap_hypothesis_id")
        if gap_id not in expected_gaps or gap_id in seen:
            raise ValueError("R2HR_DECISION_GAP_SET_MISMATCH")
        seen.add(gap_id)
        base = expected_gaps[gap_id]
        required_decision = {
            "gap_hypothesis_id",
            "review_tier",
            "decision",
            "rationale",
            "candidate_ids",
            "bridge_endpoints_normalized",
            "metric_snapshot",
            "decision_authority",
            "decision_is_geometry_acceptance",
        }
        if set(decision) != required_decision:
            raise ValueError(f"R2HR_DECISION_FIELD_SET_MISMATCH:{gap_id}")
        if decision.get("review_tier") != base.get("review_tier"):
            raise ValueError(f"R2HR_DECISION_TIER_MISMATCH:{gap_id}")
        if decision.get("decision") not in ALLOWED_DECISIONS:
            raise ValueError(f"R2HR_DECISION_VALUE_INVALID:{gap_id}")
        rationale = decision.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale.strip()) > 4000:
            raise ValueError(f"R2HR_DECISION_RATIONALE_INVALID:{gap_id}")
        for key in ("candidate_ids", "bridge_endpoints_normalized", "metric_snapshot"):
            if not _same_json_value(decision.get(key), base.get(key)):
                raise ValueError(f"R2HR_DECISION_EVIDENCE_TAMPERED:{gap_id}:{key}")
        if decision.get("decision_authority") != "HUMAN_REVIEW_EVIDENCE_ONLY":
            raise ValueError(f"R2HR_DECISION_AUTHORITY_INVALID:{gap_id}")
        if decision.get("decision_is_geometry_acceptance") is not False:
            raise ValueError(f"R2HR_DECISION_GEOMETRY_ACCEPTANCE_FORBIDDEN:{gap_id}")
    if seen != set(expected_gaps):
        raise ValueError("R2HR_DECISION_GAP_SET_MISMATCH")
    return receipt


def audit_envelope(task_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
    raw = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    region = re.sub(r"[^A-Za-z0-9._-]", "-", receipt["evidence_region_id"])
    decision_id = f"R2HR-{region}-{receipt['candidate_head_sha'][:12]}-{digest[:16]}"
    return {
        "decision_id": decision_id,
        "task_id": task_id,
        "residual_id": receipt["evidence_region_id"],
        "timestamp": receipt["reviewed_at"],
        "receipt_type": "CEW_PWB005_R2HR_RUNTIME_AUDIT_ENVELOPE_v1",
        "r2hr_receipt": receipt,
        "authority": "RUNTIME_AUDIT_ONLY",
        "canonical_write": False,
        "engineering_authority_effect": "NONE",
        "next_gate": "R2HR_GOVERNED_REVIEW_INGEST_REQUIRED",
    }


def _proposal_svg(row: dict[str, Any]) -> str:
    a = row["bridge_endpoints_normalized"]["a"]
    b = row["bridge_endpoints_normalized"]["b"]
    css = "high" if row["review_tier"] == "HIGH_CONTRAST_REVIEW" else "standard"
    gap_id = html.escape(row["gap_hypothesis_id"], quote=True)
    return (
        f'<g class="gap {css}" data-gap-id="{gap_id}">'
        f'<line x1="{float(a[0]):.8f}" y1="{float(a[1]):.8f}" x2="{float(b[0]):.8f}" y2="{float(b[1]):.8f}" />'
        f'<circle cx="{float(a[0]):.8f}" cy="{float(a[1]):.8f}" r="0.007" />'
        f'<circle cx="{float(b[0]):.8f}" cy="{float(b[1]):.8f}" r="0.007" />'
        "</g>"
    )


def build_review_page(task_id: str, region_id: str) -> str:
    payload = template(region_id)
    gaps = payload.get("gaps") or []
    if not gaps:
        return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Revisione continuità raster</title></head><body style="font-family:system-ui;max-width:900px;margin:40px auto;padding:0 20px"><a href="/workbench?task={html.escape(task_id, quote=True)}">← Torna all'ambiente grafico</a><h1>Nessuna ipotesi di continuità da classificare</h1><p>Per questa evidenza il pacchetto R2HR corrente non contiene gap candidati. Nessuna geometria viene creata.</p></body></html>'''
    overlays = "".join(_proposal_svg(row) for row in gaps)
    cards = []
    for index, row in enumerate(gaps, 1):
        gid = html.escape(row["gap_hypothesis_id"], quote=True)
        tier = "alta evidenza grafica" if row["review_tier"] == "HIGH_CONTRAST_REVIEW" else "revisione standard"
        cards.append(f'''<section class="card" data-gap-id="{gid}"><h2>Ipotesi {index}</h2><p class="meta">{html.escape(tier)}</p><label>Decisione<select class="decision"><option value="">— seleziona —</option><option value="SUPPORTED_CONTINUITY_HYPOTHESIS">Continuità supportata dalla sorgente</option><option value="REJECTED_CONTINUITY_HYPOTHESIS">Continuità respinta dalla sorgente</option><option value="UNRESOLVED_FROM_CURRENT_VIEW">Non risolvibile con questa vista</option></select></label><label>Motivazione<textarea class="rationale" rows="3" maxlength="4000" placeholder="Descrivi ciò che osservi nella sorgente."></textarea></label></section>''')
    embedded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    task_json = json.dumps(task_id, ensure_ascii=False)
    source_href = "/api/source/pdf/" + html.escape(payload["source_code"], quote=True)
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Revisione continuità raster</title><style>
:root{{--ink:#17202a;--muted:#61707c;--line:#cfd6dc;--accent:#173f5f;--warn:#8a4b08}}*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui;background:#eef2f5;color:var(--ink)}}header{{background:#fff;border-bottom:1px solid var(--line);padding:12px 18px;display:flex;gap:12px;align-items:center}}main{{max-width:1450px;margin:auto;padding:16px}}a{{color:var(--accent);font-weight:700}}.notice{{background:#fff7e8;border-left:5px solid var(--warn);padding:10px 12px;margin-bottom:12px}}.layout{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(360px,.75fr);gap:14px}}.viewport{{position:sticky;top:12px;background:#111;border:1px solid #555;max-height:82vh;overflow:auto}}.viewport img{{display:block;width:100%;height:auto}}.viewport svg{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}}.gap line{{fill:none;stroke-width:3px;vector-effect:non-scaling-stroke}}.gap circle{{fill:none;stroke-width:2px;vector-effect:non-scaling-stroke}}.high line,.high circle{{stroke:#ff2d55;stroke-dasharray:10 7}}.standard line,.standard circle{{stroke:#00b7ff;stroke-dasharray:3 7;opacity:.82}}.card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px;margin-bottom:10px}}h1{{font-size:22px}}h2{{font-size:16px;margin:0 0 4px}}.meta{{color:var(--muted);font-size:12px}}label{{display:block;font-weight:700;margin:9px 0}}select,textarea,input{{width:100%;font:inherit;padding:8px;border:1px solid #aeb9c2;border-radius:6px;margin-top:4px}}button{{font:inherit;background:var(--accent);color:#fff;border:0;border-radius:6px;padding:10px 14px;font-weight:800;cursor:pointer}}.receipt{{background:#edf8f1;border-left:4px solid #286044;padding:10px;margin-top:10px}}.error{{background:#fff0f0;border-left:4px solid #a12622;padding:10px;margin-top:10px}}@media(max-width:900px){{.layout{{grid-template-columns:1fr}}.viewport{{position:relative;top:auto}}}}
</style></head><body><header><a href="/workbench?task={html.escape(task_id, quote=True)}">← Ambiente grafico</a><strong>Revisione umana delle ipotesi di continuità</strong><a href="{source_href}" target="_blank" rel="noopener">PDF verificato</a></header><main><div class="notice"><b>Confine di autorità:</b> questa revisione classifica soltanto ipotesi di continuità sul raster sorgente. Anche una continuità supportata <b>non è geometria accettata</b>, non crea identità tecnica o strutturale e non autorizza scritture canoniche.</div><div class="layout"><section><div class="viewport"><img src="/workbench/gap-review/assets/{html.escape(region_id, quote=True)}/source_crop_300.png" alt="Ritaglio della fonte verificata"><svg viewBox="0 0 1 1" preserveAspectRatio="none" aria-hidden="true">{overlays}</svg></div></section><section>{''.join(cards)}<section class="card"><label>Revisore<input id="reviewerLabel" maxlength="200" placeholder="Nome, sigla o identificativo professionale"></label><label><input id="attestation" type="checkbox" style="width:auto"> Attesto di aver esaminato la sorgente visualizzata e che le decisioni riportano la mia revisione effettiva.</label><button id="submitBtn">Registra revisione in CEW</button><div id="result" aria-live="polite"></div></section></section></div></main><script id="template" type="application/json">{embedded}</script><script>
const TASK={task_json};const T=JSON.parse(document.getElementById('template').textContent);const out=document.getElementById('result');
function collect(){{const label=document.getElementById('reviewerLabel').value.trim();if(!label)throw new Error('Inserisci il revisore.');if(!document.getElementById('attestation').checked)throw new Error('È richiesta l’attestazione del revisore.');const cards=[...document.querySelectorAll('.card[data-gap-id]')];const decisions=cards.map((card,i)=>{{const base=T.gaps.find(g=>g.gap_hypothesis_id===card.dataset.gapId);const decision=card.querySelector('.decision').value;const rationale=card.querySelector('.rationale').value.trim();if(!decision)throw new Error(`Seleziona la decisione per l’ipotesi ${{i+1}}.`);if(!rationale)throw new Error(`Inserisci la motivazione per l’ipotesi ${{i+1}}.`);return {{gap_hypothesis_id:base.gap_hypothesis_id,review_tier:base.review_tier,decision,rationale,candidate_ids:base.candidate_ids,bridge_endpoints_normalized:base.bridge_endpoints_normalized,metric_snapshot:base.metric_snapshot,decision_authority:'HUMAN_REVIEW_EVIDENCE_ONLY',decision_is_geometry_acceptance:false}}}});return {{schema_version:'1.0',receipt_type:'CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1',candidate_head_sha:T.candidate_head_sha,build_revision:T.build_revision,evidence_region_id:T.evidence_region_id,source_code:T.source_code,source_version_id:T.source_version_id,source_sha256:T.source_sha256,page_id:T.page_id,transform_id:T.transform_id,reviewer_label:label,reviewer_attestation:true,reviewed_at:new Date().toISOString(),decisions,receipt_authority:'HUMAN_REVIEW_EVIDENCE_ONLY',supported_continuity_hypothesis_is_geometry:false,human_review_is_bridge_acceptance:false,bridge_candidate_authorized:false,geometry_materialization_authorized:false,r2c_scene_adapter_authorized:false,technical_identity_authorized:false,structural_identity_authorized:false,canonical_write_authorized:false,engineering_authority_effect:'NONE'}}}}
document.getElementById('submitBtn').onclick=async()=>{{try{{const receipt=collect();const r=await fetch('/api/workbench/gap-review/receipt',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{task:TASK,receipt}})}});const body=await r.json();if(!r.ok)throw new Error(body.reason||body.state||'Revisione respinta');out.className='receipt';out.textContent='Revisione registrata nell’audit CEW. Nessuna geometria o dato canonico è stato modificato. Ricevuta: '+body.runtime_receipt_id;document.getElementById('submitBtn').disabled=true}}catch(e){{out.className='error';out.textContent=e.message}}}};
</script></body></html>'''
