#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, html, json
from pathlib import Path
from urllib.parse import quote


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def csv_rows(path: Path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def esc(v):
    return html.escape(str(v))


def _state_view(state):
    """Normalize historical CEW state 1.x and product/runtime state 2.x for the legacy Control Room renderer.

    This is a display compatibility layer only. It does not restore engineering authority to CEW product state.
    """
    if state.get('state_role') == 'CEW_PRODUCT_RUNTIME_STATE':
        product_maturity = state.get('product_maturity', {})
        maturity = {
            'current_level': product_maturity.get('user_workflow', 'UNKNOWN'),
            'target_next': product_maturity.get('target', 'UNKNOWN'),
        }
        current = dict(state.get('current_product_work_item', {}))
        current.setdefault('objective', 'Product work package selected by the CEW Product Orchestrator.')
        modules = []
        for cap in state.get('capability_maturity', []):
            dimensions = [
                f"engine={cap.get('engine_available')}",
                f"integrated={cap.get('integrated')}",
                f"workflow={cap.get('user_workflow_available')}",
                f"human_factors={cap.get('human_factors_validated')}",
                f"production={cap.get('production_ready')}",
            ]
            modules.append({'id': cap.get('id', 'UNKNOWN'), 'status': ' | '.join(dimensions)})
        roadmap = [
            {'id': row.get('phase_id'), 'name': row.get('title'), 'status': row.get('workspace_status')}
            for row in state.get('engineering_state', {}).get('phase_projection', [])
        ]
        return {
            'reference_project': state.get('reference_project', 'UNKNOWN'),
            'maturity': maturity,
            'current_work_item': current,
            'implemented_modules': modules,
            'roadmap': roadmap,
            'next_action': state.get('next_action', ''),
            'anti_drift_rules': state.get('anti_drift_rules', []),
        }
    return state


def build(state, issues, review_tasks=None):
    view = _state_view(state)
    blockers = issues['issues']
    review_tasks = review_tasks or []
    impact_counts = {}
    for i in blockers:
        impact_counts[i['impact']] = impact_counts.get(i['impact'], 0) + 1
    rows = ''.join(
        f"<tr><td>{esc(i['issue_id'])}</td><td>{esc(i['title'])}</td><td>{esc(i['impact'])}</td><td>{esc(i['state'])}</td><td>{esc(i['required_authority'])}</td></tr>"
        for i in blockers
    )
    modules = ''.join(
        f"<li><b>{esc(m['id'])}</b> — {esc(m['status'])}</li>" for m in view['implemented_modules']
    )
    roadmap = ''.join(
        f"<tr><td>{esc(r['id'])}</td><td>{esc(r['name'])}</td><td>{esc(r['status'])}</td></tr>" for r in view['roadmap']
    )
    cards = ''.join(
        f"<div class='card'><div class='big'>{n}</div><div>{esc(k.replace('_',' '))}</div></div>" for k,n in sorted(impact_counts.items())
    )
    review_rows = ''.join(
        f"<tr><td>{esc(t['task_id'])}</td><td>{esc(t['residual_id'])}</td><td>{esc(t['domain'])}</td><td>{esc(t['status'])}</td><td><a class='action' href='/review/f7?task={quote(t['task_id'])}'>Apri revisione</a></td></tr>"
        for t in review_tasks
    )
    review_section = '' if not review_tasks else f'''
<section><h2>Revisione umana evidenze F7</h2><div class="card authority"><b>HUMAN REVIEW — NO CANONICAL WRITE</b><p>La revisione avviene direttamente nel Control Room. CEW valida la receipt, esegue il promotion gate e prepara soltanto un candidato governato. Nessun dato canonico viene scritto da questa UI.</p></div><table><thead><tr><th>Task</th><th>Residuo</th><th>Dominio</th><th>Stato</th><th>Azione</th></tr></thead><tbody>{review_rows}</tbody></table></section>'''
    return f'''<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CEW Project Control Room — {esc(view['reference_project'])}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#f5f6f8;color:#18212b}}header{{padding:24px 32px;background:white;border-bottom:1px solid #ddd}}main{{padding:24px 32px;max-width:1400px;margin:auto}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}.card{{background:white;padding:18px;border:1px solid #ddd;border-radius:10px}}.authority{{border-left:5px solid #365f91}}.big{{font-size:28px;font-weight:700}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left}}section{{margin:24px 0}}code{{background:#eee;padding:2px 5px;border-radius:4px}}.status{{font-weight:700}}ul{{background:white;border:1px solid #ddd;border-radius:10px;padding:18px 32px}}a.action{{display:inline-block;padding:7px 10px;background:#18212b;color:white;text-decoration:none;border-radius:6px}}
</style></head><body><header><h1>CEW Project Control Room — {esc(view['reference_project'])}</h1><div class="status">{esc(view['maturity']['current_level'])} → target {esc(view['maturity']['target_next'])}</div></header><main>
<section><h2>Current work item</h2><div class="card"><b>{esc(view['current_work_item']['id'])}</b><p>{esc(view['current_work_item']['objective'])}</p><code>{esc(view['current_work_item']['state'])}</code></div></section>
{review_section}
<section><h2>Residual impact</h2><div class="grid">{cards}</div></section>
<section><h2>Current issues</h2><table><thead><tr><th>ID</th><th>Issue</th><th>Impact</th><th>State</th><th>Authority</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Implemented capabilities</h2><ul>{modules}</ul></section>
<section><h2>Lifecycle projection</h2><table><thead><tr><th>ID</th><th>Phase</th><th>Workspace status</th></tr></thead><tbody>{roadmap}</tbody></table></section>
<section><h2>Next action</h2><div class="card">{esc(view['next_action'])}</div></section>
<section><h2>Anti-drift rules</h2><ul>{''.join(f'<li>{esc(x)}</li>' for x in view['anti_drift_rules'])}</ul></section>
</main></body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', required=True, type=Path)
    ap.add_argument('--issues', required=True, type=Path)
    ap.add_argument('--f7-tasks', type=Path)
    ap.add_argument('--output', required=True, type=Path)
    a = ap.parse_args()
    state, issues = load(a.state), load(a.issues)
    review_tasks = csv_rows(a.f7_tasks) if a.f7_tasks else []
    if state.get('state_role') not in {'SINGLE_OPERATIONAL_SOURCE_OF_TRUTH', 'CEW_PRODUCT_RUNTIME_STATE'}:
        raise SystemExit('FAIL: invalid CURRENT state role')
    if len(issues.get('issues', [])) == 0:
        raise SystemExit('FAIL: empty issue registry')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(build(state, issues, review_tasks), encoding='utf-8')
    view = _state_view(state)
    print(f"CEW CONTROL ROOM: PASS | issues={len(issues['issues'])} | f7_tasks={len(review_tasks)} | work_item={view['current_work_item']['id']}")

if __name__ == '__main__':
    main()
