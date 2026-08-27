#!/usr/bin/env python3
from __future__ import annotations

import hashlib, hmac, html, json, os, re, time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

app = FastAPI(title="CEW Project Control Room", docs_url=None, redoc_url=None)
COOKIE="cew_session"
PURPOSE=b"CEW_SINGLE_OPERATOR_PILOT_V1"
ACK="I reviewed the cited immutable primary-source evidence and understand this receipt is not itself a canonical write."
ALLOWED_OUTCOMES=["CONFIRMED","REJECTED","UNREADABLE","UNBOUND","NEEDS_BETTER_SOURCE","NEEDS_SITE_SURVEY","DEFER"]
ALLOWED_STATES=["ND","INF","RIF","MIS","DOC"]
TARGET="CEW-TARGET-REINFORCEMENT-OBSERVATION"
TASKS={
"ERW-N12-001":dict(residual_id="M1E-B06-R08",question="Determine quantity and diameter for TAV-05A record G01-R06 without analogy.",source="TAV-05A · T5A-G01/G01-R06",known="length=1040 DOC",unknown="quantity ND; diameter ND",ceiling="DOC",evidence_region="CEW-N12-REG-G01-R06",source_version="CEW-N12-SRC-TAV05A-V17DEC414"),
"ERW-N12-002":dict(residual_id="M1E-B06-R09",question="Determine quantity and diameter for TAV-05A record G07-R07 without analogy.",source="TAV-05A · T5A-G07/G07-R07",known="length=865 DOC",unknown="quantity ND; diameter ND",ceiling="DOC",evidence_region="CEW-N12-REG-G07-R07",source_version="CEW-N12-SRC-TAV05A-V17DEC414"),
"ERW-N12-003":dict(residual_id="M1E-B06-R10",question="Resolve missing dimensions of the directly visible intermediate sagomato continuation G05-R04.",source="TAV-05A · T5A-G05/G05-R04",known="intermediate sagomato continuation DOC_DIRECT_PARTIAL",unknown="missing dimensions ND",ceiling="DOC",evidence_region="CEW-N12-REG-G05-R04",source_version="CEW-N12-SRC-TAV05A-V17DEC414"),
"ERW-N12-004":dict(residual_id="M1E-B06-R11",question="Adjudicate whether any direct primary evidence can bind T6A-G03 to G5-B017 or another canonical member.",source="TAV-06A · T6A-G03",known="G5-B017 endpoints 12-19 DOC; T6A-G03 source scheme DOC",unknown="member-specific reinforcement ND; direct source binding ND",ceiling="INF",evidence_region="CEW-N12-REG-T6A-G03",source_version="CEW-N12-SRC-TAV06A-V3F2D557F")}
REQ={"schema_version","decision_id","task_id","residual_id","review_mode","reviewer","timestamp","outcome","human_observation","evidence_regions","source_versions","direct_primary_evidence_observed","requested_epistemic_state","target_id","reopen_approval_id","authority_acknowledgement"}
DIR_RE=re.compile(r"(\d+)\s*(?:[ΦØ]|[fF]|phi)\s*(\d+)\s+superiori\s*(?:\+|e)\s*(\d+)\s*(?:[ΦØ]|[fF]|phi)\s*(\d+)\s+inferiori",re.I)

def auth_ready(): return bool(os.getenv("CEW_ACCESS_PASSWORD")) and bool(os.getenv("CEW_SESSION_SECRET"))
def audit_ready(): return bool(os.getenv("CEW_AUDIT_NEON_DATABASE_URL"))
def session_value(): return hmac.new(os.environ.get("CEW_SESSION_SECRET","").encode(),PURPOSE,hashlib.sha256).hexdigest()
def authorized(req): return auth_ready() and hmac.compare_digest(req.cookies.get(COOKIE,""),session_value())

@app.middleware("http")
async def guard(req, call_next):
    if req.url.path in {"/login","/healthz"}: return await call_next(req)
    if not authorized(req): return RedirectResponse("/login",303)
    return await call_next(req)

@app.get("/healthz")
def healthz():
    return {"service":"CEW_USER_RUNTIME","status":"OK" if auth_ready() and audit_ready() else "CONFIG_REQUIRED","auth_configured":auth_ready(),"audit_backend":"NEON_APPEND_ONLY" if audit_ready() else "UNCONFIGURED_PRODUCTION","production_receipt_submit_ready":audit_ready(),"canonical_write_authorized":False}

@app.get("/login",response_class=HTMLResponse)
def login_get():
    return HTMLResponse("""<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'><body style='font-family:system-ui;background:#f4f6f8'><main style='max-width:420px;margin:12vh auto;background:white;padding:28px;border-radius:12px'><h1>CEW</h1><p>Project Control Room</p><form method='post'><input name='password' type='password' placeholder='Password operatore' style='width:100%;padding:10px;box-sizing:border-box'><button style='margin-top:12px;padding:10px;width:100%'>Accedi</button></form></main></body></html>""")

