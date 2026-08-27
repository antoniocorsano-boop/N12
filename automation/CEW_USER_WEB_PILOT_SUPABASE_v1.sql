create table if not exists public.cew_human_receipt_audit (
  decision_id text primary key,
  task_id text not null,
  residual_id text not null,
  receipt_sha256 text not null check (length(receipt_sha256) = 64),
  receipt_json jsonb not null,
  authority text not null default 'RUNTIME_AUDIT_ONLY' check (authority = 'RUNTIME_AUDIT_ONLY'),
  canonical_write boolean not null default false check (canonical_write = false),
  submitted_at timestamptz not null,
  stored_at timestamptz not null default now()
);

alter table public.cew_human_receipt_audit enable row level security;
revoke all on table public.cew_human_receipt_audit from anon, authenticated;

create or replace function public.cew_reject_receipt_audit_mutation()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  raise exception 'CEW receipt audit is append-only';
end;
$$;

drop trigger if exists cew_human_receipt_audit_no_update_delete on public.cew_human_receipt_audit;
create trigger cew_human_receipt_audit_no_update_delete
before update or delete on public.cew_human_receipt_audit
for each row execute function public.cew_reject_receipt_audit_mutation();

comment on table public.cew_human_receipt_audit is
'CEW runtime audit only. Human receipt persistence is append-only and never constitutes a canonical engineering write.';
