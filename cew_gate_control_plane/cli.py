from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .candidate_fetch import fetch_candidate
from .contracts import ControlPlaneError, load_strict_json_bytes, validate_dispatch_context, validate_pr_metadata
from .decision import reduce_decision
from .handoff import HandoffContext, build_handoff_envelope, verify_handoff_directory
from .trust_anchor import load_and_verify_promotion_record, verify_materialized_gate, verify_operational_commit_available


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def _positive_int(value: object, *, code: str) -> int:
    if isinstance(value, bool):
        raise ControlPlaneError(code)
    try:
        text = str(value)
        if not text or any(ch not in "0123456789" for ch in text):
            raise ValueError
        number = int(text)
    except (TypeError, ValueError) as exc:
        raise ControlPlaneError(code) from exc
    if number < 1:
        raise ControlPlaneError(code)
    return number


def _exit_code(value: object | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ControlPlaneError(code="CONTROL_PLANE_OR_INVOCATION_ERROR")
    text = str(value)
    if text not in {"0", "1", "2"}:
        raise ControlPlaneError("CONTROL_PLANE_OR_INVOCATION_ERROR")
    return int(text)


def _bool_text(value: object) -> bool:
    if value == "true": return True
    if value == "false": return False
    raise ControlPlaneError("CONTROL_PLANE_OR_INVOCATION_ERROR")


def _add_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-json", type=Path, required=True)


def _parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="cew-gate-control-plane"); sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("preflight"); s.add_argument("--repository",required=True); s.add_argument("--ref",required=True); s.add_argument("--ref-type",required=True); s.add_argument("--pr-number",required=True); s.add_argument("--candidate-sha",required=True); s.add_argument("--pr-metadata",type=Path); _add_output(s)
    s=sub.add_parser("fetch-candidate"); s.add_argument("--base-url",required=True); s.add_argument("--pr-number",required=True); s.add_argument("--candidate-sha",required=True); s.add_argument("--destination",type=Path,required=True); _add_output(s)
    s=sub.add_parser("verify-trust"); s.add_argument("--promotion-record",type=Path,required=True); s.add_argument("--gate-git-dir",type=Path,required=True); s.add_argument("--operational-git-dir",type=Path,required=True); _add_output(s)
    s=sub.add_parser("build-handoff"); s.add_argument("--receipt",type=Path,required=True); s.add_argument("--run-id",required=True); s.add_argument("--run-attempt",required=True); s.add_argument("--base-sha",required=True); s.add_argument("--pr-number",required=True); s.add_argument("--head-repository",required=True); s.add_argument("--head-sha",required=True); s.add_argument("--promotion-record",type=Path,required=True); s.add_argument("--qualification-exit-code",required=True); s.add_argument("--envelope-path",type=Path,required=True); _add_output(s)
    s=sub.add_parser("verify-handoff"); s.add_argument("--directory",type=Path,required=True); s.add_argument("--run-id",required=True); s.add_argument("--run-attempt",required=True); s.add_argument("--base-sha",required=True); s.add_argument("--pr-number",required=True); s.add_argument("--head-repository",required=True); s.add_argument("--head-sha",required=True); s.add_argument("--promotion-record",type=Path,required=True); _add_output(s)
    s=sub.add_parser("decision"); s.add_argument("--qualify-job-result",required=True); s.add_argument("--qualification-exit-code"); s.add_argument("--receipt-emitted",required=True); s.add_argument("--handoff-job-result",required=True); _add_output(s)
    return p


def main(argv: list[str] | None=None) -> int:
    args=_parser().parse_args(argv)
    try:
        if args.command=="preflight":
            pr_number=_positive_int(args.pr_number,code="INVALID_DISPATCH_INPUT")
            req=validate_dispatch_context(args.repository,args.ref,args.ref_type,pr_number,args.candidate_sha); out={"pr_number":req.pr_number,"candidate_sha":req.candidate_sha}
            if args.pr_metadata:
                meta=load_strict_json_bytes(args.pr_metadata.read_bytes(),label="PR_METADATA_UNAVAILABLE"); binding=validate_pr_metadata(meta,req); out.update({"head_repository":binding.head_repository,"head_sha":binding.head_sha})
            _write(args.output_json,out); return 0
        if args.command=="fetch-candidate":
            pr_number=_positive_int(args.pr_number,code="INVALID_DISPATCH_INPUT")
            sha=fetch_candidate(args.base_url,pr_number,args.candidate_sha,args.destination); _write(args.output_json,{"candidate_sha":sha,"git_dir":str(args.destination)}); return 0
        if args.command=="verify-trust":
            anchor=load_and_verify_promotion_record(args.promotion_record); verify_materialized_gate(args.gate_git_dir,anchor); verify_operational_commit_available(args.operational_git_dir,anchor); _write(args.output_json,{"gate_core_commit_sha":anchor.g0_commit_sha,"authority_id":anchor.authority_id,"operational_commit_sha":anchor.operational_commit_sha}); return 0
        if args.command=="build-handoff":
            run_id=_positive_int(args.run_id,code="HANDOFF_ENVELOPE_INVALID"); run_attempt=_positive_int(args.run_attempt,code="HANDOFF_ENVELOPE_INVALID"); pr_number=_positive_int(args.pr_number,code="HANDOFF_ENVELOPE_INVALID"); qualification_exit_code=_exit_code(args.qualification_exit_code)
            anchor=load_and_verify_promotion_record(args.promotion_record); ctx=HandoffContext(run_id,run_attempt,args.base_sha,pr_number,args.head_repository,args.head_sha); env=build_handoff_envelope(args.receipt,ctx,anchor,qualification_exit_code); args.envelope_path.write_text(json.dumps(env,ensure_ascii=False,sort_keys=True,separators=(",", ":")),encoding="utf-8"); _write(args.output_json,env); return 0
        if args.command=="verify-handoff":
            run_id=_positive_int(args.run_id,code="HANDOFF_ENVELOPE_INVALID"); run_attempt=_positive_int(args.run_attempt,code="HANDOFF_ENVELOPE_INVALID"); pr_number=_positive_int(args.pr_number,code="HANDOFF_ENVELOPE_INVALID")
            anchor=load_and_verify_promotion_record(args.promotion_record); ctx=HandoffContext(run_id,run_attempt,args.base_sha,pr_number,args.head_repository,args.head_sha); receipt=verifw_handoff_directory(args.directory,ctx,anchor); _write(args.output_json,{"verified":True,"qualified":receipt.get("qualified")}); return 0
        if args.command=="decision":
            qualification_exit_code=_exit_code(args.qualification_exit_code); receipt_emitted=_bool_text(args.receipt_emitted)
            decision=reduce_decision(qualify_job_result=args.qualify_job_result,qualification_exit_code=qualification_exit_code,receipt_emitted=receipt_emitted,handoff_job_result=args.handoff_job_result); _write(args.output_json,asdict(decision)); return 0 if decision.success else 1
    except ControlPlaneError as exc:
        _write(args.output_json,{"success":False,"failure_code":exc.code}); return 2
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        _write(args.output_json,{"success":false,"failure_code":"CONTROL_PLANE_OR_INVOCATION_ERROR"}); return 2
    return 2

if __name__=="__main__": raise SystemExit(main())
