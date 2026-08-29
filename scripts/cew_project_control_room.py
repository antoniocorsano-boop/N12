#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def esc(v):
    return html.escape(str(v))


def build(state, issues):
    blockers = issues['issues']
    impact_counts = {}
    for i in blockers:
        impact_counts[i['impact']] = impact_counts.get(i['impact'], 0) + 1
    rows = ''.join(
        f"<tr><td>{esc(i['issue_id'])}</td><td>{esc(i['title'])}</td><td>{esc(i['impact'])}</td><td>{esc(i['state'])}</td><td>{esc(i['required_authority'])}</td></tr>"
        for i in blockers
    )
    modules = ''.join(
        f"<li><b>{esc(m['id'])}</b> — {esc(m['status'])}</li>" for m in state['implemented_modules']
    )
    roadmap = ''.join(
        f"<tr><td>{esc(r['id'])}</td><td>{esc(r['name'])}</td><td>{esc(r['status'])}</td></tr>" for r in state['roadmap']
    )
    cards = ''.join(
        f"<div class='card'><div class='big'>{n}</div><div>{esc(k.replace('_',' '))}</div></div>" for k,n in sorted(impact_counts.items())
    )
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>CEW Project Control Room — {esc(state['reference_project'])}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#f5f6f8;color:#18212b}}header{{padding:24px 32px;background:white;border-bottom:1px solid #ddd}}main{{padding:24px 32px;max-width:1400px;margin:auto}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}.card{{background:white;padding:18px;border:1px solid #ddd;border-radius:10px}}.big{{font-size:28px;font-weight:700}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left}}section{{margin:24px 0}}code{{background:#eee;padding:2px 5px;border-radius:4px}}.status{{font-weight:700}}ul{{background:white;border:1px solid #ddd;border-radius:10px;padding:18px 32px}}
</style></head><body><header><h1>CEW Project Control Room — {esc(state['reference_project'])}</h1><div class="status">{esc(state['maturity']['current_level'])} → target {esc(state['maturity']['target_next'])}</div></header><main>
<section><h2>Current work item</h2><div class="card"><b>{esc(state['current_work_item']['id'])}</b><p>{esc(state['current_work_item']['objective'])}</p><code>{esc(state['current_work_item']['state'])}</code></div></section>
<section><h2>Residual impact</h2><div class="grid">{cards}</div></section>
<section><h2>Current issues</h2><table><thead><tr><th>ID</th><th>Issue</th><th>Impact</th><th>State</th><th>Authority</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Implemented modules</h2><ul>{modules}</ul></section>
<section><h2>Roadmap</h2><table><thead><tr><th>ID</th><th>Slice</th><th>Status</th></tr></thead><tbody>{roadmap}</tbody></table></section>
<section><h2>Next action</h2><div class="card">{esc(state['next_action'])}</div></section>
<section><h2>Anti-drift rules</h2><ul>{''.join(f'<li>{esc(x)}</li>' for x in state['anti_drift_rules'])}</ul></section>
</main></body></html>'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', required=True, type=Path)
    ap.add_argument('--issues', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    a = ap.parse_args()
    state, issues = load(a.state), load(a.issues)
    if state.get('state_role') != 'SINGLE_OPERATIONAL_SOURCE_OF_TRUTH':
        raise SystemExit('FAIL: invalid CURRENT state role')
    if len(issues.get('issues', [])) == 0:
        raise SystemExit('FAIL: empty issue registry')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(build(state, issues), encoding='utf-8')
    print(f"CEW CONTROL ROOM: PASS | issues={len(issues['issues'])} | work_item={state['current_work_item']['id']}")

if __name__ == '__main__':
    main()
