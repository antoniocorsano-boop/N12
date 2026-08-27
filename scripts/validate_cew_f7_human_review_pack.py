#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'automation/CEW_HUMAN_DECISION_INTAKE_CONTRACT_v1.json'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--built-dir',required=True);a=ap.parse_args();b=Path(a.built_dir)
    c=json.loads(CONTRACT.read_text(encoding='utf-8'));m=json.loads((b/'human_review_manifest.json').read_text(encoding='utf-8'))
    if c.get('milestone')!='CEW-F7' or m.get('authority')!='HUMAN_REVIEW_INPUT_ONLY':raise AssertionError('intake authority drift')
    inv=c['authority_invariants'];false_keys=['pack_may_prefill_outcome','pack_may_prefill_human_observation','pack_may_claim_direct_primary_evidence','pack_may_select_promotion_target','pack_may_request_epistemic_promotion','pack_may_write_canonical','pack_may_modify_f2_geometry','pack_may_reopen_m0g']
    if any(inv[k] is not False for k in false_keys):raise AssertionError('intake authority weakened')
    if len(m.get('entries',[]))!=4 or m.get('prefilled_decisions')!=0:raise AssertionError('review inventory/prefill drift')
    if m.get('compact_review') is not True:raise AssertionError('compact review contract missing')
    expected_unlocated={'ERW-N12-001','ERW-N12-002'}
    for e in m['entries']:
        d=e['decision_template']
        if d['review_mode']!='HUMAN_REVIEW':raise AssertionError('review mode drift')
        for k in ('decision_id','reviewer','timestamp','outcome','human_observation','requested_epistemic_state','target_id','reopen_approval_id'):
            if d[k] != '':raise AssertionError(f'forbidden prefill: {e["task_id"]}/{k}')
        if d['direct_primary_evidence_observed'] is not None or d['authority_acknowledgement'] is not False:raise AssertionError('human acknowledgement prefilled')
        if len(d['evidence_regions'])!=1 or len(d['source_versions'])!=1:raise AssertionError('evidence provenance missing')
        for key in ('element_it','known_it','missing_it','technical_it'):
            if not str(e.get(key,'')).strip():raise AssertionError(f'compact field missing: {e["task_id"]}/{key}')
        if e['task_id'] in expected_unlocated and 'FILARE DA LOCALIZZARE SU TAV-05S' not in e['element_it']:
            raise AssertionError(f'unverified filare was not exposed as unresolved: {e["task_id"]}')
        viewer=b/e['viewer_url'].split('?')[0]
        context=b/e['context_viewer_url'].split('?')[0]
        if not viewer.is_file() or not context.is_file():raise AssertionError(f'missing embedded viewer: {e["task_id"]}')
        if e.get('context_source') not in ('TAV-05S','TAV-06S'):raise AssertionError('unexpected carpenteria context source')
    for rel in ('index.html','app.js','human_review_manifest.json','source-viewer/index.html','source-viewer/viewer_manifest.json'):
        if not (b/rel).is_file():raise AssertionError(f'missing review pack file {rel}')
    vm=json.loads((b/'source-viewer/viewer_manifest.json').read_text(encoding='utf-8'))
    context_codes={x.get('source_code') for x in vm.get('context_sources',[])}
    expected_context={'TAV-05S','TAV-06S'}
    if context_codes!=expected_context:raise AssertionError(f'context coverage drift: {context_codes}')
    if any(x in context_codes for x in ('TAV-04S','TAV-06E')):raise AssertionError('out-of-scope context source leaked into clean F7 review pack')
    html=(b/'index.html').read_text(encoding='utf-8')
    js=(b/'app.js').read_text(encoding='utf-8')
    for token in ('FILARE / ELEMENTO','GIÀ RICONOSCIUTO','DA COMPLETARE','RISPOSTA','Apri tavole di verifica','Dettagli tecnici'):
        if token not in js:raise AssertionError(f'compact review control missing: {token}')
    for legacy in ('Cosa devi controllare','1. Dove guardare:','2. Cosa cercare:','Non fare questo:','Quando puoi confermare:','Registra il risultato'):
        if legacy in js or legacy in html:raise AssertionError(f'verbose legacy review block reintroduced: {legacy}')
    for token in ('CONFIRMED','direct_primary_evidence_observed','authority_acknowledgement','target_id','Esporta la decisione in JSON'):
        if token not in js:raise AssertionError(f'human decision control missing: {token}')
    if '.compact-grid' not in html or 'Revisione tecnica essenziale' not in html:raise AssertionError('compact shell missing')
    if re.search(r'canonical_write[^\n]*true',json.dumps(m),flags=re.I):raise AssertionError('review pack gained canonical write')
    print('HUMAN_DECISION_INTAKE_PACK_PASS')
    print('TASKS=4/4')
    print('COMPACT_REVIEW=PASS')
    print('UNVERIFIED_FILARE_LABELS=EXPLICIT')
    print('PREFILLED_OUTCOMES=0')
    print('PREFILLED_HUMAN_OBSERVATIONS=0')
    print('PREFILLED_DIRECT_PRIMARY_CLAIMS=0')
    print('PREFILLED_PROMOTION_TARGETS=0')
    print('PRIMARY_SOURCE_VIEWER=EMBEDDED')
    print('CARPENTERIA_CONTEXT=TAV-05S,TAV-06S')
    print('OUT_OF_SCOPE_CONTEXT=NONE')
    print('CANONICAL_WRITE=FORBIDDEN')
    print('M0G_REOPEN=FORBIDDEN')
    return 0

if __name__=='__main__':raise SystemExit(main())
