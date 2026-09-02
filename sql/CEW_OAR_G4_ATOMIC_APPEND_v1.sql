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

-- Single server-side governance predicate for this bounded G4/TAV-05S pilot.
-- It mirrors _validate_receipt_governance() in cew_oar_g4_region_binding.py so
-- replay/backfill and new atomic writes cannot accept a receipt that normal
-- Workbench reconstruction would reject.
create or replace function public.cew_oar_validate_g4_receipt_v1(
  p_receipt jsonb,
  p_binding_id text,
  p_support_id text
)
returns void
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
declare
  v_action text := p_receipt->>'action';
  v_expected_evidence text;
  v_expected_family text;
  v_family_map jsonb := '{
    "1":"COL-G4-40X40","2":"COL-G4-40X40","3":"COL-G4-40X40","4":"COL-G4-40X40",
    "5":"COL-G4-40X40","6":"COL-G4-40X40","7":"COL-G4-40X40","8":"COL-G4-40X40",
    "9":"COL-G4-40X40","10":"COL-G4-45X30","11":"COL-G4-45X30","12":"COL-G4-30X45",
    "13":"COL-G4-45X30","14":"COL-G4-45X30","15":"COL-G4-45X30","16":"COL-G4-40X40",
    "17":"COL-G4-40X40","18":"COL-G4-30X110","19":"COL-G4-40X40","20":"COL-G4-40X40",
    "21":"COL-G4-30X45","22":"COL-G4-30X45","22''":"COL-G4-40X40","23":"COL-G4-30X110",
    "24":"COL-G4-40X40","25":"COL-G4-40X40","26":"COL-G4-30X45","27":"COL-G4-40X40",
    "28":"COL-G4-40X40","29":"COL-G4-30X45","30":"COL-G4-110X30","31":"COL-G4-40X40",
    "32":"COL-G4-40X40","33":"COL-G4-40X40"
  }'::jsonb;
