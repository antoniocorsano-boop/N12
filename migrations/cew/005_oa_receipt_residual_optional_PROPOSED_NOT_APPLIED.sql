-- CEW OA / Neon audit compatibility migration
-- STATUS: PROPOSED_NOT_APPLIED
-- Authority effect: NONE
-- Canonical write authority: false
--
-- Context
-- -------
-- public.cew_human_receipt_audit is a shared append-only audit ledger.
-- Historical ERW/F7 receipts carry a residual_id because they belong to a
-- residual-resolution task. OA governed receipts belong to OBJECT_ACQUISITION
-- and intentionally do not fabricate an ERW residual identity.
--
-- Therefore the physical audit table must permit residual_id = NULL while the
-- ERW application contract continues to require a real residual_id for ERW/F7
-- receipt types.
--
-- This migration does not create engineering authority, canonical writes,
-- structural identity, or project-material readiness.

BEGIN;

ALTER TABLE public.cew_human_receipt_audit
  ALTER COLUMN residual_id DROP NOT NULL;

COMMIT;

-- Post-apply verification (read only):
-- SELECT is_nullable
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND table_name = 'cew_human_receipt_audit'
--   AND column_name = 'residual_id';
-- Expected: YES