@app.post("/login")
async def login_post(req:Request):
    from urllib.parse import parse_qs
    supplied=parse_qs((await req.body()).decode()).get("password",[""])[0]
    if not auth_ready(): return HTMLResponse("CEW non configurato",503)
    if not hmac.compare_digest(supplied,os.environ["CEW_ACCESS_PASSWORD"]): return HTMLResponse("Password non valida",401)
    r=RedirectResponse("/",303); r.set_cookie(COOKIE,session_value(),httponly=True,secure=True,samesite="lax",max_age=43200); return r

@app.post("/logout")
def logout():
    r=RedirectResponse("/login",303); r.delete_cookie(COOKIE); return r

@app.get("/",response_class=HTMLResponse)
def home():
    cards="".join(f"<a href='/review/f7?task={k}' style='display:block;padding:14px;margin:10px 0;background:white;border:1px solid #ddd;border-radius:9px;text-decoration:none;color:#17202a'><b>{k}</b> · {html.escape(v['residual_id'])}<br><small>{html.escape(v['question'])}</small></a>" for k,v in TASKS.items())
    return HTMLResponse(f"<!doctype html><html><meta name='viewport' content='width=device-width,initial-scale=1'><body style='font-family:system-ui;background:#f4f6f8;color:#17202a'><main style='max-width:900px;margin:auto;padding:24px'><h1>CEW Project Control Room</h1><p>Revisione umana evidenze F7 · HUMAN REVIEW — NO CANONICAL WRITE</p>{cards}<form method='post' action='/logout'><button>Esci</button></form></main></body></html>")

@app.get("/review/f7",response_class=HTMLResponse)
def review(task:str=""):
    t=TASKS.get(task)
    if not t: return HTMLResponse("Task non trovato",404)
    outcomes="".join(f"<option>{x}</option>" for x in ALLOWED_OUTCOMES); states="".join(f"<option>{x}</option>" for x in ALLOWED_STATES)
    meta=json.dumps({"task_id":task,"residual_id":t['residual_id'],"evidence_region":t['evidence_region'],"source_version":t['source_version']})
    return HTMLResponse(f'''<!doctype html><html lang="it"><meta name="viewport" content="width=device-width,initial-scale=1"><body style="font-family:system-ui;background:#f5f6f8;color:#18212b"><main style="max-width:900px;margin:auto;padding:22px"><a href="/">← Control Room</a><h1>{task}</h1><p>{html.escape(t['question'])}</p><section style="background:white;padding:16px;border-radius:9px"><b>Fonte:</b> {html.escape(t['source'])}<br><b>Già noto:</b> {html.escape(t['known'])}<br><b>Da completare:</b> {html.escape(t['unknown'])}<br><b>EvidenceRegion:</b> {t['evidence_region']}<br><b>SourceVersion:</b> {t['source_version']}</section><section style="background:white;padding:16px;border-radius:9px;margin-top:12px"><label>Revisore<input id="reviewer" style="width:100%;padding:8px"></label><label>Esito<select id="outcome" style="width:100%;padding:8px"><option value="">—</option>{outcomes}</select></label><label>Osservazione<textarea id="obs" style="width:100%;min-height:100px"></textarea></label><label><input id="direct" type="checkbox"> Ho verificato direttamente la fonte primaria</label><label>Stato<select id="state"><option value="">—</option>{states}</select></label><label>Target<select id="target"><option value="">—</option><option value="{TARGET}">{TARGET}</option></select></label><label><input id="ack" type="checkbox"> Confermo la mia revisione e comprendo che non è una scrittura canonica</label><button id="send">Invia a CEW</button></section><pre id="result" style="white-space:pre-wrap;background:#111827;color:white;padding:14px;border-radius:9px">Nessuna receipt inviata.</pre></main><script>const M={meta};const v=id=>document.getElementById(id).value.trim();document.getElementById('send').onclick=async()=>{{const r={{schema_version:'1.0',decision_id:`HUMAN-${{M.task_id}}-${{Date.now()}}`,task_id:M.task_id,residual_id:M.residual_id,review_mode:'HUMAN_REVIEW',reviewer:v('reviewer'),timestamp:new Date().toISOString(),outcome:v('outcome'),human_observation:v('obs'),evidence_regions:[M.evidence_region],source_versions:[M.source_version],direct_primary_evidence_observed:document.getElementById('direct').checked,requested_epistemic_state:v('state'),target_id:v('target'),reopen_approval_id:'',authority_acknowledgement:document.getElementById('ack').checked?{json.dumps(ACK)}:''}};const out=document.getElementById('result');try{{const x=await fetch('/api/f7/receipt',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(r)}});out.textContent=JSON.stringify(await x.json(),null,2)}}catch(e){{out.textContent=String(e)}}}};</script></body></html>''')

