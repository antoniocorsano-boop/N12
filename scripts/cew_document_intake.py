#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_INDEX = ROOT / "data/canonical/tavole_originali_remote_index_v1.csv"
MODEL = ROOT / "automation/CEW_DOCUMENT_INTAKE_MODEL_v1.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_METADATA_SIZE = 2 * 1024 * 1024 * 1024


def rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sources() -> dict[str, dict]:
    return {row["id"]: row for row in rows(SOURCE_INDEX)}


def normalize_sha256(value: str) -> str:
    digest = (value or "").strip().lower()
    if not SHA256_RE.fullmatch(digest):
        raise ValueError("INVALID_SHA256")
    return digest


def analyze_metadata(payload: dict) -> dict:
    filename = str(payload.get("filename") or "").strip()
    mime_type = str(payload.get("mime_type") or "").strip()[:200]
    selected_source_id = str(payload.get("selected_source_id") or "").strip()
    try:
        size_bytes = int(payload.get("size_bytes"))
    except (TypeError, ValueError):
        raise ValueError("INVALID_SIZE_BYTES")
    if not filename:
        raise ValueError("FILENAME_REQUIRED")
    if size_bytes < 0 or size_bytes > MAX_METADATA_SIZE:
        raise ValueError("SIZE_OUT_OF_POLICY")
    digest = normalize_sha256(str(payload.get("sha256") or ""))

    registry = sources()
    matches = [row for row in registry.values() if row.get("sha256", "").strip().lower() == digest]
    if matches:
        row = matches[0]
        return {
            "state": "EXACT_DUPLICATE",
            "filename": filename,
            "size_bytes": size_bytes,
            "mime_type": mime_type,
            "sha256": digest,
            "matching_source_id": row["id"],
            "matching_source_status": row["status"],
            "selected_source_id": selected_source_id or None,
            "bytes_uploaded": False,
            "canonical_write_authorized": False,
            "next_action": "USE_EXISTING_SOURCE_VERSION",
            "reason_codes": ["EXACT_SHA256_MATCH"],
        }

    if selected_source_id:
        if selected_source_id not in registry:
            raise ValueError("SELECTED_SOURCE_NOT_REGISTERED")
        return {
            "state": "NEW_VERSION_CANDIDATE",
            "filename": filename,
            "size_bytes": size_bytes,
            "mime_type": mime_type,
            "sha256": digest,
            "selected_source_id": selected_source_id,
            "bytes_uploaded": False,
            "canonical_write_authorized": False,
            "next_action": "HUMAN_CONFIRM_VERSION_RELATION_AND_CLASSIFICATION",
            "reason_codes": ["EXPLICIT_EXISTING_SOURCE_SELECTED", "SHA256_DIFFERS_FROM_REGISTERED_VERSIONS"],
        }

    same_filename = [row["id"] for row in registry.values() if row.get("canonical_filename", "").casefold() == filename.casefold()]
    return {
        "state": "SOURCE_DECISION_REQUIRED",
        "filename": filename,
        "size_bytes": size_bytes,
        "mime_type": mime_type,
        "sha256": digest,
        "selected_source_id": None,
        "filename_similarity_hints": same_filename,
        "filename_hint_is_binding": False,
        "bytes_uploaded": False,
        "canonical_write_authorized": False,
        "next_action": "HUMAN_CHOOSE_NEW_SOURCE_OR_EXISTING_SOURCE_VERSION",
        "reason_codes": ["NO_EXACT_SHA256_MATCH", "SOURCE_RELATION_NOT_AUTHORIZED"],
    }


def esc(value) -> str:
    return html.escape(str(value or ""))


