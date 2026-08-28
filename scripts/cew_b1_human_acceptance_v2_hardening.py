#!/usr/bin/env python3
from __future__ import annotations

import json
import os

import cew_b1_human_acceptance_v2 as base


def _runtime_revision() -> str:
    return (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or "UNRESOLVED_RUNTIME_REVISION"
    )


def _runtime_deployment() -> str:
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        return render_url
    render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
    if render_host:
        return f"https://{render_host}"
    return os.getenv("VERCEL_URL") or "LOCAL_OR_UNRESOLVED_DEPLOYMENT"


def _harden_template(template: str) -> str:
    replacements = {
        "const TASKS=__TASKS_JSON__;const CONTRACT=__CONTRACT_JSON__;const RUNTIME_REVISION=__COMMIT_JSON__;const RUNTIME_DEPLOYMENT=__DEPLOYMENT_JSON__;const SESSION_KEY=__SESSION_KEY_JSON__;":
            "const TASKS=__TASKS_JSON__;const CONTRACT=__CONTRACT_JSON__;const RUNTIME_REVISION=__COMMIT_JSON__;const RUNTIME_DEPLOYMENT=__DEPLOYMENT_JSON__;const SESSION_KEY=__SESSION_KEY_JSON__+'::'+RUNTIME_REVISION;",
        "function loadSession(){try{return JSON.parse(localStorage.getItem(SESSION_KEY))||freshSession()}catch(_e){return freshSession()}}":
            "function loadSession(){try{const stored=JSON.parse(localStorage.getItem(SESSION_KEY));if(!stored)return freshSession();if(stored.runtime_revision!==RUNTIME_REVISION||stored.runtime_deployment!==RUNTIME_DEPLOYMENT){localStorage.removeItem(SESSION_KEY);return freshSession()}return stored}catch(_e){return freshSession()}}",
        "if(t.task_id==='UX-DOC-01')return last.startsWith('/drawings/TAV-05A')?'SUCCESS':'FALSE_SUCCESS';":
            "if(t.task_id==='UX-DOC-01'){const wrongSourceOrVersion=paths.some(p=>p.startsWith('/drawings/')&&!p.startsWith('/drawings/TAV-05A'));return !wrongSourceOrVersion&&last.startsWith('/drawings/TAV-05A')?'SUCCESS':'FALSE_SUCCESS';}",
        "if(t.task_id==='UX-DOC-03'){const macro=m.source_scale_states.some(v=>v.startsWith('MACRO'));const finalMicro=(m.source_scale_states[m.source_scale_states.length-1]||'').startsWith('MICRO');return macro&&finalMicro&&last.startsWith('/evidence/review?task=ERW-N12-001')?'SUCCESS':'FALSE_SUCCESS'}":
            "if(t.task_id==='UX-DOC-03'){const macro=m.source_scale_states.some(v=>v.startsWith('MACRO'));const finalMicro=(m.source_scale_states[m.source_scale_states.length-1]||'').startsWith('MICRO');const zoomed=m.viewer_states.some(v=>v.startsWith('Evidenza · Zoom ')&&!v.includes('Zoom 100%'));const panned=m.viewer_states.some(v=>v.includes('Pan usato'));return zoomed&&panned&&macro&&finalMicro&&last.startsWith('/evidence/review?task=ERW-N12-001')?'SUCCESS':'FALSE_SUCCESS'}",
        "function deriveBlockers(s){const out=[];":
            "function deriveBlockers(s){const out=[];if(RUNTIME_REVISION==='UNRESOLVED_RUNTIME_REVISION')out.push('RUNTIME_REVISION_UNRESOLVED');if(RUNTIME_DEPLOYMENT==='LOCAL_OR_UNRESOLVED_DEPLOYMENT')out.push('RUNTIME_DEPLOYMENT_UNRESOLVED');",
        "if(r.task_outcome==='FALSE_SUCCESS')out.push(t.task_id+':FALSE_SUCCESS');":
            "if(r.task_outcome==='FALSE_SUCCESS')out.push(t.task_id+':FALSE_SUCCESS');if(t.task_id==='UX-DOC-01'&&(r.navigation_path||[]).some(p=>p.startsWith('/drawings/')&&!p.startsWith('/drawings/TAV-05A')))out.push(t.task_id+':WRONG_SOURCE_OR_VERSION');",
    }
    hardened = template
    for old, new in replacements.items():
        if old not in hardened:
            raise RuntimeError(f"B1.8 hardening anchor missing: {old[:80]}")
        hardened = hardened.replace(old, new, 1)
    return hardened


def task_specs() -> list[dict]:
    return base.task_specs()


def build_app() -> str:
    contract = base._load(base.CONTRACT)
    tasks = task_specs()
    template = _harden_template(base.TEMPLATE)
    commit = _runtime_revision()
    deployment = _runtime_deployment()
    return (
        template
        .replace("__TASKS_JSON__", json.dumps(tasks, ensure_ascii=False).replace("</", "<\\/"))
        .replace(
            "__CONTRACT_JSON__",
            json.dumps({"reviewer_decisions": contract["reviewer_decisions"]}, ensure_ascii=False).replace("</", "<\\/"),
        )
        .replace("__COMMIT_JSON__", json.dumps(commit))
        .replace("__DEPLOYMENT_JSON__", json.dumps(deployment))
        .replace("__SESSION_KEY_JSON__", json.dumps(base.SESSION_KEY))
    )


if __name__ == "__main__":
    print(build_app())
