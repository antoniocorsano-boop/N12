#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

ALLOWED_SCREEN = {"RELEVANT","POSSIBLY_RELEVANT","NOT_SUPPORTED","NOT_APPLICABLE","ND"}

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--contract',required=True); ap.add_argument('--profile',required=True); ap.add_argument('--registry',required=True); a=ap.parse_args()
    c,p,r=load(a.contract),load(a.profile),load(a.registry)
    errors=[]
    if p.get('degradation_execution_authorized') is not False: errors.append('degradation execution must remain false in v0 profile')
    if not p.get('evidence_recovery_queue'): errors.append('missing evidence recovery queue')
    mechanisms={m['mechanism'] for m in p.get('mechanism_screening',[])}
    required=set(c.get('screening_mechanisms',[]))
    if mechanisms != required: errors.append(f'mechanism screening mismatch: {mechanisms ^ required}')
    for m in p.get('mechanism_screening',[]):
        if m.get('state') not in ALLOWED_SCREEN: errors.append(f"invalid screening state {m.get('state')}")
    # A registry scaffold cannot become project evidence or active merely by profile presence.
    for m in r.get('models',[]):
        if m.get('calibration_state') == 'NOT_CALIBRATED' and p.get('degradation_execution_authorized'):
            errors.append(f"uncalibrated model would execute: {m.get('model_id')}")
    # Current N12 v0 must contain no measurement values until evidence is explicitly bound.
    if p.get('measurements'): errors.append('v0 N12 profile unexpectedly contains measurements')
    if errors:
        print('CEW EXPOSURE CONDITION: FAIL')
        for e in errors: print('-',e)
        return 2
    print('CEW EXPOSURE CONDITION: PASS | zones=%d | observations=%d | measurements=%d | mechanisms=%d | degradation=BLOCKED' % (len(p.get('zones',[])),len(p.get('condition_observations',[])),len(p.get('measurements',[])),len(p.get('mechanism_screening',[]))))
    return 0
if __name__=='__main__': sys.exit(main())