begin
  if p_receipt is null then
    raise exception 'OAR_REGION_RECEIPT_INVALID' using errcode='23514';
  end if;
  if p_receipt->>'receipt_type' is distinct from 'CEW_OAR_REGION_GEOMETRY_RECEIPT_v1' then
    raise exception 'OAR_REGION_RECEIPT_TYPE_INVALID' using errcode='23514';
  end if;
  if p_binding_id is distinct from 'OAR-G4-COLUMN-REGION-BINDING' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_BINDING_ID' using errcode='23514';
  end if;
  v_expected_family := v_family_map->>p_support_id;
  if v_expected_family is null then
    raise exception 'OAR_REGION_SUPPORT_NOT_IN_PILOT' using errcode='23514';
  end if;
  if v_action is null or v_action not in ('PROPOSE_GEOMETRY','CONFIRM_GEOMETRY') then
    raise exception 'OAR_REGION_ACTION_INVALID' using errcode='23514';
  end if;

  v_expected_evidence := 'EOBJ-G4-SUPPORT-' || p_support_id;

  if p_receipt->>'task_id' is distinct from 'OAR-G4-COLUMN-REGION-BINDING' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_TASK_ID' using errcode='23514';
  end if;
  if p_receipt->>'residual_id' is distinct from v_expected_evidence then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_RESIDUAL_ID' using errcode='23514';
  end if;
  if p_receipt->>'pilot_id' is distinct from 'OAR-PILOT-G4-COLUMNS' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_PILOT_ID' using errcode='23514';
  end if;
  if p_receipt->>'binding_id' is distinct from 'OAR-G4-COLUMN-REGION-BINDING' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_BINDING_ID' using errcode='23514';
  end if;
  if p_receipt->>'support_id' is distinct from p_support_id then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_SUPPORT_ID' using errcode='23514';
  end if;
  if p_receipt->>'evidence_object_id' is distinct from v_expected_evidence then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_EVIDENCE_OBJECT_ID' using errcode='23514';
  end if;
  if p_receipt->>'family_id' is distinct from v_expected_family then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_FAMILY_ID' using errcode='23514';
  end if;
  if p_receipt->>'source_version_id' is distinct from 'CEW-N12-SRC-TAV05S-V2143DBCF' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_SOURCE_VERSION_ID' using errcode='23514';
  end if;
  if p_receipt->>'page_id' is distinct from 'CEW-N12-PAGE-TAV05S-P001' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_PAGE_ID' using errcode='23514';
  end if;
  if p_receipt->>'derived_asset_id' is distinct from 'CEW-N12-ASSET-TAV05S-P001-300DPI' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_DERIVED_ASSET_ID' using errcode='23514';
  end if;
  if p_receipt->>'page_transform_id' is distinct from 'CEW-N12-XFORM-TAV05S-P001' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_PAGE_TRANSFORM_ID' using errcode='23514';
  end if;
  if p_receipt->>'coordinate_system' is distinct from 'NORMALIZED_0_1' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_COORDINATE_SYSTEM' using errcode='23514';
  end if;
  if (v_action='PROPOSE_GEOMETRY' and p_receipt->>'authority' is distinct from 'WORKING_GEOMETRY_ONLY')
     or (v_action='CONFIRM_GEOMETRY' and p_receipt->>'authority' is distinct from 'HUMAN_EVIDENCE_LOCALIZATION_ONLY') then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_AUTHORITY' using errcode='23514';
  end if;
  if p_receipt->'oar_human_confirmation' is distinct from 'false'::jsonb then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_OAR_HUMAN_CONFIRMATION' using errcode='23514';
  end if;
  if p_receipt->'structural_identity_authorized' is distinct from 'false'::jsonb then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_STRUCTURAL_IDENTITY_AUTHORIZED' using errcode='23514';
  end if;
  if p_receipt->'canonical_write_authorized' is distinct from 'false'::jsonb then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_CANONICAL_WRITE_AUTHORIZED' using errcode='23514';
  end if;
  if p_receipt->>'engineering_authority_effect' is distinct from 'NONE' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_ENGINEERING_AUTHORITY_EFFECT' using errcode='23514';
  end if;
  if p_receipt->'base_proposal_decision_id' is not null
     and p_receipt->'base_proposal_decision_id' <> 'null'::jsonb
     and nullif(trim(p_receipt->>'base_proposal_decision_id'), '') is null then
    raise exception 'OAR_REGION_BASE_PROPOSAL_DECISION_ID_INVALID' using errcode='23514';
  end if;
end;
$$;

-- Canonical backend replay for legacy pre-CAS receipt history. This function
-- mirrors the anchored-transition semantics of scripts/cew_oar_g4_region_binding.py:
-- replacement proposals advance the active revision, confirmations bound to an
-- older predecessor are stale/non-mutating, and malformed/divergent history
-- fails closed instead of manufacturing a revision head.
create or replace function public.cew_oar_replay_region_head_v1(
  p_binding_id text,
  p_support_id text
)
returns table(
  current_proposal_decision_id text,
  state text,
  updated_at timestamptz,
  receipt_count bigint,
  stale_transition_count bigint
)
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
declare
  r record;
  v_receipt jsonb;
  v_decision_id text;
  v_action text;
  v_anchor text;
  v_bbox jsonb;
  v_current_id text := null;
  v_current_bbox jsonb := null;
  v_confirmed jsonb := null;
  v_history jsonb := '{}'::jsonb;
  v_seen jsonb := '{}'::jsonb;
  v_initial_anchor text := 'CEW_OAR_UNBOUND_REVISION:' || p_support_id;
  v_has_initial_proposal boolean := false;
  v_last_transition timestamptz := null;
  v_count bigint := 0;
  v_stale bigint := 0;
  v_anchored jsonb;
  v_equivalent boolean;
