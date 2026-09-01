-- CEW OAR G4 — Arena-style atomic revision append + governed MVCC snapshot read
-- Runtime audit only: this migration grants no canonical, structural,
-- classification or engineering authority.

create extension if not exists pgcrypto;

create table if not exists public.cew_oar_region_revision_heads (
  binding_id text not null,
  support_id text not null,
  current_proposal_decision_id text,
  state text not null check (state in ('UNBOUND','PROPOSED','GEOMETRY_CONFIRMED')),
  updated_at timestamptz not null default clock_timestamp(),
  primary key (binding_id, support_id)
);

create or replace function public.cew_oar_append_region_receipt_v1(p_receipt jsonb)
returns table(receipt_json jsonb, receipt_sha256 text)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_binding_id text := nullif(trim(p_receipt->>'binding_id'), '');
  v_support_id text := nullif(trim(p_receipt->>'support_id'), '');
  v_decision_id text := nullif(trim(p_receipt->>'decision_id'), '');
  v_action text := p_receipt->>'action';
  v_expected text := nullif(trim(p_receipt->>'base_proposal_decision_id'), '');
  v_current text;
  v_state text;
  v_commit_time timestamptz;
  v_committed jsonb;
  v_digest text;
begin
  if p_receipt is null
     or p_receipt->>'receipt_type' is distinct from 'CEW_OAR_REGION_GEOMETRY_RECEIPT_v1'
     or v_binding_id is null or v_support_id is null or v_decision_id is null or v_expected is null
     or v_action not in ('PROPOSE_GEOMETRY','CONFIRM_GEOMETRY')
     or p_receipt->>'engineering_authority_effect' is distinct from 'NONE'
     or p_receipt->'canonical_write_authorized' is distinct from 'false'::jsonb
     or p_receipt->'structural_identity_authorized' is distinct from 'false'::jsonb
     or p_receipt->'oar_human_confirmation' is distinct from 'false'::jsonb then
    raise exception 'OAR_REGION_ATOMIC_CONTRACT_VIOLATION' using errcode='23514';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(v_binding_id || ':' || v_support_id, 0));

  select head.current_proposal_decision_id, head.state
    into v_current, v_state
  from public.cew_oar_region_revision_heads head
  where head.binding_id=v_binding_id and head.support_id=v_support_id;

  if not found then
    v_current := 'CEW_OAR_UNBOUND_REVISION:' || v_support_id;
    v_state := 'UNBOUND';
  end if;

  if v_action='PROPOSE_GEOMETRY' then
    if v_state='GEOMETRY_CONFIRMED' then
      raise exception 'OAR_REGION_GEOMETRY_ALREADY_CONFIRMED' using errcode='23514';
    end if;
  elsif v_state <> 'PROPOSED' then
    raise exception 'OAR_REGION_CONFIRMATION_REQUIRES_CURRENT_PROPOSAL' using errcode='23514';
  end if;

  if v_expected is distinct from v_current then
    raise exception 'OAR_REGION_REVISION_CONFLICT' using errcode='40001';
  end if;

  v_commit_time := clock_timestamp();
  v_committed := jsonb_set(p_receipt, '{timestamp}', to_jsonb(v_commit_time::text), true);
  v_digest := encode(digest(convert_to(v_committed::text, 'UTF8'), 'sha256'), 'hex');

  insert into public.cew_human_receipt_audit
    (decision_id, task_id, residual_id, receipt_sha256, receipt_json,
     authority, canonical_write, submitted_at)
  values
    (v_decision_id, v_committed->>'task_id', v_committed->>'residual_id', v_digest,
     v_committed, 'RUNTIME_AUDIT_ONLY', false, v_commit_time);

  if v_action='PROPOSE_GEOMETRY' then
    insert into public.cew_oar_region_revision_heads
      (binding_id, support_id, current_proposal_decision_id, state, updated_at)
    values (v_binding_id, v_support_id, v_decision_id, 'PROPOSED', v_commit_time)
    on conflict (binding_id, support_id) do update set
      current_proposal_decision_id=excluded.current_proposal_decision_id,
      state='PROPOSED', updated_at=excluded.updated_at;
  else
    update public.cew_oar_region_revision_heads set
      state='GEOMETRY_CONFIRMED', updated_at=v_commit_time
    where binding_id=v_binding_id and support_id=v_support_id;
  end if;

  receipt_json := v_committed;
  receipt_sha256 := v_digest;
  return next;
end;
$$;

-- Upgrade-safe return-type transition. Earlier revisions of this governed
-- migration created the zero-argument RPC as RETURNS TABLE(receipt_json jsonb).
-- PostgreSQL cannot change a function return type with CREATE OR REPLACE, so the
-- old signature must be removed before the scalar-jsonb contract is recreated.
-- This RPC is runtime audit read-only and carries no engineering authority.
drop function if exists public.cew_oar_read_region_receipts_v1();

-- One RPC invocation is one PostgreSQL statement/MVCC snapshot. The complete
-- receipt set is aggregated into ONE jsonb scalar before crossing PostgREST, so
-- API Max Rows cannot truncate individual OAR receipts. receipt_count gives the
-- client an independent fail-closed completeness check.
create function public.cew_oar_read_region_receipts_v1()
returns jsonb
language sql
stable
security definer
set search_path = public, pg_temp
as $$
  select jsonb_build_object(
    'schema_version', '1.0',
    'snapshot', 'SERVER_MVCC_SINGLE_JSON_VALUE',
    'receipt_count', count(*),
    'receipts', coalesce(
      jsonb_agg(a.receipt_json order by a.submitted_at asc nulls last, a.decision_id asc),
      '[]'::jsonb
    ),
    'authority', 'RUNTIME_AUDIT_READ_ONLY',
    'canonical_write', false,
    'engineering_authority_effect', 'NONE'
  )
  from public.cew_human_receipt_audit a
  where a.receipt_json->>'receipt_type' = 'CEW_OAR_REGION_GEOMETRY_RECEIPT_v1'
$$;

revoke all on function public.cew_oar_append_region_receipt_v1(jsonb) from public;
revoke all on function public.cew_oar_read_region_receipts_v1() from public;
grant execute on function public.cew_oar_append_region_receipt_v1(jsonb) to service_role;
grant execute on function public.cew_oar_read_region_receipts_v1() to service_role;
