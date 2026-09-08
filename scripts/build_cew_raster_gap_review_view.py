#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R2_ROOT = ROOT / ".cew_raster_geometry_candidates"
R2_MANIFEST = R2_ROOT / "manifest.json"
R2BR_ROOT = ROOT / ".cew_raster_bridge_review"
R2BR_MANIFEST = R2BR_ROOT / "manifest.json"
ASSET_ROOT = ROOT / "artifacts" / "cew_r2rv_review"
MANIFEST = ASSET_ROOT / "manifest.json"
EXPECTED_REGIONS = {
    "CEW-N12-REG-G01-R06",
    "CEW-N12-REG-G05-R04",
    "CEW-N12-REG-G07-R07",
    "CEW-N12-REG-T6A-G03",
}


def _revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    ).strip()


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"R2RV_REQUIRED_ARTIFACT_MISSING:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _line_svg(row: dict[str, Any]) -> str:
    endpoints = row["bridge_endpoints_normalized"]
    a, b = endpoints["a"], endpoints["b"]
    tier = row["review_tier"]
    if tier == "HIGH_CONTRAST_REVIEW":
        css = "gap high"
        radius = "0.008"
    elif tier == "STANDARD_REVIEW":
        css = "gap standard"
        radius = "0.006"
    else:
        css = "gap incomplete"
        radius = "0.008"
    gap_id = html.escape(row["gap_hypothesis_id"], quote=True)
    return (
        f'<g class="{css}" data-gap-id="{gap_id}">'
        f'<line x1="{float(a[0]):.8f}" y1="{float(a[1]):.8f}" '
        f'x2="{float(b[0]):.8f}" y2="{float(b[1]):.8f}" vector-effect="non-scaling-stroke" />'
        f'<circle cx="{float(a[0]):.8f}" cy="{float(a[1]):.8f}" r="{radius}" vector-effect="non-scaling-stroke" />'
        f'<circle cx="{float(b[0]):.8f}" cy="{float(b[1]):.8f}" r="{radius}" vector-effect="non-scaling-stroke" />'
        '</g>'
    )


def _table_row(row: dict[str, Any]) -> str:
    def f(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.4f}"
        return html.escape(str(value))

    return (
        f'<tr data-tier="{html.escape(row["review_tier"], quote=True)}">'
        f'<td><code>{html.escape(row["gap_hypothesis_id"])}</code></td>'
        f'<td>{html.escape(row["review_tier"])}</td>'
        f'<td>{f(row["r2s_cross_scale_min_support_fraction"])}</td>'
        f'<td>{f(row["r2s_cross_scale_min_longest_run_fraction"])}</td>'
        f'<td>{f(row["cross_scale_min_support_contrast"])}</td>'
        f'<td>{f(row["cross_scale_min_run_contrast"])}</td>'
        f'<td>{f(row["projected_gap_norm"])}</td>'
        f'<td>{f(row["nearest_endpoint_distance_norm"])}</td>'
        '</tr>'
    )


def _render_html(region: dict[str, Any], image_filename: str, revision: str) -> str:
    rows = region["review_rows"]
    overlays = "\n".join(_line_svg(row) for row in rows)
    table_rows = "\n".join(_table_row(row) for row in rows)
    region_id = html.escape(region["evidence_region_id"])
    source_code = html.escape(region["source_code"])
    source_version = html.escape(region["source_version_id"])
    page_id = html.escape(region["page_id"])
    transform_id = html.escape(region["transform_id"])
    image_filename_escaped = html.escape(image_filename, quote=True)
    revision_escaped = html.escape(revision)
    high_count = sum(1 for row in rows if row["review_tier"] == "HIGH_CONTRAST_REVIEW")
    standard_count = sum(1 for row in rows if row["review_tier"] == "STANDARD_REVIEW")
    incomplete_count = sum(1 for row in rows if row["review_tier"] == "CONTROL_INCOMPLETE_REVIEW")

    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>R2RV · {region_id}</title>
