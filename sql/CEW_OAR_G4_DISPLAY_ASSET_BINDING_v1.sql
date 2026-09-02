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

revoke all on function public.cew_oar_validate_g4_receipt_v1(jsonb,text,text) from public;
