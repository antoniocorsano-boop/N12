#!/usr/bin/env python3
"""Generate CEW Structural Viewer v0 with evidence/assessment overlay.

Builds on the read-only structural viewer. The overlay exposes project-level
claims, M1E blockers, assessment modes and investigation candidates. It does
not change the canonical model or authorize solver execution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cew_structural_model_builder import BuildError, build_model
from cew_structural_viewer import make_html


def inject_overlay(base_html: str, profile: dict, contract: dict) -> str:
    data = json.dumps({"profile": profile, "contract": contract}, ensure_ascii=False, separators=(",", ":"))
    overlay = r'''
<style>
#assessmentToggle{position:absolute;right:12px;top:12px;z-index:5}
#assessmentPanel{position:absolute;right:12px;top:52px;width:min(390px,calc(100% - 24px));max-height:calc(100% - 64px);overflow:auto;z-index:4;background:rgba(19,28,37,.97);border:1px solid #3a4957;border-radius:8px;padding:12px;display:none;box-shadow:0 12px 30px rgba(0,0,0,.35)}
#assessmentPanel.open{display:block}.ap-title{font-weight:700;margin-bottom:8px}.ap-section{border-top:1px solid #32404d;padding-top:9px;margin-top:9px}.ap-section h3{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#9fb0bf;margin:0 0 7px}.claim,.blocker,.mode,.investigation{padding:7px 8px;background:#1d2832;border:1px solid #31404c;border-radius:6px;margin:6px 0;font-size:12px}.claim strong,.blocker strong,.mode strong,.investigation strong{display:block;margin-bottom:2px}.muted2{color:#9caab7}.statechip{display:inline-block;padding:1px 5px;border-radius:10px;border:1px solid #51616f;font-size:10px;margin-left:4px}.blocked{border-color:#724a50}.mode-ok{border-color:#3f6e58}.mode-no{border-color:#6b4b50}
</style>
<button id="assessmentToggle">Conoscenza / scenari</button>
<div id="assessmentPanel"><div class="ap-title">CEW Existing Assessment</div><div id="assessmentContent"></div></div>
<script>
const ASSESSMENT=__ASSESSMENT__;
(function(){
 const p=ASSESSMENT.profile,c=ASSESSMENT.contract,panel=document.getElementById('assessmentPanel'),out=document.getElementById('assessmentContent');
 document.getElementById('assessmentToggle').onclick=()=>panel.classList.toggle('open');
 const esc2=s=>String(s??'').replace(/[&<>]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[m]));
 const claims=(p.claims||[]).map(x=>`<div class="claim"><strong>${esc2(x.domain)} <span class="statechip">${esc2(x.state)}</span></strong><div>${esc2(x.value??'ND')}</div><div class="muted2">${esc2(x.evidence_kind)}</div></div>`).join('');
 const blockers=(p.blocking_domains||[]).map(x=>`<div class="blocker blocked"><strong>${esc2(x.id)} · ${esc2(x.domain)}</strong><div class="muted2">${esc2((x.missing||[]).join(', '))}</div></div>`).join('');
 const probReady=(p.probability_models||[]).length>0;
 const hasTests=(p.claims||[]).some(x=>x.evidence_kind==='TEST' || x.evidence_kind==='CURRENT_MEASUREMENT');
 const modes=Object.entries(c.modes||{}).map(([id,m])=>{let ready=true,why=[];if(m.requires_probability_model&&!probReady){ready=false;why.push('modello probabilistico non calibrato')}if(m.requires_test_evidence&&!hasTests){ready=false;why.push('evidenza prove non registrata')}if((p.blocking_domains||[]).length&&id!=='MODE-1'){why.push('residui M1E aperti')}return `<div class="mode ${ready?'mode-ok':'mode-no'}"><strong>${id} · ${esc2(m.id)}</strong><div>${esc2(m.purpose)}</div><div class="muted2">${ready?'profilo generabile; autorizzazione solver resta governata dal gate':why.join(' · ')}</div></div>`}).join('');
 const inv=(p.investigation_candidates||[]).sort((a,b)=>(a.priority||99)-(b.priority||99)).map(x=>`<div class="investigation"><strong>#${esc2(x.priority)} · ${esc2(x.investigation_id)}</strong><div>${esc2(x.test_method)}</div><div class="muted2">invasività ${esc2(x.invasiveness)} · riduzione incertezza ${esc2(x.expected_uncertainty_reduction)}</div></div>`).join('');
 out.innerHTML=`<div class="ap-section"><h3>Profilo</h3><div class="muted2">${esc2(p.profile_status)} · ${(p.blocking_domains||[]).length} blocker</div></div><div class="ap-section"><h3>Claim</h3>${claims}</div><div class="ap-section"><h3>Blocker M1E</h3>${blockers}</div><div class="ap-section"><h3>Modalità assessment</h3>${modes}</div><div class="ap-section"><h3>Indagini candidate</h3>${inv}</div>`;
})();
</script>
'''.replace('__ASSESSMENT__', data)
    return base_html.replace('</body>', overlay + '\n</body>')


def main() -> int:
    p=argparse.ArgumentParser()
    for name in ['handoff','nodes','rigid-offsets','members','foundation','foundation-xy-rule','assessment-profile','assessment-contract','output-html']:
        p.add_argument('--'+name, required=True, type=Path)
    a=p.parse_args()
    try:
        model=build_model(a.handoff,a.nodes,a.rigid_offsets,a.members,a.foundation,a.foundation_xy_rule)
        profile=json.loads(a.assessment_profile.read_text(encoding='utf-8'))
        contract=json.loads(a.assessment_contract.read_text(encoding='utf-8'))
    except (OSError,json.JSONDecodeError,BuildError) as exc:
        print(f'CEW VIEWER OVERLAY: FAIL: {exc}')
        return 2
    if profile.get('project_id') != model.get('project_id'):
        print('CEW VIEWER OVERLAY: FAIL: project mismatch')
        return 2
    if len(profile.get('blocking_domains',[])) != 6:
        print('CEW VIEWER OVERLAY: FAIL: expected current N12 six-blocker profile')
        return 2
    html=inject_overlay(make_html(model),profile,contract)
    a.output_html.parent.mkdir(parents=True,exist_ok=True)
    a.output_html.write_text(html,encoding='utf-8')
    print(f"CEW VIEWER OVERLAY: PASS | claims={len(profile.get('claims',[]))} | blockers={len(profile.get('blocking_domains',[]))} | investigations={len(profile.get('investigation_candidates',[]))}")
    return 0

if __name__=='__main__':
    raise SystemExit(main())