def persist(receipt,digest):
    import psycopg
    try:
        with psycopg.connect(os.environ["CEW_AUDIT_NEON_DATABASE_URL"],connect_timeout=10) as c:
            with c.cursor() as cur:
                cur.execute("INSERT INTO public.cew_human_receipt_audit(decision_id,task_id,residual_id,receipt_sha256,receipt_json,authority,canonical_write,submitted_at) VALUES(%s,%s,%s,%s,%s::jsonb,'RUNTIME_AUDIT_ONLY',false,%s)",(receipt['decision_id'],receipt['task_id'],receipt['residual_id'],digest,json.dumps(receipt,ensure_ascii=False),receipt['timestamp']))
            c.commit()
    except psycopg.errors.UniqueViolation as e: raise ValueError("DUPLICATE_DECISION_ID") from e
    return {"runtime_receipt_id":receipt['decision_id'],"sha256":digest,"authority":"RUNTIME_AUDIT_ONLY","audit_backend":"NEON_APPEND_ONLY","canonical_write":False}

@app.post("/api/f7/receipt")
async def submit(req:Request):
    try: r=await req.json()
    except Exception: return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["INVALID_JSON"],"canonical_write_performed":False},400)
    if not isinstance(r,dict) or set(r)!=REQ: return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["EXACT_RECEIPT_SCHEMA_REQUIRED"],"canonical_write_performed":False},422)
    t=TASKS.get(r['task_id'])
    if not t or r['residual_id']!=t['residual_id'] or r['evidence_regions']!=[t['evidence_region']] or r['source_versions']!=[t['source_version']]: return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["TASK_SOURCE_BINDING_MISMATCH"],"canonical_write_performed":False},422)
    if r['review_mode']!='HUMAN_REVIEW' or r['authority_acknowledgement']!=ACK or r['outcome'] not in ALLOWED_OUTCOMES or r['requested_epistemic_state'] not in ALLOWED_STATES: return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["HUMAN_AUTHORITY_VALIDATION_FAILED"],"canonical_write_performed":False},422)
    if r['requested_epistemic_state'] not in ({'ND','INF','RIF','MIS','DOC'} if t['ceiling']=='DOC' else {'ND','INF'}): return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["EPISTEMIC_CEILING_EXCEEDED"],"canonical_write_performed":False},422)
    if r['outcome']=='CONFIRMED' and (not r['reviewer'] or not r['human_observation'] or not r['direct_primary_evidence_observed'] or r['target_id']!=TARGET): return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["CONFIRMED_REQUIRES_HUMAN_DIRECT_PRIMARY_AND_TARGET"],"canonical_write_performed":False},422)
    if r['outcome']!='CONFIRMED' and r['target_id']: return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["NON_PROMOTIVE_TARGET_FORBIDDEN"],"canonical_write_performed":False},422)
    digest=hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    try: audit=persist(r,digest)
    except ValueError as e: return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":[str(e)],"canonical_write_performed":False},409)
    except Exception: return JSONResponse({"state":"RECEIPT_REJECTED","reason_codes":["RUNTIME_AUDIT_PERSISTENCE_REJECTED"],"canonical_write_performed":False},503)
    if r['outcome']!='CONFIRMED': return {"state":"RETAIN_RESIDUAL","receipt":audit,"canonical_write_authorized":False,"canonical_write_performed":False}
    if r['task_id'] not in {'ERW-N12-001','ERW-N12-002'}: return {"state":"SEMANTIC_BLOCKED","receipt":audit,"reason_codes":["TARGET_SPECIFIC_SEMANTIC_GRAMMAR_REQUIRED"],"raw_human_observation":r['human_observation'],"canonical_write_authorized":False,"canonical_write_performed":False}
    m=DIR_RE.search(r['human_observation'])
    if not m: return {"state":"SEMANTIC_BLOCKED","receipt":audit,"reason_codes":["SEMANTIC_DIRECTIONAL_GRAMMAR_REQUIRED"],"raw_human_observation":r['human_observation'],"canonical_write_authorized":False,"canonical_write_performed":False}
    u_n,u_d,l_n,l_d=map(int,m.groups())
    semantic={"upper":{"count":u_n,"diameter_mm":u_d},"lower":{"count":l_n,"diameter_mm":l_d},"raw_human_observation":r['human_observation']}
    return {"state":"PATCH_CANDIDATE_READY_NO_WRITE","receipt":audit,"patch_candidate":{"task_id":r['task_id'],"residual_id":r['residual_id'],"target_id":TARGET,"target_class":"REINFORCEMENT_ASSERTION","canonical_locator":"DERIVED_CANONICAL_PROJECTION/REINFORCEMENT","operation":"ADD_OR_REPLACE_ASSERTION","requested_epistemic_state":r['requested_epistemic_state'],"source_authority":"VALIDATED_HUMAN_DIRECT_PRIMARY","evidence_regions":r['evidence_regions'],"source_versions":r['source_versions'],"semantic_payload":semantic,"canonical_write_authorized":False,"canonical_write_performed":False},"canonical_write_authorized":False,"canonical_write_performed":False}
