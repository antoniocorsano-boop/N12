#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import build_cew_source_viewer as base

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data" / "canonical" / "CEW_SOURCE_IDENTITY_REGISTRY_v1.csv"

EXTRA_CONTEXT = {
    "TAV-04": "tiles/TAV-04.dzi",
    "TAV-06E": "tiles/TAV-06E.dzi",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    manifest = base.build_manifest()
    source_rows = rows(SOURCES)
    existing = {x["source_code"] for x in manifest.get("context_sources", [])}

    for code, dzi in EXTRA_CONTEXT.items():
        if code in existing:
            continue
        candidates = [
            r for r in source_rows
            if r["logical_source_code"].strip() == code
            and r["readiness_state"].strip() == "READY"
        ]
        if len(candidates) != 1:
            raise AssertionError(f"expected exactly one READY context source for {code}")
        r = candidates[0]
        manifest["context_sources"].append({
            "source_code": code,
            "source_version_id": r["source_version_id"].strip(),
            "source_sha256": r["sha256"].strip(),
            "document_role": r["document_role"].strip(),
            "dzi": dzi,
            "context_only": True,
            "authority_note": (
                "Fonte primaria di contesto per la localizzazione umana del torrino scale. "
                "Non crea automaticamente EvidenceRegion, binding strutturali, coordinate o decisioni canoniche."
            ),
        })

    manifest["geometry_banner"] = (
        "LE REGIONI F2 ESISTENTI SONO IN SOLA LETTURA — TAV-04, TAV-05S, TAV-06S E TAV-06E "
        "SONO MOSTRATE SOLO COME CONTESTO PER LA LOCALIZZAZIONE UMANA DEL TORRINO/SCALA"
    )

    (out / "viewer_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out / "index.html").write_text(base.HTML, encoding="utf-8")
    (out / "styles.css").write_text(base.CSS, encoding="utf-8")
    (out / "app.js").write_text(base.JS, encoding="utf-8")

    print(f"SOURCE_VIEWER_MANIFEST_ENTRIES={len(manifest['entries'])}")
    print(f"SOURCE_VIEWER_CONTEXT_SOURCES={len(manifest['context_sources'])}")
    for e in manifest["context_sources"]:
        print(f"VIEWER_CONTEXT={e['source_code']}->{e['source_version_id']}->{e['dzi']}")
    print("TORRINO_CONTEXT=TAV-04,TAV-06E")
    print("CANONICAL_WRITE=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