<style>
:root {{ font-family: system-ui, sans-serif; color-scheme: light dark; }}
body {{ margin: 0; padding: 18px; background: Canvas; color: CanvasText; }}
header, .notice, .controls, .metrics {{ max-width: 1500px; margin: 0 auto 14px; }}
.notice {{ border: 2px solid currentColor; padding: 10px 12px; font-weight: 650; }}
.meta {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:8px; font-size:.9rem; }}
.viewport {{ position:relative; max-width:1500px; margin:0 auto; overflow:auto; border:1px solid #777; background:#111; }}
.viewport img {{ display:block; width:100%; height:auto; }}
.viewport svg {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }}
.gap line {{ fill:none; stroke-width:3px; }}
.gap circle {{ fill:none; stroke-width:2px; }}
.high line, .high circle {{ stroke:#ff2d55; stroke-dasharray:10 7; }}
.standard line, .standard circle {{ stroke:#00b7ff; stroke-dasharray:3 7; opacity:.78; }}
.incomplete line, .incomplete circle {{ stroke:#ffb000; stroke-dasharray:12 5 2 5; }}
body.hide-high .high {{ display:none; }}
body.hide-standard .standard {{ display:none; }}
body.hide-incomplete .incomplete {{ display:none; }}
.controls label {{ margin-right:18px; }}
table {{ width:100%; border-collapse:collapse; font-size:.82rem; }}
th,td {{ border:1px solid #777; padding:6px; text-align:left; }}
th {{ position:sticky; top:0; background:Canvas; }}
code {{ overflow-wrap:anywhere; }}
.legend span {{ margin-right:16px; }}
.swatch {{ display:inline-block; width:28px; border-top:3px dashed currentColor; vertical-align:middle; }}
.high-key {{ color:#ff2d55; }} .standard-key {{ color:#00b7ff; }} .incomplete-key {{ color:#ffb000; }}
</style>
</head>
<body>
<header>
<h1>R2RV · Raster Gap Review View</h1>
<p><strong>{region_id}</strong> · {source_code}</p>
<div class="meta">
<div>SourceVersion: <code>{source_version}</code></div>
<div>Page: <code>{page_id}</code></div>
<div>Transform: <code>{transform_id}</code></div>
<div>Build revision: <code>{revision_escaped}</code></div>
</div>
</header>
<div class="notice">SOLO ISPEZIONE UMANA — le sovrapposizioni sono ipotesi di continuità. Non sono geometria tecnica, non sono elementi strutturali e non autorizzano alcuna scrittura canonica.</div>
<div class="controls">
<label><input id="toggleHigh" type="checkbox" checked> HIGH_CONTRAST_REVIEW ({high_count})</label>
<label><input id="toggleStandard" type="checkbox" checked> STANDARD_REVIEW ({standard_count})</label>
<label><input id="toggleIncomplete" type="checkbox" checked> CONTROL_INCOMPLETE_REVIEW ({incomplete_count})</label>
<div class="legend"><span class="high-key"><i class="swatch"></i> priorità alta</span><span class="standard-key"><i class="swatch"></i> standard</span><span class="incomplete-key"><i class="swatch"></i> controllo incompleto</span></div>
</div>
<div class="viewport">
<img src="{image_filename_escaped}" alt="Crop raster sorgente della EvidenceRegion {region_id}">
<svg viewBox="0 0 1 1" preserveAspectRatio="none" aria-hidden="true">
{overlays}
</svg>
</div>
<div class="metrics">
<h2>Misure di revisione</h2>
<table>
<thead><tr><th>Gap</th><th>Review tier</th><th>Support</th><th>Longest run</th><th>Support contrast</th><th>Run contrast</th><th>Projected gap</th><th>Endpoint distance</th></tr></thead>
<tbody>{table_rows}</tbody>
</table>
<p><strong>Authority:</strong> NONE · <strong>Overlay role:</strong> HUMAN_INSPECTION_PROPOSAL_ONLY · <strong>Bridge candidate:</strong> false · <strong>R2C:</strong> false · <strong>Canonical write:</strong> false.</p>
</div>
<script>
const bind=(id,cls)=>document.getElementById(id).addEventListener('change',e=>document.body.classList.toggle(cls,!e.target.checked));
bind('toggleHigh','hide-high'); bind('toggleStandard','hide-standard'); bind('toggleIncomplete','hide-incomplete');
</script>
</body>
</html>
"""


def build() -> dict[str, Any]:
    revision = _revision()
    r2 = _load(R2_MANIFEST)
    r2br = _load(R2BR_MANIFEST)
    if r2.get("build_revision") != revision or r2br.get("build_revision") != revision:
        raise AssertionError("R2RV_INPUT_REVISION_MISMATCH")
    if r2br.get("decision_state") != "BRIDGE_REVIEW_LAYER_READY_HUMAN_INSPECTION_REQUIRED":
        raise AssertionError("R2RV_REQUIRES_R2BR_READY")
    if r2br.get("bridge_candidate_authorized") is not False or r2br.get("r2c_scene_adapter_authorized") is not False:
        raise AssertionError("R2RV_REQUIRES_AUTHORITY_BLOCKS")

    r2_entries = {row["evidence_region_id"]: row for row in r2["region_entries"]}
    r2br_entries = {row["evidence_region_id"]: row for row in r2br["regions"]}
    if set(r2_entries) != EXPECTED_REGIONS or set(r2br_entries) != EXPECTED_REGIONS:
        raise AssertionError("R2RV_REGION_COVERAGE_MISMATCH")

    if ASSET_ROOT.exists():
        shutil.rmtree(ASSET_ROOT)
    ASSET_ROOT.mkdir(parents=True, exist_ok=True)

    output_regions = []
    total = high = standard = incomplete = 0
    index_links = []

    for region_id in sorted(EXPECTED_REGIONS):
        r2_entry = r2_entries[region_id]
        review = _load(R2BR_ROOT / r2br_entries[region_id]["result_filename"])
        crop_source = R2_ROOT / r2_entry["crop_300_filename"]
        expected_crop_sha = r2_entry["crop_300_sha256"]
        if not crop_source.is_file() or _sha256(crop_source) != expected_crop_sha:
            raise AssertionError(f"R2RV_CROP_IDENTITY_FAILURE:{region_id}")

        region_dir = ASSET_ROOT / region_id
        region_dir.mkdir(parents=True, exist_ok=True)
        crop_target = region_dir / "source_crop_300.png"
        shutil.copyfile(crop_source, crop_target)
        if _sha256(crop_target) != expected_crop_sha:
            raise AssertionError(f"R2RV_CROP_COPY_IDENTITY_FAILURE:{region_id}")

        rows = review["review_rows"]
        region_high = sum(1 for row in rows if row["review_tier"] == "HIGH_CONTRAST_REVIEW")
        region_standard = sum(1 for row in rows if row["review_tier"] == "STANDARD_REVIEW")
        region_incomplete = sum(1 for row in rows if row["review_tier"] == "CONTROL_INCOMPLETE_REVIEW")
        total += len(rows)
        high += region_high
        standard += region_standard
        incomplete += region_incomplete

        metadata = {
            "schema_version": "1.0",
            "review_view_contract": "CEW_PWB005_R2RV_RASTER_GAP_REVIEW_VIEW_v1",
            "build_revision": revision,
            "evidence_region_id": region_id,
            "source_code": review["source_code"],
            "source_version_id": review["source_version_id"],
            "source_sha256": review["source_sha256"],
            "page_id": review["page_id"],
            "transform_id": review["transform_id"],
            "source_crop_300_filename": crop_target.name,
            "source_crop_300_sha256": expected_crop_sha,
            "gap_hypothesis_total": len(rows),
            "high_contrast_review_count": region_high,
            "standard_review_count": region_standard,
            "control_incomplete_review_count": region_incomplete,
            "review_rows": rows,
            "review_view_authority": "NONE",
            "overlay_role": "HUMAN_INSPECTION_PROPOSAL_ONLY",
            "review_priority_is_correctness_threshold": False,
            "gap_overlay_is_geometry": False,
            "bridge_candidate_authorized": False,
            "geometry_materialization_authorized": False,
            "r2c_scene_adapter_authorized": False,
            "technical_identity_authorized": False,
            "structural_identity_authorized": False,
            "canonical_write_authorized": False,
            "engineering_authority_effect": "NONE",
        }
        metadata_path = region_dir / "review.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        html_path = region_dir / "index.html"
        html_path.write_text(_render_html(metadata, crop_target.name, revision), encoding="utf-8")

        output_regions.append({
            "evidence_region_id": region_id,
            "directory": region_id,
            "html_filename": f"{region_id}/index.html",
            "html_sha256": _sha256(html_path),
            "metadata_filename": f"{region_id}/review.json",
            "metadata_sha256": _sha256(metadata_path),
            "source_crop_300_filename": f"{region_id}/source_crop_300.png",
            "source_crop_300_sha256": expected_crop_sha,
            "gap_count": len(rows),
            "high_contrast_review_count": region_high,
            "standard_review_count": region_standard,
            "control_incomplete_review_count": region_incomplete,
        })
        index_links.append(
            f'<li><a href="{html.escape(region_id, quote=True)}/index.html">{html.escape(region_id)}</a> — '
            f'{region_high} high / {region_standard} standard / {region_incomplete} incomplete</li>'
        )

    if total != 10 or high != 5 or standard != 5 or incomplete != 0:
        raise AssertionError(f"R2RV_EXPECTED_REVIEW_INVENTORY_MISMATCH:{total}:{high}:{standard}:{incomplete}")

    index_html = (
        '<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>CEW R2RV review package</title></head><body>'
        '<h1>CEW R2RV · Raster Gap Review Package</h1>'
        '<p><strong>Solo ispezione umana.</strong> Nessuna geometria tecnica o strutturale è autorizzata.</p><ul>'
        + ''.join(index_links)
        + '</ul><p>review_view_authority=NONE · bridge_candidate_authorized=false · r2c_scene_adapter_authorized=false · canonical_write_authorized=false</p>'
        '</body></html>'
    )
    index_path = ASSET_ROOT / "index.html"
    index_path.write_text(index_html, encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "review_view_contract": "CEW_PWB005_R2RV_RASTER_GAP_REVIEW_VIEW_v1",
        "build_revision": revision,
        "region_coverage": "4/4",
        "gap_hypothesis_total": total,
        "high_contrast_review_total": high,
        "standard_review_total": standard,
        "control_incomplete_review_total": incomplete,
        "regions": output_regions,
        "index_filename": "index.html",
        "index_sha256": _sha256(index_path),
        "artifact_role": "REVISION_BOUND_HUMAN_INSPECTION_PACKAGE",
        "runtime_dependency": False,
        "review_view_authority": "NONE",
        "overlay_role": "HUMAN_INSPECTION_PROPOSAL_ONLY",
        "review_priority_is_correctness_threshold": False,
        "gap_overlay_is_geometry": False,
        "bridge_candidate_authorized": False,
        "geometry_materialization_authorized": False,
        "r2c_scene_adapter_authorized": False,
        "technical_identity_authorized": False,
        "structural_identity_authorized": False,
        "canonical_write_authorized": False,
        "engineering_authority_effect": "NONE",
        "decision_state": "REVIEW_PACKAGE_READY_HUMAN_INSPECTION_REQUIRED",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("CEW_PWB005_R2RV_RASTER_GAP_REVIEW_VIEW_BUILD = PASS")
    print("REGION_COVERAGE = 4/4")
    print("GAP_HYPOTHESIS_TOTAL = 10")
    print("HIGH_CONTRAST_REVIEW_TOTAL = 5")
    print("STANDARD_REVIEW_TOTAL = 5")
    print("CONTROL_INCOMPLETE_REVIEW_TOTAL = 0")
    print("REVIEW_PACKAGE = artifacts/cew_r2rv_review")
    print("REVIEW_VIEW_AUTHORITY = NONE")
    print("GAP_OVERLAY_IS_GEOMETRY = false")
    print("R2_BRIDGE_CANDIDATE_AUTHORIZED = false")
    print("PWB005_R2C_SCENE_ADAPTER_AUTHORIZED = false")
    print("CANONICAL_WRITE_AUTHORIZED = false")
    return manifest


if __name__ == "__main__":
    build()