begin
  if nullif(trim(p_binding_id), '') is null or nullif(trim(p_support_id), '') is null then
    raise exception 'OAR_REGION_REPLAY_SCOPE_REQUIRED' using errcode='23514';
  end if;

  if exists (
    select 1
    from public.cew_human_receipt_audit a
    where a.receipt_json->>'receipt_type'='CEW_OAR_REGION_GEOMETRY_RECEIPT_v1'
      and a.receipt_json->>'binding_id'=p_binding_id
      and a.receipt_json->>'support_id'=p_support_id
      and coalesce(a.receipt_json->>'timestamp','') !~ '(Z|[+-][0-9]{2}:[0-9]{2})$'
  ) then
    raise exception 'OAR_REGION_TIMESTAMP_TIMEZONE_REQUIRED' using errcode='23514';
  end if;

  for r in
    select a.decision_id, a.receipt_json,
           (a.receipt_json->>'timestamp')::timestamptz as governed_timestamp
    from public.cew_human_receipt_audit a
    where a.receipt_json->>'receipt_type'='CEW_OAR_REGION_GEOMETRY_RECEIPT_v1'
      and a.receipt_json->>'binding_id'=p_binding_id
      and a.receipt_json->>'support_id'=p_support_id
    order by (a.receipt_json->>'timestamp')::timestamptz asc, a.decision_id asc
  loop
    v_receipt := r.receipt_json;
    perform public.cew_oar_validate_g4_receipt_v1(v_receipt, p_binding_id, p_support_id);
    v_count := v_count + 1;
    v_decision_id := nullif(trim(v_receipt->>'decision_id'), '');
    v_action := v_receipt->>'action';
    v_anchor := case
      when v_receipt->'base_proposal_decision_id' is null or v_receipt->'base_proposal_decision_id'='null'::jsonb then null
      else nullif(trim(v_receipt->>'base_proposal_decision_id'), '')
    end;
    v_bbox := v_receipt->'bbox';

    if v_decision_id is null or v_decision_id like 'CEW_OAR_UNBOUND_REVISION:%' then
      raise exception 'OAR_REGION_DECISION_ID_INVALID' using errcode='23514';
    end if;
    if v_seen ? v_decision_id then
      raise exception 'OAR_REGION_DUPLICATE_DECISION_ID' using errcode='23514';
    end if;
    v_seen := v_seen || jsonb_build_object(v_decision_id, true);

    if jsonb_typeof(v_bbox) is distinct from 'object'
       or jsonb_typeof(v_bbox->'x') is distinct from 'number'
       or jsonb_typeof(v_bbox->'y') is distinct from 'number'
       or jsonb_typeof(v_bbox->'w') is distinct from 'number'
       or jsonb_typeof(v_bbox->'h') is distinct from 'number' then
      raise exception 'OAR_REGION_BBOX_INVALID' using errcode='23514';
    end if;
    if (v_bbox->>'x')::numeric < 0 or (v_bbox->>'x')::numeric > 1
       or (v_bbox->>'y')::numeric < 0 or (v_bbox->>'y')::numeric > 1
       or (v_bbox->>'w')::numeric <= 0 or (v_bbox->>'w')::numeric > 1
       or (v_bbox->>'h')::numeric <= 0 or (v_bbox->>'h')::numeric > 1
       or (v_bbox->>'x')::numeric + (v_bbox->>'w')::numeric > 1
       or (v_bbox->>'y')::numeric + (v_bbox->>'h')::numeric > 1 then
      raise exception 'OAR_REGION_BBOX_OUT_OF_RANGE' using errcode='23514';
    end if;

    if v_action='PROPOSE_GEOMETRY' then
      if v_confirmed is not null then
        if (v_anchor is not null and v_anchor = v_confirmed->>'base_proposal_decision_id')
           or (v_anchor = v_initial_anchor and v_has_initial_proposal) then
          v_stale := v_stale + 1;
          continue;
        end if;
        raise exception 'OAR_REGION_GEOMETRY_ALREADY_CONFIRMED' using errcode='23514';
      end if;

      if v_current_id is not null and v_anchor is not null and v_anchor <> v_current_id then
        v_stale := v_stale + 1;
        continue;
      end if;
      if v_current_id is null and v_anchor is not null then
        if v_anchor = v_initial_anchor then
          null;
        elsif v_history ? v_anchor then
          v_stale := v_stale + 1;
          continue;
        else
          raise exception 'OAR_REGION_BASE_PROPOSAL_NOT_FOUND' using errcode='23514';
        end if;
      end if;

      v_current_id := v_decision_id;
      v_current_bbox := v_bbox;
      v_history := v_history || jsonb_build_object(v_decision_id, v_receipt);
      if v_anchor = v_initial_anchor then
        v_has_initial_proposal := true;
      end if;
      v_last_transition := r.governed_timestamp;
      continue;
    end if;

    -- CONFIRM_GEOMETRY
    if v_confirmed is not null then
      v_equivalent :=
        (v_confirmed->>'support_id' is not distinct from v_receipt->>'support_id') and
        (v_confirmed->>'evidence_object_id' is not distinct from v_receipt->>'evidence_object_id') and
        (v_confirmed->>'family_id' is not distinct from v_receipt->>'family_id') and
        (v_confirmed->>'pilot_id' is not distinct from v_receipt->>'pilot_id') and
        (v_confirmed->>'binding_id' is not distinct from v_receipt->>'binding_id') and
        (v_confirmed->>'source_version_id' is not distinct from v_receipt->>'source_version_id') and
        (v_confirmed->>'page_id' is not distinct from v_receipt->>'page_id') and
        (v_confirmed->>'derived_asset_id' is not distinct from v_receipt->>'derived_asset_id') and
        (v_confirmed->>'page_transform_id' is not distinct from v_receipt->>'page_transform_id') and
        (v_confirmed->>'coordinate_system' is not distinct from v_receipt->>'coordinate_system') and
        (v_confirmed->>'base_proposal_decision_id' is not distinct from v_receipt->>'base_proposal_decision_id') and
        (v_confirmed->>'authority' is not distinct from v_receipt->>'authority') and
        (v_confirmed->'oar_human_confirmation' is not distinct from v_receipt->'oar_human_confirmation') and
        (v_confirmed->'structural_identity_authorized' is not distinct from v_receipt->'structural_identity_authorized') and
        (v_confirmed->'canonical_write_authorized' is not distinct from v_receipt->'canonical_write_authorized') and
        (v_confirmed->>'engineering_authority_effect' is not distinct from v_receipt->>'engineering_authority_effect') and
        (v_confirmed->'bbox' = v_bbox);
      if v_equivalent then
        continue;
      end if;
      v_anchored := case when v_anchor is null then null else v_history->v_anchor end;
      if v_anchored is not null and v_anchored->'bbox'=v_bbox then
        v_stale := v_stale + 1;
        continue;
      end if;
      raise exception 'OAR_REGION_GEOMETRY_ALREADY_CONFIRMED' using errcode='23514';
    end if;

    if v_current_id is null then
      raise exception 'OAR_REGION_CONFIRMATION_WITHOUT_PROPOSAL' using errcode='23514';
    end if;
    if v_anchor is not null and v_anchor <> v_current_id then
      v_anchored := v_history->v_anchor;
      if v_anchored is not null and v_anchored->'bbox'=v_bbox then
        v_stale := v_stale + 1;
        continue;
      end if;
      raise exception 'OAR_REGION_BASE_PROPOSAL_MISMATCH' using errcode='23514';
    end if;
    if v_bbox <> v_current_bbox then
      raise exception 'OAR_REGION_CONFIRMATION_BBOX_MISMATCH' using errcode='23514';
    end if;
    v_confirmed := v_receipt;
    v_last_transition := r.governed_timestamp;
  end loop;

  current_proposal_decision_id := coalesce(v_current_id, v_initial_anchor);
  state := case when v_confirmed is not null then 'GEOMETRY_CONFIRMED'
                when v_current_id is not null then 'PROPOSED'
                else 'UNBOUND' end;
  updated_at := v_last_transition;
  receipt_count := v_count;
  stale_transition_count := v_stale;
  return next;
