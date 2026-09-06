#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R2RV_ROOT = ROOT / "artifacts" / "cew_r2rv_review"
R2RV_MANIFEST = R2RV_ROOT / "manifest.json"
R2BR_ROOT = ROOT / ".cew_raster_bridge_review"
R2BR_MANIFEST = R2BR_ROOT / "manifest.json"
SCHEMA_PATH = ROOT / "automation" / "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_RECEIPT_SCHEMA_v1.json"
ASSET_ROOT = ROOT / "artifacts" / "cew_r2hr_review"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2HR_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _candidate_head_sha() -> str:
    value = os.getenv("CEW_REVIEW_HEAD_SHA", "").strip().lower()
    if not SHA40.fullmatch(value):
        raise AssertionError("R2HR_CANDIDATE_HEAD_SHA_REQUIRED")
    return value


def _metric_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "projected_gap_norm": row["projected_gap_norm"],
        "nearest_endpoint_distance_norm": row["nearest_endpoint_distance_norm"],
        "r2s_cross_scale_min_support_fraction": row["r2s_cross_scale_min_support_fraction"],
        "r2s_cross_scale_min_longest_run_fraction": row["r2s_cross_scale_min_longest_run_fraction"],
        "cross_scale_min_support_contrast": row["cross_scale_min_support_contrast"],
        "cross_scale_min_run_contrast": row["cross_scale_min_run_contrast"],
    }


def _proposal_svg(row: dict[str, Any]) -> str:
    a = row["bridge_endpoints_normalized"]["a"]
    b = row["bridge_endpoints_normalized"]["b"]
    tier = row["review_tier"]
    css = "high" if tier == "HIGH_CONTRAST_REVIEW" else "standard" if tier == "STANDARD_REVIEW" else "incomplete"
    gap_id = html.escape(row["gap_hypothesis_id"], quote=True)
    return (
        f'<g class="gap {css}" data-gap-id="{gap_id}">'
        f'<line x1="{float(a[0]):.8f}" y1="{float(a[1]):.8f}" x2="{float(b[0]):.8f}" y2="{float(b[1]):.8f}" vector-effect="non-scaling-stroke" />'
        f'<circle cx="{float(a[0]):.8f}" cy="{float(a[1]):.8f}" r="0.007" vector-effect="non-scaling-stroke" />'
        f'<circle cx="{float(b[0]):.8f}" cy="{float(b[1]):.8f}" r="0.007" vector-effect="non-scaling-stroke" />'
        '</g>'
    )


def _decision_card(row: dict[str, Any], index: int) -> str:
    gap = html.escape(row["gap_hypothesis_id"])
    tier = html.escape(row["review_tier"])
    metrics = row["metric_snapshot"]
    return f"""
<section class="decision-card" data-gap-id="{gap}">
  <h3>{index}. <code>{gap}</code></h3>
  <p><strong>{tier}</strong> · supporto {metrics['r2s_cross_scale_min_support_fraction']} · run {metrics['r2s_cross_scale_min_longest_run_fraction']} · contrasto {metrics['cross_scale_min_support_contrast']} · run contrast {metrics['cross_scale_min_run_contrast']}</p>
  <label>Decisione
    <select class="decision" required>
      <option value="">— seleziona —</option>
      <option value="SUPPORTED_CONTINUITY_HYPOTHESIS">Ipotesi di continuità supportata</option>
      <option value="REJECTED_CONTINUITY_HYPOTHESIS">Ipotesi di continuità respinta</option>
      <option value="UNRESOLVED_FROM_CURRENT_VIEW">Irrisolta con la vista corrente</option>
    </select>
  </label>
  <label>Motivazione
    <textarea class="rationale" rows="3" maxlength="4000" required placeholder="Descrivi cosa osservi nella sorgente e perché questa ipotesi è supportata, respinta o resta irrisolta."></textarea>
  </label>
</section>
"""


