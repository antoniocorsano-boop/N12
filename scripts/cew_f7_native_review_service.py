#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_cew_canonical_patch_candidates as patch_builder
import build_cew_f7_promotion_requests as receipt_bridge
import cew_project_control_room as control_room
import run_cew_promotion_engine as promotion_engine

STATE = ROOT / "data/canonical/CEW_PROJECT_STATE_CURRENT_v1.json"
ISSUES = ROOT / "data/canonical/N12_ISSUES_CURRENT_v1.json"
TASKS = ROOT / "data/canonical/CEW_ERW_RESOLUTION_TASKS_v1.csv"
VIEWER_BINDINGS = ROOT / "data/canonical/CEW_SOURCE_VIEWER_BINDINGS_v1.csv"
TARGETS = ROOT / "data/canonical/CEW_PROMOTION_TARGET_REGISTRY_v1.csv"
RECEIPT_SCHEMA = ROOT / "automation/CEW_HUMAN_DECISION_RECEIPT_SCHEMA_v1.json"
SERVICE_CONTRACT = ROOT / "automation/CEW_F7_NATIVE_REVIEW_SERVICE_CONTRACT_v1.json"
DEFAULT_STORE = ROOT / "artifacts/cew-runtime/human-receipts"
SAFE_DECISION_ID = re.compile(r"^[A-Za-z0-9._-]+$")
MAX_BODY = 64 * 1024


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def maps():
    tasks = {r["task_id"].strip(): r for r in rows(TASKS)}
    bindings = {r["task_id"].strip(): r for r in rows(VIEWER_BINDINGS)}
    targets = {r["target_id"].strip(): r for r in rows(TARGETS)}
    return tasks, bindings, targets