end;
$$;

-- Upgrade/backfill boundary. Every missing head is produced by the replay above;
-- existing CAS-managed heads are never overwritten.
with legacy_supports as (
  select distinct
    a.receipt_json->>'binding_id' as binding_id,
    a.receipt_json->>'support_id' as support_id
  from public.cew_human_receipt_audit a
  where a.receipt_json->>'receipt_type'='CEW_OAR_REGION_GEOMETRY_RECEIPT_v1'
    and nullif(trim(a.receipt_json->>'binding_id'), '') is not null
    and nullif(trim(a.receipt_json->>'support_id'), '') is not null
), replayed as (
  select s.binding_id, s.support_id,
         r.current_proposal_decision_id, r.state, r.updated_at
  from legacy_supports s
  cross join lateral public.cew_oar_replay_region_head_v1(s.binding_id, s.support_id) r
)
insert into public.cew_oar_region_revision_heads
  (binding_id, support_id, current_proposal_decision_id, state, updated_at)
select binding_id, support_id, current_proposal_decision_id, state,
       coalesce(updated_at, clock_timestamp())
from replayed
where state <> 'UNBOUND'
on conflict (binding_id, support_id) do nothing;

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
  v_replay_updated_at timestamptz;
  v_commit_time timestamptz;
  v_committed jsonb;
  v_digest text;