def build_intake_page() -> str:
    options = "".join(
        f"<option value='{esc(source_id)}'>{esc(source_id)} · {esc(row.get('classe','').replace('_',' '))} · {esc(row.get('livello_uso','').replace('_',' '))}</option>"
        for source_id, row in sorted(sources().items())
    )
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW — Acquisisci documento</title>
<style>
:root{{--ink:#17202a;--muted:#65717e;--line:#d8dde3;--bg:#f4f6f8;--accent:#173f5f;--warn:#8a4b08}}*{{box-sizing:border-box}}body{{margin:0;font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink)}}a{{color:var(--accent)}}header{{background:#fff;border-bottom:1px solid var(--line)}}.top{{max-width:980px;margin:auto;padding:20px 24px;display:flex;gap:14px}}.brand{{font-size:11px;font-weight:850;letter-spacing:.08em;color:var(--accent)}}h1{{margin:4px 0}}main{{max-width:980px;margin:auto;padding:22px 24px 50px}}.panel{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:14px}}label{{display:grid;gap:5px;margin:12px 0;font-weight:700}}input,select,button{{font:inherit;padding:10px;border:1px solid #bcc6cf;border-radius:7px}}button{{background:var(--accent);color:#fff;font-weight:800;cursor:pointer}}button:disabled{{opacity:.5;cursor:not-allowed}}.muted{{color:var(--muted);line-height:1.5}}.notice{{border-left:5px solid var(--accent)}}.warning{{border-left:5px solid var(--warn)}}#result{{white-space:pre-wrap;background:#f7f9fa;border-radius:8px;padding:12px;min-height:52px}}.row{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}@media(max-width:700px){{.row{{grid-template-columns:1fr}}}}
</style></head><body><header><div class="top"><a href="/documents">← Documenti</a><div><div class="brand">CEW · DOCUMENT INTAKE B1.4 PREPARATION</div><h1>Acquisisci un documento</h1><p class="muted">Prima controlliamo identità e versione. I byte restano sul dispositivo finché non esiste uno storage privato autorizzato.</p></div></div></header><main>
<section class="panel notice"><b>Privacy by design.</b> CEW calcola SHA-256 nel browser. In questa fase invia al server solo nome, dimensione, MIME e hash. Il file non viene caricato.</section>
<section class="panel"><h2>1. Seleziona il file</h2><input id="file" type="file"><p id="hashState" class="muted">Nessun file selezionato.</p><div class="row"><label>Relazione con una fonte esistente (opzionale)<select id="source"><option value="">Non so / nuovo documento</option>{options}</select></label><label>Tipo MIME rilevato<input id="mime" readonly></label></div><button id="analyze" disabled>Analizza identità e versione</button></section>
<section class="panel"><h2>2. Esito</h2><div id="result">Seleziona un file per iniziare.</div></section>
<section class="panel warning"><h2>3. Storage</h2><p class="muted"><b>Non ancora autorizzato in B1.4 preparation.</b> Anche se l’analisi identifica un nuovo documento o una nuova versione, CEW non dichiara l’ingestione completata e non crea una SourceVersion finché i byte non sono archiviati privatamente e l’hash memorizzato non viene riverificato.</p></section>
<script>
let digest='';let fileMeta=null;const f=document.getElementById('file'),a=document.getElementById('analyze'),hs=document.getElementById('hashState'),r=document.getElementById('result'),mime=document.getElementById('mime');
function hex(buf){{return [...new Uint8Array(buf)].map(b=>b.toString(16).padStart(2,'0')).join('')}}
f.addEventListener('change',async()=>{{digest='';a.disabled=true;const file=f.files[0];if(!file){{hs.textContent='Nessun file selezionato.';return}}mime.value=file.type||'';hs.textContent='Calcolo SHA-256 locale…';const data=await file.arrayBuffer();digest=hex(await crypto.subtle.digest('SHA-256',data));fileMeta={{filename:file.name,size_bytes:file.size,mime_type:file.type||'',sha256:digest}};hs.textContent=`SHA-256 pronto: ${{digest.slice(0,16)}}… · ${{file.size}} byte · nessun byte inviato`;a.disabled=false;}});
a.addEventListener('click',async()=>{{if(!fileMeta)return;a.disabled=true;r.textContent='Analisi…';const payload={{...fileMeta,selected_source_id:document.getElementById('source').value}};try{{const res=await fetch('/api/intake/analyze',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});const out=await res.json();r.textContent=JSON.stringify(out,null,2)}}catch(e){{r.textContent='Analisi non disponibile: '+e}}finally{{a.disabled=false}}}});
</script></main></body></html>'''
