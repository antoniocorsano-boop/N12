#!/usr/bin/env python3
import argparse,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--prepare',action='store_true');g.add_argument('--finalize',action='store_true');a=p.parse_args()
cmd=['python','scripts/n12_m0g_reopen_b055_prepare.py'] if a.prepare else ['python','scripts/n12_m0g_reopen_b055_finalize.py']
r=subprocess.run(cmd,cwd=R)
if r.returncode:sys.exit(r.returncode)
print('M0G_REOPEN_B055_DISPATCH=PASS')
