#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
EXPECTED_EPISTEMIC={"DOC","MIS","RIF","INF","ND"};EXPECTED_WORKFLOW={"READY","RUNNING","IN_REVIEW","BLOCKED","COMPLETE","FAILED"};EXPECTED_SEVERITY={"OK","ATTENTION","CRITICAL","NOT_ASSESSED"};REQUIRED_COMPONENTS={"ProjectContextBar","EngineeringEvidenceCard","EpistemicStateMark","EngineeringInspector","EvidenceDecisionTrail","HumanDecisionPanel","TechnicalDataTable","SourceModelSplitView","ProvenanceDrawer","EngineeringStateBanner"}
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def validate(root):
 e=[]; paths=["docs/UX/CEW_HUMAN_ENGINEERING_EXPERIENCE_MODEL_v1.md","docs/UX/CEW_ENGINEERING_DESIGN_SYSTEM_v1.md","docs/UX/CEW_ENGINEERING_INFORMATION_ARCHITECTURE_v1.md","docs/UX/CEW_UI_OPEN_SOURCE_ADOPTION_MATRIX_v1.md","automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json","automation/CEW_ENGINEERING_DESIGN_SYSTEM_CONTRACT_v1.json","automation/CEW_UX_FOUNDATION_WORK_QUEUE_v1.json","ui/foundation/tokens/cew.tokens.json","ui/foundation/contracts/component-catalog.json","ui/foundation/contracts/information-architecture.json","ui/foundation/cew-engineering.css","ui/foundation/reference/engineering-workspace.html"]
 for rel in paths:
  if not (root/rel).exists():e.append(f"missing {rel}")
 if e:return e
 h=load(root/"automation/CEW_HUMAN_ENGINEERING_EXPERIENCE_CONTRACT_v1.json");d=load(root/"automation/CEW_ENGINEERING_DESIGN_SYSTEM_CONTRACT_v1.json");t=load(root/"ui/foundation/tokens/cew.tokens.json");c=load(root/"ui/foundation/contracts/component-catalog.json");q=load(root/"automation/CEW_UX_FOUNDATION_WORK_QUEUE_v1.json")
 if h.get("primary_professional_role")!="CIVIL_STRUCTURAL_ENGINEER_EXISTING_BUILDINGS":e.append("primary professional role drift")
 if h["internal_ids"].get("primary_ui_label") is not False:e.append("raw IDs may not be primary UI labels")
 if h["human_authority"].get("ui_may_write_canonical_directly") is not False:e.append("UI canonical write boundary violated")
 if h["human_authority"].get("engineering_decision_may_be_prefilled") is not False:e.append("engineering decision prefill forbidden")
 states=d.get("state_taxonomies",{});sets=[set(states.get("EPISTEMIC",[])),set(states.get("WORKFLOW",[])),set(states.get("ENGINEERING_SEVERITY",[]))]
 if sets[0]!=EXPECTED_EPISTEMIC or sets[1]!=EXPECTED_WORKFLOW or sets[2]!=EXPECTED_SEVERITY:e.append("state taxonomy drift")
 if any(a&b for i,a in enumerate(sets) for b in sets[i+1:]):e.append("state taxonomies must be disjoint")
 if d["state_rules"].get("color_only_encoding_allowed") is not False:e.append("color-only state encoding forbidden")
 if d["third_party_boundary"].get("viewer_geometry_is_evidence_authority") is not False:e.append("viewer may not become evidence authority")
 names={x["name"] for x in c.get("components",[])}
 if not REQUIRED_COMPONENTS<=names:e.append("required engineering component missing")
 for x in c.get("components",[]):
  if x.get("raw_ids_primary") is not False:e.append(f"{x.get('name')}: raw ID primary label")
  a=x.get("accessibility",{})
  if not all(a.get(k) is True for k in ("keyboard_operable","visible_focus","state_not_color_only")):e.append(f"{x.get('name')}: accessibility contract incomplete")
 for taxonomy in ("epistemic","workflow","severity"):
  for name,spec in t.get(taxonomy,{}).items():
   if not spec.get("label") or not spec.get("icon"):e.append(f"{taxonomy}.{name}: text/icon missing")
 items={x["id"]:x for x in q.get("items",[])}
 if set(items)!={"UX0-001","UX1-001"}:e.append("UX work queue mismatch")
 if q.get("canonical_promotion")!="DISABLED":e.append("UX queue may not promote canonically")
 ref=(root/"ui/foundation/reference/engineering-workspace.html").read_text(encoding="utf-8")
 if "EvidenceRegion congelata da CEW-F2" not in ref:e.append("reference shell must declare frozen F2 region")
 if "Nessuna associazione preconfermata" not in ref:e.append("reference shell may not preconfirm binding")
 return e
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1]);args=ap.parse_args();errors=validate(args.root)
 if errors:
  print("CEW UX FOUNDATION = FAIL");[print(f"- {x}") for x in errors];raise SystemExit(1)
 print("CEW UX FOUNDATION = PASS\nPrimary role = CIVIL_STRUCTURAL_ENGINEER_EXISTING_BUILDINGS\nSTATE_TAXONOMIES = DISJOINT\nCOLOR_ONLY_STATE = FORBIDDEN\nDIRECT_CANONICAL_UI_WRITE = FORBIDDEN\nUX0-001 = READY_FOR_RECEIPT")
if __name__=="__main__":main()
