-- CEW OAR G4 — display-asset binding + complete receipt-governance patch
-- Apply after sql/CEW_OAR_G4_ATOMIC_APPEND_v1.sql.
-- The atomic append/replay RPCs call this validator by its stable function name,
-- therefore this patch is the effective server-side predicate for every OAR write
-- after the governed provisioning sequence is complete.
-- It grants no canonical, structural, classification or engineering authority.

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
  v_x numeric;
  v_y numeric;
  v_w numeric;
  v_h numeric;
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
  if p_receipt->>'derived_asset_id' is distinct from 'CEW-N12-ASSET-TAV05S-P001-OAR-300DPI' then
    raise exception 'OAR_REGION_GOVERNED_FIELD_MISMATCH_DERIVED_ASSET_ID' using errcode='23514';
  end if;
  if p_receipt->>'page_transform_id' is distinct from 'CEW-N12-XFORM-TAV05S-P001-OAR' then
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

  -- Geometry is part of the same atomic receipt contract. Validate JSON shape
  -- before numeric casts so malformed input fails with governed markers rather
  -- than reaching the append/head mutation or surfacing backend cast errors.
  if jsonb_typeof(p_receipt->'bbox') is distinct from 'object' then
    raise exception 'OAR_REGION_BBOX_REQUIRED' using errcode='23514';
  end if;
  if jsonb_typeof(p_receipt->'bbox'->'x') is distinct from 'number'
     or jsonb_typeof(p_receipt->'bbox'->'y') is distinct from 'number'
     or jsonb_typeof(p_receipt->'bbox'->'w') is distinct from 'number'
     or jsonb_typeof(p_receipt->'bbox'->'h') is distinct from 'number' then
    raise exception 'OAR_REGION_BBOX_INVALID' using errcode='23514';
  end if;

  v_x := (p_receipt->'bbox'->>'x')::numeric;
  v_y := (p_receipt->'bbox'->>'y')::numeric;
  v_w := (p_receipt->'bbox'->>'w')::numeric;
  v_h := (p_receipt->'bbox'->>'h')::numeric;

  if v_x < 0 or v_x > 1 or v_y < 0 or v_y > 1 or v_w < 0 or v_w > 1 or v_h < 0 or v_h > 1 then
    raise exception 'OAR_REGION_BBOX_OUT_OF_RANGE' using errcode='23514';
  end if;
  if v_w <= 0 or v_h <= 0 then
    raise exception 'OAR_REGION_BBOX_EMPTY' using errcode='23514';
  end if;
  if v_x + v_w > 1 or v_y + v_h > 1 then
    raise exception 'OAR_REGION_BBOX_EXCEEDS_PAGE' using errcode='23514';
  end if;
end;
$$;

-- Effective atomic writer. The confirmation bbox is compared to the immutable
-- proposal receipt under the same support advisory lock and before any audit
-- insert or revision-head mutation. A service-role caller therefore cannot
-- confirm a proposal ID while substituting different valid normalized geometry.
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
  v_current_proposal jsonb;
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

  if v_action='CONFIRM_GEOMETRY' then
    select a.receipt_json
      into v_current_proposal
    from public.cew_human_receipt_audit a
    where a.decision_id=v_current
      and a.receipt_json->>'receipt_type'='CEW_OAR_REGION_GEOMETRY_RECEIPT_v1'
      and a.receipt_json->>'binding_id'=v_binding_id
      and a.receipt_json->>'support_id'=v_support_id
      and a.receipt_json->>'action'='PROPOSE_GEOMETRY'
    limit 1;

    if not found then
      raise exception 'OAR_REGION_BASE_PROPOSAL_NOT_FOUND' using errcode='23514';
    end if;

    perform public.cew_oar_validate_g4_receipt_v1(v_current_proposal, v_binding_id, v_support_id);

    if p_receipt->'bbox' is distinct from v_current_proposal->'bbox' then
      raise exception 'OAR_REGION_CONFIRMATION_BBOX_MISMATCH' using errcode='23514';
    end if;
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

revoke all on function public.cew_oar_validate_g4_receipt_v1(jsonb,text,text) from public;
revoke all on function public.cew_oar_append_region_receipt_v1(jsonb) from public;
grant execute on function public.cew_oar_append_region_receipt_v1(jsonb) to service_role;
