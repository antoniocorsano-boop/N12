-- CEW B1.6 PREPARATION ONLY — DO NOT APPLY TO PRODUCTION YET.
-- Product workflow storage only. This table is not the F2 EvidenceRegion authority.

create table if not exists public.cew_evidence_region_candidate_audit (
    candidate_id text primary key,
    source_version_id text not null,
    page_id text not null,
    geometry_type text not null check (geometry_type = 'BBOX'),
    coordinate_space text not null check (coordinate_space = 'NORMALIZED_0_1'),
    x double precision not null check (x >= 0 and x <= 1),
    y double precision not null check (y >= 0 and y <= 1),
    width double precision not null check (width > 0 and width <= 1),
    height double precision not null check (height > 0 and height <= 1),
    author_type text not null check (author_type in ('HUMAN','MACHINE_PROPOSAL')),
    purpose text not null,
    human_note text,
    state text not null check (state in ('DRAFT','PROPOSED','REVIEW_REQUIRED','REJECTED','READY_FOR_F2_PROMOTION_REVIEW','SUPERSEDED')),
    receipt_json jsonb not null,
    authority text not null default 'PRODUCT_AUDIT_ONLY' check (authority = 'PRODUCT_AUDIT_ONLY'),
    canonical_write boolean not null default false check (canonical_write = false),
    created_at timestamptz not null,
    stored_at timestamptz not null default now(),
    check (x + width <= 1.000001),
    check (y + height <= 1.000001)
);

-- Intended application role policy when this migration is separately authorized:
-- GRANT SELECT, INSERT ON public.cew_evidence_region_candidate_audit TO cew_audit_writer;
-- REVOKE UPDATE, DELETE, TRUNCATE ON public.cew_evidence_region_candidate_audit FROM cew_audit_writer;
