CREATE TABLE IF NOT EXISTS cew_human_receipt_audit (
  decision_id text PRIMARY KEY,
  task_id text NOT NULL,
  residual_id text NOT NULL,
  receipt_sha256 text NOT NULL CHECK (receipt_sha256 ~ '^[0-9a-f]{64}$'),
  receipt_json jsonb NOT NULL,
  authority text NOT NULL CHECK (authority = 'RUNTIME_AUDIT_ONLY'),
  canonical_write boolean NOT NULL DEFAULT false CHECK (canonical_write = false),
  submitted_at timestamptz,
  stored_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION cew_forbid_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'CEW human receipt audit is append-only';
END;
$$;

DROP TRIGGER IF EXISTS cew_human_receipt_audit_no_update_delete ON cew_human_receipt_audit;
CREATE TRIGGER cew_human_receipt_audit_no_update_delete
BEFORE UPDATE OR DELETE ON cew_human_receipt_audit
FOR EACH ROW EXECUTE FUNCTION cew_forbid_audit_mutation();

DROP TRIGGER IF EXISTS cew_human_receipt_audit_no_truncate ON cew_human_receipt_audit;
CREATE TRIGGER cew_human_receipt_audit_no_truncate
BEFORE TRUNCATE ON cew_human_receipt_audit
FOR EACH STATEMENT EXECUTE FUNCTION cew_forbid_audit_mutation();