def ensure_runtime_store(path: Path) -> Path:
    resolved = path.resolve()
    protected = [
        (ROOT / "data/canonical").resolve(),
        (ROOT / "knowledge").resolve(),
        (ROOT / "automation/receipts").resolve(),
        (ROOT / "automation/inbox").resolve(),
    ]
    for base in protected:
        if resolved == base or base in resolved.parents:
            raise ValueError(f"runtime receipt store cannot be inside protected path: {base}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def persist_runtime_receipt(receipt: dict, store: Path) -> dict:
    decision_id = str(receipt["decision_id"])
    if not SAFE_DECISION_ID.fullmatch(decision_id):
        raise ValueError("decision_id contains unsafe filename characters")
    target = store / f"{decision_id}.json"
    raw = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    try:
        with target.open("x", encoding="utf-8") as f:
            f.write(raw)
    except FileExistsError as e:
        raise ValueError("duplicate decision_id: runtime receipt already exists") from e
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return {
        "runtime_receipt_id": decision_id,
        "sha256": digest,
        "authority": "RUNTIME_AUDIT_ONLY",
        "canonical_write": False,
    }


def process_receipt(receipt: dict, receipt_store: Path) -> dict:
    schema = load_json(RECEIPT_SCHEMA)
    contract = load_json(SERVICE_CONTRACT)
    if contract.get("authority_invariants", {}).get("service_may_write_canonical_directly") is not False:
        raise AssertionError("native review service authority contract drift")

    required = set(schema["required_fields"])
    supplied = set(receipt)
    extra = sorted(supplied - required)
    missing = sorted(required - supplied)
    if extra or missing:
        return {
            "state": "RECEIPT_REJECTED",
            "reason_codes": (["MISSING_REQUIRED_FIELDS"] if missing else []) + (["UNEXPECTED_FIELDS_FORBIDDEN"] if extra else []),
            "missing_fields": missing,
            "unexpected_fields": extra,
            "canonical_write_performed": False,
        }

    if any(k in receipt for k in ("fixture_only", "fixture_id", "source_authority", "canonical_write_authorized")):
        return {
            "state": "RECEIPT_REJECTED",
            "reason_codes": ["INTERACTIVE_FIXTURE_OR_AUTHORITY_FIELDS_FORBIDDEN"],
            "canonical_write_performed": False,
        }

    task_map, _, target_map = maps()
    try:
        request = receipt_bridge.normalize_receipt(receipt, task_map)
    except SystemExit as e:
        return {
            "state": "RECEIPT_REJECTED",
            "reason_codes": ["HUMAN_RECEIPT_VALIDATOR_REJECTED"],
            "detail": str(e),
            "canonical_write_performed": False,
        }
    except (AssertionError, KeyError, ValueError) as e:
        return {
            "state": "RECEIPT_REJECTED",
            "reason_codes": ["HUMAN_RECEIPT_BRIDGE_REJECTED"],
            "detail": str(e),
            "canonical_write_performed": False,
        }

    try:
        audit = persist_runtime_receipt(receipt, receipt_store)
    except ValueError as e:
        return {
            "state": "RECEIPT_REJECTED",
            "reason_codes": ["RUNTIME_AUDIT_PERSISTENCE_REJECTED"],
            "detail": str(e),
            "canonical_write_performed": False,
        }

    evaluation = promotion_engine.evaluate_with_context(request, target_map)
    if evaluation.get("terminal_action") != "EMIT_CANONICAL_PATCH_CANDIDATE":
        return {
            "state": "RETAIN_RESIDUAL",
            "receipt": audit,
            "evaluation": evaluation,
            "canonical_write_authorized": False,
            "canonical_write_performed": False,
        }

    target = target_map.get(evaluation.get("target_id") or "")
    if target is None:
        return {
            "state": "SEMANTIC_BLOCKED",
            "receipt": audit,
            "evaluation": evaluation,
            "reason_codes": ["SEMANTIC_REGISTERED_TARGET_REQUIRED"],
            "canonical_write_authorized": False,
            "canonical_write_performed": False,
        }

    semantic_payload, reason = patch_builder.semantic_payload_for(evaluation, target)
    if semantic_payload is None:
        return {
            "state": "SEMANTIC_BLOCKED",
            "receipt": audit,
            "evaluation": evaluation,
            "reason_codes": [reason],
            "raw_human_observation": evaluation.get("human_observation"),
            "canonical_write_authorized": False,
            "canonical_write_performed": False,
        }

    payload = {
        "decision_id": evaluation["decision_id"],
        "task_id": evaluation.get("task_id"),
        "residual_id": evaluation.get("residual_id"),
        "target_id": evaluation["target_id"],
        "target_class": target["target_class"],
        "canonical_locator": target["canonical_locator"],
        "operation": target["allowed_operations"],
        "requested_epistemic_state": evaluation["requested_epistemic_state"],
        "source_authority": "VALIDATED_HUMAN_DIRECT_PRIMARY",
        "evidence_regions": evaluation.get("evidence_regions", []),
        "source_versions": evaluation.get("source_versions", []),
        "semantic_payload": semantic_payload,
        "canonical_write_authorized": False,
        "canonical_write_performed": False,
    }
    candidate = {"patch_candidate_id": "CEW-PATCH-CAND-" + patch_builder.stable_id(payload), **payload}
    return {
        "state": "PATCH_CANDIDATE_READY_NO_WRITE",
        "receipt": audit,
        "evaluation": evaluation,
        "patch_candidate": candidate,
        "canonical_write_authorized": False,
        "canonical_write_performed": False,
    }


def render_review(task_id: str) -> str:
    tasks, bindings, targets = maps()
    if task_id not in tasks or task_id not in bindings:
        return "<!doctype html><html><body><h1>Task F7 non trovato</h1><a href='/'>Torna al Control Room</a></body></html>"
    task = tasks[task_id]
    binding = bindings[task_id]
    schema = load_json(RECEIPT_SCHEMA)
    active_targets = [t for t in targets.values() if t.get("status") == "ACTIVE"]
    target_options = "".join(
        f"<option value='{html.escape(t['target_id'])}'>{html.escape(t['target_id'])} — {html.escape(t['target_class'])}</option>"
        for t in active_targets
    )
    outcomes = "".join(f"<option value='{html.escape(x)}'>{html.escape(x)}</option>" for x in schema["allowed_outcomes"])
    states = "".join(f"<option value='{html.escape(x)}'>{html.escape(x)}</option>" for x in schema["allowed_requested_states"])
    task_json = json.dumps({
        "task_id": task_id,
        "residual_id": task["residual_id"],
        "evidence_regions": [binding["evidence_region_id"]],
        "source_versions": [binding["source_version_id"]],
        "ack": schema["authority_acknowledgement_exact"],
    }, ensure_ascii=False)
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW F7 — {html.escape(task_id)}</title>
<style>body{{font-family:system-ui;margin:0;background:#f5f6f8;color:#18212b}}header,main{{max-width:1100px;margin:auto;padding:20px}}section{{background:white;border:1px solid #d7dbe1;border-radius:10px;padding:18px;margin:14px 0}}label{{display:block;font-weight:650;margin-top:12px}}input,select,textarea{{width:100%;box-sizing:border-box;padding:9px;margin-top:4px}}textarea{{min-height:100px}}.check{{display:flex;gap:8px;align-items:flex-start;font-weight:500}}.check input{{width:auto}}button{{margin-top:16px;padding:10px 16px}}pre{{white-space:pre-wrap;background:#111827;color:#eef2ff;padding:14px;border-radius:8px}}.authority{{border-left:5px solid #365f91}}.known{{border-left:5px solid #3b7a57}}</style></head><body><header><a href="/">← Control Room</a><h1>Revisione evidenza F7 — {html.escape(task_id)}</h1><p>{html.escape(task['question'])}</p></header><main>
<section class="known"><b>Residuo:</b> {html.escape(task['residual_id'])}<br><b>Fonte:</b> {html.escape(task['source_id'])} · {html.escape(task['source_locator'])}<br><b>Già noto:</b> {html.escape(task['known_claims'])}<br><b>Da completare:</b> {html.escape(task['unknown_claims'])}<br><b>EvidenceRegion:</b> {html.escape(binding['evidence_region_id'])}<br><b>SourceVersion:</b> {html.escape(binding['source_version_id'])}</section>
<section class="authority"><b>Autorità:</b> i campi umani partono vuoti. Il submit crea una receipt di audit e può produrre un patch candidate, ma non scrive dati canonici. Se hai già effettuato la lettura, puoi ripetere qui la stessa osservazione senza doverla ricavare di nuovo.</section>
<section><label>Revisore<input id="reviewer" autocomplete="name"></label><label>Esito<select id="outcome"><option value="">— scegli —</option>{outcomes}</select></label><label>Osservazione umana<textarea id="observation" placeholder="Trascrivi personalmente ciò che hai osservato sulla fonte primaria."></textarea></label><label class="check"><input type="checkbox" id="direct">Ho verificato direttamente la fonte primaria.</label><label>Stato epistemico richiesto<select id="epistemic"><option value="">— scegli —</option>{states}</select></label><label>Target di promozione<select id="target"><option value="">— nessun target selezionato —</option>{target_options}</select></label><label>ID approvazione riapertura (solo se richiesto)<input id="reopen"></label><label class="check"><input type="checkbox" id="ack">Confermo che questa è una mia revisione della fonte primaria e che la receipt non è una scrittura canonica.</label><button id="submit">Invia a CEW</button></section>
<section><h2>Esito CEW</h2><pre id="result">Nessuna receipt inviata.</pre></section></main><script>
const META={task_json};
function val(id){{return document.getElementById(id).value.trim()}}
document.getElementById('submit').onclick=async()=>{{
 const outcome=val('outcome'),target=val('target'),state=val('epistemic');
 const receipt={{schema_version:'1.0',decision_id:`HUMAN-${{META.task_id}}-${{Date.now()}}`,task_id:META.task_id,residual_id:META.residual_id,review_mode:'HUMAN_REVIEW',reviewer:val('reviewer'),timestamp:new Date().toISOString(),outcome,human_observation:val('observation'),evidence_regions:META.evidence_regions,source_versions:META.source_versions,direct_primary_evidence_observed:document.getElementById('direct').checked,requested_epistemic_state:state,target_id:target,reopen_approval_id:val('reopen'),authority_acknowledgement:document.getElementById('ack').checked?META.ack:''}};
 const box=document.getElementById('result');
 if(!receipt.reviewer||!outcome||!state||!document.getElementById('ack').checked){{box.textContent='Compila Revisore, Esito, Stato epistemico e attestazione finale.';return;}}
 if(outcome==='CONFIRMED'&&(!receipt.human_observation||!receipt.direct_primary_evidence_observed||!target)){{box.textContent='CONFERMATO richiede osservazione, verifica diretta e target selezionato.';return;}}
 if(outcome!=='CONFIRMED'&&target){{box.textContent='Un esito non promotivo non può selezionare un target.';return;}}
 box.textContent='Validazione CEW in corso…';
 try{{const r=await fetch('/api/f7/receipt',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(receipt)}});const data=await r.json();box.textContent=JSON.stringify(data,null,2);}}catch(e){{box.textContent='Errore di comunicazione con CEW: '+e;}}
}};
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    state = load_json(STATE)
    issues = load_json(ISSUES)
    task_rows = rows(TASKS)
    receipt_store = DEFAULT_STORE

    def log_message(self, fmt, *args):
        sys.stderr.write("CEW_HTTP " + (fmt % args) + "\n")

    def send_html(self, body: str, status=HTTPStatus.OK):
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_json(self, obj: dict, status=HTTPStatus.OK):
        raw = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_html(control_room.build(self.state, self.issues, self.task_rows))
            return
        if parsed.path == "/review/f7":
            task_id = parse_qs(parsed.query).get("task", [""])[0]
            self.send_html(render_review(task_id))
            return
        if parsed.path == "/healthz":
            self.send_json({"status": "ok", "service": "CEW-F7-NATIVE-REVIEW", "canonical_write": False})
            return
        self.send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/f7/receipt":
            self.send_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json({"state": "RECEIPT_REJECTED", "reason_codes": ["INVALID_CONTENT_LENGTH"]}, HTTPStatus.BAD_REQUEST)
            return
        if length <= 0 or length > MAX_BODY:
            self.send_json({"state": "RECEIPT_REJECTED", "reason_codes": ["INVALID_BODY_SIZE"]}, HTTPStatus.BAD_REQUEST)
            return
        try:
            receipt = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(receipt, dict):
                raise ValueError("receipt must be a JSON object")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
            self.send_json({"state": "RECEIPT_REJECTED", "reason_codes": ["INVALID_JSON"], "detail": str(e)}, HTTPStatus.BAD_REQUEST)
            return
        result = process_receipt(receipt, self.receipt_store)
        status = HTTPStatus.OK if result["state"] != "RECEIPT_REJECTED" else HTTPStatus.UNPROCESSABLE_ENTITY
        self.send_json(result, status)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--receipt-store", type=Path, default=DEFAULT_STORE)
    args = ap.parse_args()
    contract = load_json(SERVICE_CONTRACT)
    if contract.get("product_surface") != "PROJECT_CONTROL_ROOM":
        raise SystemExit("FAIL: native review service contract drift")
    Handler.receipt_store = ensure_runtime_store(args.receipt_store)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"CEW NATIVE CONTROL ROOM: http://{args.host}:{args.port}/")
    print("F7_RECEIPT_SUBMIT=NATIVE")
    print("CANONICAL_WRITE=FORBIDDEN")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
