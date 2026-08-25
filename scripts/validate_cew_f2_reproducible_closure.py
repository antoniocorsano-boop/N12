#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = {"T5A-G01/G01-R06", "T5A-G07/G07-R07", "T5A-G05/G05-R04", "T6A-G03"}
FINAL_STATES = {"READABLE", "PARTIAL", "UNREADABLE", "GRAPHICALLY_DIRECT_PARTIAL"}
TOL = 1e-6


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def materialize(locator: str) -> bytes:
    m = re.fullmatch(r"git\+github://[^@]+@([0-9a-f]{40})/(.+)", locator)
    if not m:
        raise AssertionError(f"unsupported immutable locator: {locator}")
    commit, path = m.groups()
    p = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise AssertionError(f"cannot materialize immutable source {commit}:{path}: {p.stderr.decode(errors='replace')}")
    return p.stdout


def close(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    contract = json.loads((ROOT / "automation/CEW_EVIDENCE_PROVENANCE_CONTRACT_v1.json").read_text(encoding="utf-8"))
    if contract["required_chain"] != ["SourceVersion", "Page", "PageTransform", "EvidenceRegion", "Observation"]:
        raise AssertionError("F2 required chain is not the reproducible closure chain")
    inv = contract["invariants"]
    for key in (
        "ready_region_requires_transform",
        "ready_region_requires_localization_receipt",
        "ready_region_requires_reproducible_derived_asset_when_used_for_adjudication",
    ):
        if inv.get(key) is not True:
            raise AssertionError(f"missing strict F2 invariant: {key}")
    if inv.get("viewer_may_correct_evidence_geometry") is not False:
        raise AssertionError("F3 must not correct F2 geometry")
    if inv.get("observation_may_assert_structural_member_binding") is not False:
        raise AssertionError("Observation must remain outside structural binding authority")

    sources = {r["source_version_id"]: r for r in rows("data/canonical/CEW_SOURCE_IDENTITY_REGISTRY_v1.csv")}
    pages = {r["page_id"]: r for r in rows("data/canonical/CEW_PAGE_REGISTRY_v1.csv")}
    assets = {r["derived_asset_id"]: r for r in rows("data/canonical/CEW_DERIVED_ASSET_REGISTRY_v1.csv")}
    transforms = {r["transform_id"]: r for r in rows("data/canonical/CEW_COORDINATE_TRANSFORM_REGISTRY_v1.csv")}
    receipts = {r["evidence_region_id"]: r for r in rows("data/canonical/CEW_F2_LOCALIZATION_RECEIPT_v1.csv")}
    guards = {r["reference_item"]: r for r in rows("data/canonical/CEW_F2_BINDING_GUARD_v1.csv")}
    regions = rows("data/canonical/CEW_EVIDENCE_REGION_REGISTRY_v1.csv")
    observations = {r["reference_item"]: r for r in rows("data/canonical/CEW_OBSERVATION_REGISTRY_v1.csv")}

    if {r["reference_item"] for r in regions} != REFERENCE:
        raise AssertionError("reference region set mismatch")
    if set(observations) != REFERENCE:
        raise AssertionError("reference observation set mismatch")
    guard = guards.get("T6A-G03")
    if not guard or guard["structural_binding_state"] != "UNBOUND" or guard["applies_to_observation_field"].lower() != "false":
        raise AssertionError("T6A-G03 requires a separate UNBOUND structural binding guard")

    source_docs: dict[str, fitz.Document] = {}
    for source_id, src in sources.items():
        if src["readiness_state"] != "READY":
            continue
        payload = materialize(src["storage_locator"])
        if hashlib.sha256(payload).hexdigest() != src["sha256"]:
            raise AssertionError(f"source digest mismatch: {source_id}")
        source_docs[source_id] = fitz.open(stream=payload, filetype="pdf")

    for page_id, page in pages.items():
        if page["readiness_state"] != "READY":
            raise AssertionError(f"reference page not READY: {page_id}")
        src_id = page["source_version_id"]
        if src_id not in source_docs:
            raise AssertionError(f"READY page source not materialized: {page_id}")
        doc = source_docs[src_id]
        index = int(page["page_index"])
        if index < 0 or index >= doc.page_count:
            raise AssertionError(f"invalid page index: {page_id}")
        p = doc[index]
        sw, sh = float(page["source_width"]), float(page["source_height"])
        if not close(p.rect.width, sw, 1e-3) or not close(p.rect.height, sh, 1e-3):
            raise AssertionError(f"page dimensions not reproducible: {page_id}")

    for asset_id, asset in assets.items():
        if asset["authority_state"] != "DERIVED_REVIEW_AID_ONLY":
            raise AssertionError(f"derived asset authority violation: {asset_id}")
        if asset["reproducibility_state"] != "REPRODUCIBLE_FROM_IMMUTABLE_SOURCE":
            raise AssertionError(f"derived asset not reproducible: {asset_id}")
        if int(asset["dpi"]) < 300:
            raise AssertionError(f"technical reading asset below 300 dpi: {asset_id}")
        page = pages[asset["page_id"]]
        doc = source_docs[asset["source_version_id"]]
        pix = doc[int(page["page_index"])].get_pixmap(matrix=fitz.Matrix(int(asset["dpi"]) / 72.0, int(asset["dpi"]) / 72.0), alpha=False)
        if pix.width != int(asset["width_px"]) or pix.height != int(asset["height_px"]):
            raise AssertionError(f"derived render dimensions not reproducible: {asset_id}")

    ready = set()
    for region in regions:
        ref = region["reference_item"]
        rid = region["evidence_region_id"]
        if region["readiness_state"] != "READY":
            raise AssertionError(f"reference region not READY: {rid}")
        if region["coordinate_space"] != "NORMALIZED_0_1" or region["geometry_type"] != "BBOX":
            raise AssertionError(f"reference region must be normalized BBOX: {rid}")
        if not region["derived_asset_id"] or not region["transform_id"]:
            raise AssertionError(f"READY region missing asset/transform: {rid}")
        page = pages[region["page_id"]]
        asset = assets[region["derived_asset_id"]]
        tr = transforms[region["transform_id"]]
        receipt = receipts.get(rid)
        if receipt is None or receipt["adjudication_state"] != "ACCEPTED":
            raise AssertionError(f"READY region lacks accepted localization receipt: {rid}")
        if tr["page_id"] != region["page_id"] or tr["derived_asset_id"] != region["derived_asset_id"]:
            raise AssertionError(f"transform parent mismatch: {rid}")
        if asset["page_id"] != region["page_id"] or asset["source_version_id"] != region["source_version_id"]:
            raise AssertionError(f"derived asset parent mismatch: {rid}")
        if receipt["page_id"] != region["page_id"] or receipt["derived_asset_id"] != region["derived_asset_id"] or receipt["transform_id"] != region["transform_id"]:
            raise AssertionError(f"localization receipt parent mismatch: {rid}")

        x, y, w, h = [float(region[k]) for k in ("x", "y", "width", "height")]
        if not (0 <= x <= 1 and 0 <= y <= 1 and w > 0 and h > 0 and x + w <= 1 + TOL and y + h <= 1 + TOL):
            raise AssertionError(f"invalid normalized bbox: {rid}")
        for k, value in (("x", x), ("y", y), ("width", w), ("height", h)):
            if not close(float(receipt[k]), value):
                raise AssertionError(f"receipt coordinate drift {rid}:{k}")

        sw, sh = float(page["source_width"]), float(page["source_height"])
        pw, ph = float(asset["width_px"]), float(asset["height_px"])
        if not close(float(tr["source_scale_x"]), sw) or not close(float(tr["source_scale_y"]), sh):
            raise AssertionError(f"source transform scale mismatch: {rid}")
        if not close(float(tr["pixel_scale_x"]), pw) or not close(float(tr["pixel_scale_y"]), ph):
            raise AssertionError(f"pixel transform scale mismatch: {rid}")
        if tr["viewer_space"] != "VIEWER_NORMALIZED_0_1" or not close(float(tr["viewer_scale_x"]), 1.0) or not close(float(tr["viewer_scale_y"]), 1.0):
            raise AssertionError(f"viewer transform must be normalized identity: {rid}")

        pdf_bbox = (x * sw, y * sh, (x + w) * sw, (y + h) * sh)
        px_bbox = (x * pw, y * ph, (x + w) * pw, (y + h) * ph)
        if not all(math.isfinite(v) for v in pdf_bbox + px_bbox):
            raise AssertionError(f"non-finite reconstructed bbox: {rid}")
        if pdf_bbox[0] < -TOL or pdf_bbox[1] < -TOL or pdf_bbox[2] > sw + TOL or pdf_bbox[3] > sh + TOL:
            raise AssertionError(f"PDF bbox outside page: {rid}")
        if px_bbox[0] < -TOL or px_bbox[1] < -TOL or px_bbox[2] > pw + TOL or px_bbox[3] > ph + TOL:
            raise AssertionError(f"pixel bbox outside derived asset: {rid}")
        roundtrip = (pdf_bbox[0] / sw, pdf_bbox[1] / sh, (pdf_bbox[2] - pdf_bbox[0]) / sw, (pdf_bbox[3] - pdf_bbox[1]) / sh)
        if any(not close(a, b, 1e-9) for a, b in zip(roundtrip, (x, y, w, h))):
            raise AssertionError(f"normalized/PDF round-trip failed: {rid}")

        obs = observations[ref]
        if obs["source_version_id"] != region["source_version_id"] or obs["evidence_region_id"] != rid:
            raise AssertionError(f"Observation -> EvidenceRegion link mismatch: {ref}")
        if obs["reading_state"] not in FINAL_STATES:
            raise AssertionError(f"observation not finalized: {ref}")
        if obs["structural_binding"]:
            raise AssertionError(f"Observation must not carry structural binding: {ref}")
        ready.add(ref)

    if ready != REFERENCE:
        raise AssertionError("not all reference chains are reproducible")

    print("CEW F2 REPRODUCIBLE EVIDENCE CHAINS = 4/4")
    print("EVIDENCE_PROVENANCE_PASS")
    print("T6A-G03 STRUCTURAL_BINDING_GUARD = UNBOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
