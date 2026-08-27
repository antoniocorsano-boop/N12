#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'deploy/cew_user_runtime.py'
text=BUNDLE.read_text(encoding='utf-8')
required=['NEON_APPEND_ONLY','RUNTIME_AUDIT_ONLY','canonical_write_authorized":False','CEW-N12-REG-G01-R06','CEW-N12-SRC-TAV05A-V17DEC414','2 f 12 superiori e 2 f 12 inferiori']
for marker in required:
    if marker not in text:
        raise SystemExit(f'FAIL missing {marker}')

spec=importlib.util.spec_from_file_location('cew_bundle',BUNDLE)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
for phrase in ['2 Φ12 superiori + 2 Φ12 inferiori','i filari lunghi 1040 son 2 f 12 superiori e 2 f 12 inferiori']:
    m=mod.DIR_RE.search(phrase)
    if not m or tuple(map(int,m.groups()))!=(2,12,2,12):
        raise SystemExit('FAIL directional grammar')
if mod.DIR_RE.search('4 Φ12'):
    raise SystemExit('FAIL aggregate grammar admitted')
if mod.TASKS['ERW-N12-004']['ceiling']!='INF':
    raise SystemExit('FAIL R11 epistemic ceiling drift')
print('CEW_NEON_USER_RUNTIME_PASS')
print('DIRECTIONAL_NATURAL_LANGUAGE=PASS')
print('AGGREGATE_4PHI12=BLOCKED')
print('CANONICAL_WRITE=FORBIDDEN')
