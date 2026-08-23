#!/usr/bin/env python3
import argparse,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--finalize',action='store_true');a=p.parse_args()
if a.prepare:
    cmds=[['python','scripts/n12_m0g_reopen_prepare.py'],['python','scripts/n12_m0g_reopen_model_contracts.py']]
else:
    cmds=[['python','scripts/n12_m0g_reopen_finalize.py']]
for cmd in cmds:
    r=subprocess.run(cmd,cwd=R)
    if r.returncode:sys.exit(r.returncode)
print('M0G_REOPEN_DISPATCH=PASS')
