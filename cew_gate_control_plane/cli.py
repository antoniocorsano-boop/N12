from __future__ import annotations

import argparse, json
from dataclasses import asdict
from pathlib import Path
from .candidate_fetch import fetch_candidate
from .contracts import ControlPlaneError, load_strict_json_bytes, validate_dispatch_context, validate_pr_metadata
from .decision import reduce_decision
from .handoff import HandoffContext, build_handoff_envelope, verify_handoff_directory
from .trust_anchor import load_and_verify_promotion_record, verify_materialized_gate, verify_operational_commit_available

def _write(path:Path,value:dict[str,object])->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
def _positive_int(value:str)->int:
    try: n=int(value)
    except ValueError as exc: raise argparse.ArgumentTypeError("positive integer required") from exc
    if n<1: raise argparse.ArgumentTypeError("positive integer required")
    return n
def _bool_text(value:str)->bool:
    if value=="true": return True
    if value=="false": return False
    raise argparse.ArgumentTypeError("expected true or false")
def _out(p): p.add_argument("--output-json",type=Path,required=True)
def _parser():
    p=argparse.ArgumentParser(prog="cew-gate-control-plane"); sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("preflight"); s.add_argument("--repository",required=True); s.add_argument("--ref",required=True); s.add_argument("--ref-type",required=True); s.add_argument("--pr-number",type=_positive_int,required=True); s.add_argument("--candidate-sha",required=True); s.add_argument("--pr-metadata",type=Path); _out(s)
    s=sub.add_parser("fetch-candidate"); s.add_argument("--base-url",required=True); s.add_argument("--pr-number",type=_positive_int,required=True); s.add_argument("--candidate-sha",required=True); s.add_argument("--destination",type=Path,required=True); _out(s)
    s=sub.add_parser("verify-trust"); s.add_argument("--promotion-record",type=Path,required=True); s.add_argument("--gate-git-dir",type=Path,required=True); s.add_argument("--operational-git-dir",type=Path,required=True); _out(s)
    s=sub.add_parser("build-handoff"); s.add_argument("--receipt",type=Path,required=True); s.add_argument("--run-id",type=_positive_int,required=True); s.add_argument("--run-attempt",type=_positive_int,required=True); s.add_argument("--base-sha",required=True); s.add_argument("--pr-number",type=_positive_int,required=True); s.add_argument("--head-repository",required=True); s.add_argument("--head-sha",required=True); s.add_argument("--promotion-record",type=Path,required=True); s.add_argument("--qualification-exit-code",type=int,required=True); s.add_argument("--envelope-path",type=Path,required=True); _out(s)
    s=sub.add_parser("verify-handoff"); s.add_argument("--directory",type=Path,required=True); s.add_argument("--run-id",type=_positive_int,required=True); s.add_argument("--run-attempt",type=_positive_int,required=True); s.add_argument("--base-sha",required=True); s.add_argument("--pr-number",type=_positive_int,required=True); s.add_argument("--head-repository",required=True); s.add_argument("--head-sha",required=True); s.add_argument("--promotion-record",type=Path,required=True); _out(s)
    s=sub.add_parser("decision"); s.add_argument("--qualify-job-result",required=True); s.add_argument("--qualification-exit-code",type=int); s.add_argument("--receipt-emitted",type=_bool_text,required=True); s.add_argument("--handoff-job-result",required=True); _out(s); return p

def main(argv:list[str]|None=None)->int:
    args=_parser().parse_args(argv)
    try:
        if args.command=="preflight":
            req=validate_dispatch_context(args.repository,args.ref,args.ref_type,args.pr_number,args.candidate_sha); out={"pr_number":req.pr_number,"candidate_sha":req.candidate_sha}
            if args.pr_metadata:
                b=validate_pr_metadata(load_strict_json_bytes(args.pr_metadata.read_bytes(),label="PR_METADATA_UNAVAILABLE"),req); out.update({"head_repository":b.head_repository,"head_sha":b.head_sha})
            _write(args.output_json,out); return 0
        if args.command=="fetch-candidate":
            sha=fetch_candidate(args.base_url,args.pr_number,args.candidate_sha,args.destination); _write(args.output_json,{"candidate_sha":sha,"git_dir":str(args.destination)}); return 0
        if args.command=="verify-trust":
            a=load_and_verify_promotion_record(args.promotion_record); verify_materialized_gate(args.gate_git_dir,a); verify_operational_commit_available(args.operational_git_dir,a); _write(args.output_json,{"gate_core_commit_sha":a.g0_commit_sha,"authority_id":a.authority_id,"operational_commit_sha":a.operational_commit_sha}); return 0
        if args.command=="build-handoff":
            a=load_and_verify_promotion_record(args.promotion_record); c=HandoffContext(args.run_id,args.run_attempt,args.base_sha,args.pr_number,args.head_repository,args.head_sha); e=build_handoff_envelope(args.receipt,c,a,args.qualification_exit_code); args.envelope_path.write_text(json.dumps(e,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8"); _write(args.output_json,e); return 0
        if args.command=="verify-handoff":
            a=load_and_verify_promotion_record(args.promotion_record); c=HandoffContext(args.run_id,args.run_attempt,args.base_sha,args.pr_number,args.head_repository,args.head_sha); r=verify_handoff_directory(args.directory,c,a); _write(args.output_json,{"verified":True,"qualified":r.get("qualified")}); return 0
        if args.command=="decision":
            d=reduce_decision(qualify_job_result=args.qualify_job_result,qualification_exit_code=args.qualification_exit_code,receipt_emitted=args.receipt_emitted,handoff_job_result=args.handoff_job_result); _write(args.output_json,asdict(d)); return 0 if d.success else 1
    except ControlPlaneError as exc: _write(args.output_json,{"success":False,"failure_code":exc.code}); return 2
    except (OSError,json.JSONDecodeError,ValueError): _write(args.output_json,{"success":False,"failure_code":"CONTROL_PLANE_OR_INVOCATION_ERROR"}); return 2
    return 2
if __name__=="__main__": raise SystemExit(main())