def _render_html(template: dict[str, Any]) -> str:
    rows = template["gaps"]
    overlays = "\n".join(_proposal_svg(row) for row in rows)
    cards = "\n".join(_decision_card(row, index + 1) for index, row in enumerate(rows))
    embedded = json.dumps(template, ensure_ascii=False).replace("</", "<\\/")
    region = html.escape(template["evidence_region_id"])
    image = html.escape(template["source_crop_filename"], quote=True)
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>R2HR · {region}</title>
<style>
:root {{ font-family: system-ui, sans-serif; color-scheme: light dark; }}
body {{ margin:0; padding:18px; background:Canvas; color:CanvasText; }}
main {{ max-width:1500px; margin:auto; }}
.notice {{ border:2px solid currentColor; padding:10px 12px; font-weight:700; margin-bottom:14px; }}
.meta {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:8px; font-size:.88rem; margin-bottom:14px; }}
.viewport {{ position:relative; overflow:auto; border:1px solid #777; background:#111; margin-bottom:18px; }}
.viewport img {{ display:block; width:100%; height:auto; }}
.viewport svg {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }}
.gap line {{ fill:none; stroke-width:3px; }} .gap circle {{ fill:none; stroke-width:2px; }}
.high line,.high circle {{ stroke:#ff2d55; stroke-dasharray:10 7; }}
.standard line,.standard circle {{ stroke:#00b7ff; stroke-dasharray:3 7; opacity:.78; }}
.incomplete line,.incomplete circle {{ stroke:#ffb000; stroke-dasharray:12 5 2 5; }}
.decision-card {{ border:1px solid #777; padding:12px; margin:12px 0; }}
label {{ display:block; margin:10px 0; font-weight:650; }} select,textarea,input[type=text] {{ width:100%; box-sizing:border-box; font:inherit; padding:8px; }}
textarea {{ resize:vertical; }}
.actions {{ position:sticky; bottom:0; background:Canvas; border-top:1px solid #777; padding:12px 0; }}
button {{ font:inherit; padding:10px 14px; }}
.status {{ margin-left:12px; font-weight:650; }}
code {{ overflow-wrap:anywhere; }}
</style>
</head>
<body>
<main>
<h1>R2HR · Revisione umana delle ipotesi di continuità</h1>
<div class="notice">EVIDENZA DI REVISIONE UMANA SOLTANTO — anche “supportata” non significa geometria accettata. Nessun bridge, R2C o dato canonico viene creato da questa pagina.</div>
<div class="meta">
<div>EvidenceRegion: <code>{region}</code></div>
<div>SourceVersion: <code>{html.escape(template['source_version_id'])}</code></div>
<div>Candidate head: <code>{html.escape(template['candidate_head_sha'])}</code></div>
<div>Build revision: <code>{html.escape(template['build_revision'])}</code></div>
</div>
<div class="viewport">
<img src="{image}" alt="Crop raster sorgente della EvidenceRegion {region}">
<svg viewBox="0 0 1 1" preserveAspectRatio="none" aria-hidden="true">{overlays}</svg>
</div>
<h2>Classificazione delle ipotesi</h2>
<p>Completa tutte le decisioni della regione. Ogni motivazione deve riferirsi a ciò che è osservabile nella sorgente.</p>
{cards}
<section class="decision-card">
<label>Etichetta revisore
<input id="reviewerLabel" type="text" maxlength="200" required placeholder="Nome, sigla o identificativo professionale usato per questa revisione"></label>
<label><input id="attestation" type="checkbox"> Attesto di aver esaminato la sorgente visualizzata e che le classificazioni sopra riportano la mia revisione effettiva.</label>
</section>
<div class="actions"><button id="exportBtn" type="button">Esporta review JSON</button><span id="status" class="status" aria-live="polite"></span></div>
</main>
<script id="r2hrTemplate" type="application/json">{embedded}</script>
<script>
const template=JSON.parse(document.getElementById('r2hrTemplate').textContent);
const statusEl=document.getElementById('status');
function collect(){{
  const label=document.getElementById('reviewerLabel').value.trim();
  const attestation=document.getElementById('attestation').checked;
  if(!label) throw new Error('Inserisci l’etichetta del revisore.');
  if(!attestation) throw new Error('È richiesta l’attestazione del revisore.');
  const cards=[...document.querySelectorAll('.decision-card[data-gap-id]')];
  const decisions=cards.map((card,index)=>{{
    const decision=card.querySelector('.decision').value;
    const rationale=card.querySelector('.rationale').value.trim();
    if(!decision) throw new Error(`Seleziona una decisione per l’ipotesi ${{index+1}}.`);
    if(!rationale) throw new Error(`Inserisci una motivazione per l’ipotesi ${{index+1}}.`);
    const base=template.gaps.find(g=>g.gap_hypothesis_id===card.dataset.gapId);
    return {{
      gap_hypothesis_id:base.gap_hypothesis_id,
      review_tier:base.review_tier,
      decision,
      rationale,
      candidate_ids:base.candidate_ids,
      bridge_endpoints_normalized:base.bridge_endpoints_normalized,
      metric_snapshot:base.metric_snapshot,
      decision_authority:'HUMAN_REVIEW_EVIDENCE_ONLY',
      decision_is_geometry_acceptance:false
    }};
  }});
  return {{
    schema_version:'1.0',
    receipt_type:'CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_v1',
    candidate_head_sha:template.candidate_head_sha,
    build_revision:template.build_revision,
    evidence_region_id:template.evidence_region_id,
    source_code:template.source_code,
    source_version_id:template.source_version_id,
    source_sha256:template.source_sha256,
    page_id:template.page_id,
    transform_id:template.transform_id,
    reviewer_label:label,
    reviewer_attestation:true,
    reviewed_at:new Date().toISOString(),
    decisions,
    receipt_authority:'HUMAN_REVIEW_EVIDENCE_ONLY',
    supported_continuity_hypothesis_is_geometry:false,
    human_review_is_bridge_acceptance:false,
    bridge_candidate_authorized:false,
    geometry_materialization_authorized:false,
    r2c_scene_adapter_authorized:false,
    technical_identity_authorized:false,
    structural_identity_authorized:false,
    canonical_write_authorized:false,
    engineering_authority_effect:'NONE'
  }};
}}
document.getElementById('exportBtn').addEventListener('click',()=>{{
  try{{
    const receipt=collect();
    const blob=new Blob([JSON.stringify(receipt,null,2)+'\\n'],{{type:'application/json'}});
    const url=URL.createObjectURL(blob);
    const a=document.createElement('a');
    a.href=url;
    a.download=`CEW_R2HR_${{template.evidence_region_id}}_${{template.candidate_head_sha.slice(0,12)}}.json`;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    statusEl.textContent='Review JSON esportato. Nessuna scrittura CEW è stata eseguita.';
  }}catch(error){{ statusEl.textContent=error.message; }}
}});
</script>
</body>
</html>
"""


def build() -> dict[str, Any]:
    head_sha = _candidate_head_sha()
    r2rv = _load(R2RV_MANIFEST)
    r2br = _load(R2BR_MANIFEST)
    schema = _load(SCHEMA_PATH)
    build_revision = str(r2rv.get("build_revision", ""))
    if not SHA40.fullmatch(build_revision):
        raise AssertionError("R2HR_BUILD_REVISION_INVALID")
    if r2br.get("build_revision") != build_revision:
        raise AssertionError("R2HR_R2RV_R2BR_REVISION_MISMATCH")
    if r2rv.get("decision_state") != "REVIEW_PACKAGE_READY_HUMAN_INSPECTION_REQUIRED":
        raise AssertionError("R2HR_REQUIRES_R2RV_READY")
    if r2br.get("decision_state") != "BRIDGE_REVIEW_LAYER_READY_HUMAN_INSPECTION_REQUIRED":
        raise AssertionError("R2HR_REQUIRES_R2BR_READY")
    if schema.get("$id") != "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_RECEIPT_SCHEMA_v1":
        raise AssertionError("R2HR_SCHEMA_ID_MISMATCH")
    for artifact in (r2rv, r2br):
        for key in (
            "bridge_candidate_authorized",
            "geometry_materialization_authorized",
            "r2c_scene_adapter_authorized",
            "technical_identity_authorized",
            "structural_identity_authorized",
            "canonical_write_authorized",
        ):
            if artifact.get(key) is not False:
                raise AssertionError(f"R2HR_UPSTREAM_AUTHORITY_DRIFT:{key}")

    rv_entries = {row["evidence_region_id"]: row for row in r2rv["regions"]}
    br_entries = {row["evidence_region_id"]: row for row in r2br["regions"]}
    if set(rv_entries) != EXPECTED_REGIONS or set(br_entries) != EXPECTED_REGIONS:
        raise AssertionError("R2HR_REGION_COVERAGE_MISMATCH")

    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)

    regions: list[dict[str, Any]] = []
    total = high = standard = incomplete = 0
    index_links: list[str] = []

    for region_id in sorted(EXPECTED_REGIONS):
        rv_entry = rv_entries[region_id]
        rv_review = _load(R2RV_ROOT / rv_entry["metadata_filename"])
        br_review = _load(R2BR_ROOT / br_entries[region_id]["result_filename"])
        if rv_review["review_rows"] != br_review["review_rows"]:
            raise AssertionError(f"R2HR_REVIEW_ROW_DRIFT:{region_id}")
        for key in ("source_code", "source_version_id", "source_sha256", "page_id", "transform_id"):
            if rv_review[key] != br_review[key]:
                raise AssertionError(f"R2HR_PROVENANCE_DRIFT:{region_id}:{key}")

        source_crop = R2RV_ROOT / rv_entry["source_crop_300_filename"]
        if not source_crop.is_file() or _sha256(source_crop) != rv_entry["source_crop_300_sha256"]:
            raise AssertionError(f"R2HR_SOURCE_CROP_IDENTITY_FAILURE:{region_id}")

        region_dir = ASSET_ROOT / region_id
        region_dir.mkdir(parents=True, exist_ok=True)
        crop_target = region_dir / "source_crop_300.png"
        shutil.copyfile(source_crop, crop_target)

        gaps = []
        for row in br_review["review_rows"]:
            gaps.append({
                "gap_hypothesis_id": row["gap_hypothesis_id"],
                "review_tier": row["review_tier"],
                "candidate_ids": row["candidate_ids"],
                "bridge_endpoints_normalized": row["bridge_endpoints_normalized"],
                "metric_snapshot": _metric_snapshot(row),
            })
        region_high = sum(1 for row in gaps if row["review_tier"] == "HIGH_CONTRAST_REVIEW")
        region_standard = sum(1 for row in gaps if row["review_tier"] == "STANDARD_REVIEW")
        region_incomplete = sum(1 for row in gaps if row["review_tier"] == "CONTROL_INCOMPLETE_REVIEW")
        total += len(gaps); high += region_high; standard += region_standard; incomplete += region_incomplete

        template = {
            "schema_version": "1.0",
            "template_type": "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_TEMPLATE_v1",
            "receipt_schema_id": schema["$id"],
            "candidate_head_sha": head_sha,
            "build_revision": build_revision,
            "evidence_region_id": region_id,
            "source_code": rv_review["source_code"],
            "source_version_id": rv_review["source_version_id"],
            "source_sha256": rv_review["source_sha256"],
            "page_id": rv_review["page_id"],
            "transform_id": rv_review["transform_id"],
            "source_crop_filename": crop_target.name,
            "source_crop_sha256": rv_entry["source_crop_300_sha256"],
            "gaps": gaps,
            "allowed_decisions": [
                "SUPPORTED_CONTINUITY_HYPOTHESIS",
                "REJECTED_CONTINUITY_HYPOTHESIS",
                "UNRESOLVED_FROM_CURRENT_VIEW",
            ],
            "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
            "supported_continuity_hypothesis_is_geometry": False,
            "human_review_is_bridge_acceptance": False,
            "bridge_candidate_authorized": False,
            "geometry_materialization_authorized": False,
            "r2c_scene_adapter_authorized": False,
            "technical_identity_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
            "template_state": "UNREVIEWED",
        }
        template_path = region_dir / "receipt_template.json"
        template_path.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        html_path = region_dir / "index.html"
        html_path.write_text(_render_html(template), encoding="utf-8")

        regions.append({
            "evidence_region_id": region_id,
            "directory": region_id,
            "html_filename": f"{region_id}/index.html",
            "html_sha256": _sha256(html_path),
            "receipt_template_filename": f"{region_id}/receipt_template.json",
            "receipt_template_sha256": _sha256(template_path),
            "source_crop_filename": f"{region_id}/source_crop_300.png",
            "source_crop_sha256": _sha256(crop_target),
            "gap_count": len(gaps),
            "high_contrast_review_count": region_high,
            "standard_review_count": region_standard,
            "control_incomplete_review_count": region_incomplete,
        })
        index_links.append(
            f'<li><a href="{html.escape(region_id, quote=True)}/index.html">{html.escape(region_id)}</a> — '
            f'{len(gaps)} gap, {region_high} high / {region_standard} standard</li>'
        )

    if (total, high, standard, incomplete) != (10, 5, 5, 0):
        raise AssertionError(f"R2HR_REVIEW_INVENTORY_MISMATCH:{total}:{high}:{standard}:{incomplete}")

    index_path = ASSET_ROOT / "index.html"
    index_path.write_text(
        '<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>CEW R2HR human review package</title></head><body>'
        '<h1>CEW R2HR · Human Gap Review Receipt</h1>'
        '<p><strong>Review evidence only.</strong> Le decisioni esportate non accettano geometria e non scrivono nel canonico.</p>'
        '<p>Candidate head: <code>' + html.escape(head_sha) + '</code><br>Build revision: <code>' + html.escape(build_revision) + '</code></p><ul>'
        + ''.join(index_links)
        + '</ul><p>receipt_authority=HUMAN_REVIEW_EVIDENCE_ONLY · human_review_is_bridge_acceptance=false · r2c_scene_adapter_authorized=false · canonical_write_authorized=false</p>'
        '</body></html>',
        encoding="utf-8",
    )

    manifest = {
        "schema_version": "1.0",
        "package_contract": "CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_RECEIPT_PACKAGE_v1",
        "receipt_schema_id": schema["$id"],
        "candidate_head_sha": head_sha,
        "build_revision": build_revision,
        "region_coverage": "4/4",
        "gap_hypothesis_total": total,
        "high_contrast_review_total": high,
        "standard_review_total": standard,
        "control_incomplete_review_total": incomplete,
        "regions": regions,
        "index_filename": "index.html",
        "index_sha256": _sha256(index_path),
        "artifact_role": "REVISION_BOUND_HUMAN_GAP_REVIEW_PACKAGE",
        "runtime_dependency": False,
        "receipt_authority": "HUMAN_REVIEW_EVIDENCE_ONLY",
        "supported_continuity_hypothesis_is_geometry": False,
        "human_review_is_bridge_acceptance": False,
        "bridge_candidate_authorized": False,
        "geometry_materialization_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "decision_state": "HUMAN_GAP_REVIEW_PACKAGE_READY_RECEIPT_NOT_YET_PRODUCED",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2HR_HUMAN_GAP_REVIEW_PACKAGE_BUILD = PASS")
    print("CANDIDATE_HEAD_SHA = " + head_sha)
    print("BUILD_REVISION = " + build_revision)
    print("HEAD_AND_BUILD_IDENTITY_DISTINCT_FIELDS = true")
    print("REGION_COVERAGE = 4/4")
    print("GAP_HYPOTHESIS_TOTAL = 10")
    print("HIGH_CONTRAST_REVIEW_TOTAL = 5")
    print("STANDARD_REVIEW_TOTAL = 5")
    print("RECEIPT_AUTHORITY = HUMAN_REVIEW_EVIDENCE_ONLY")
    print("HUMAN_REVIEW_IS_BRIDGE_ACCEPTANCE = false")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("PWB005_R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
