#!/usr/bin/env python3
import json
from pathlib import Path

REGISTRY = Path('data/benchmark/n12_telaio5_source_recovery_v1.json')


def main() -> int:
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    slots = {s['slot_id']: s for s in data['required_source_slots']}
    cases = data['held_out_cases']

    errors = []
    ready = []
    blocked = []

    for case_id, case in cases.items():
        slot_id = case['required_source_slot']
        slot = slots.get(slot_id)
        if slot is None:
            errors.append(f'{case_id}: missing required source slot {slot_id}')
            continue
        fields = ('sha256', 'source_version_id', 'page_id', 'evidence_region_id')
        complete = slot.get('bytes_state') == 'PRESENT' and all(slot.get(k) for k in fields)
        if complete:
            ready.append(case_id)
        else:
            blocked.append(case_id)

    expected_gate = 'READY_FOR_HELD_OUT_LOCALIZATION' if len(ready) == len(cases) and not errors else 'BLOCKED_SOURCE_BYTES_MISSING'
    declared_gate = data['materialization_gate']['current_state']
    if declared_gate != expected_gate:
        errors.append(f'gate state mismatch: declared={declared_gate} expected={expected_gate}')

    if data['authority']['may_create_source_version']:
        errors.append('recovery registry must not itself authorize SourceVersion creation')
    if data['authority']['canonical_write_authorized']:
        errors.append('canonical write must remain forbidden')

    print(json.dumps({
        'schema': 'N12_CALCULATION_SOURCE_MATERIALIZATION_GATE_RESULT_v1',
        'ready_cases': ready,
        'blocked_cases': blocked,
        'gate_state': expected_gate,
        'errors': errors,
    }, indent=2))

    if errors:
        return 1
    print('N12_CALCULATION_SOURCE_MATERIALIZATION_GATE_VALID')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