begin
  if p_receipt is null
     or v_binding_id is null or v_support_id is null or v_decision_id is null or v_expected is null
     or v_action is null then
    raise exception 'OAR_REGION_ATOMIC_CONTRACT_VIOLATION' using errcode='23514';
  end if;

  perform public.cew_oar_validate_g4_receipt_v1(p_receipt, v_binding_id, v_support_id);

  perform pg_advisory_xact_lock(hashtextextended(v_binding_id || ':' || v_support_id, 0));

  select head.current_proposal_decision_id, head.state
    into v_current, v_state
  from public.cew_oar_region_revision_heads head
  where head.binding_id=v_binding_id and head.support_id=v_support_id;

  if not found then
    select r.current_proposal_decision_id, r.state, r.updated_at
      into v_current, v_state, v_replay_updated_at
    from public.cew_oar_replay_region_head_v1(v_binding_id, v_support_id) r;

    if v_state <> 'UNBOUND' then
      insert into public.cew_oar_region_revision_heads
        (binding_id, support_id, current_proposal_decision_id, state, updated_at)
      values (v_binding_id, v_support_id, v_current, v_state, coalesce(v_replay_updated_at, clock_timestamp()))
      on conflict (binding_id, support_id) do nothing;

      select head.current_proposal_decision_id, head.state
        into v_current, v_state
      from public.cew_oar_region_revision_heads head
      where head.binding_id=v_binding_id and head.support_id=v_support_id;
      if not found then
        raise exception 'OAR_REGION_LEGACY_HEAD_BACKFILL_FAILED' using errcode='40001';
      end if;
    end if;
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

-- Upgrade-safe return-type transition. Earlier revisions created the zero-arg
-- reader as RETURNS TABLE(receipt_json jsonb), which cannot be changed by
-- CREATE OR REPLACE.
drop function if exists public.cew_oar_read_region_receipts_v1();

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

revoke all on function public.cew_oar_validate_g4_receipt_v1(jsonb,text,text) from public;
revoke all on function public.cew_oar_replay_region_head_v1(text,text) from public;
revoke all on function public.cew_oar_append_region_receipt_v1(jsonb) from public;
revoke all on function public.cew_oar_read_region_receipts_v1() from public;
grant execute on function public.cew_oar_append_region_receipt_v1(jsonb) to service_role;
grant execute on function public.cew_oar_read_region_receipts_v1() to service_role;