import crypto from "node:crypto";
import { getDatabase } from "@netlify/database";

const SAFE_DECISION_ID = /^[A-Za-z0-9._-]+$/;
const REQUIRED = new Set([
  "decision_id",
  "task_id",
  "residual_id",
  "receipt_sha256",
  "receipt_json",
  "authority",
  "canonical_write",
  "submitted_at",
]);
const MAX_GOVERNED_READ_RECEIPTS = 500;
const MAX_GOVERNED_READ_PROBE = MAX_GOVERNED_READ_RECEIPTS + 1;
const OAR_RECEIPT_TYPE = "CEW_OAR_REGION_GEOMETRY_RECEIPT_v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function response(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function rowsOf(result) {
  if (Array.isArray(result)) return result;
  if (Array.isArray(result?.rows)) return result.rows;
  return [];
}

async function governedRead(req, db) {
  const url = new URL(req.url);
  const receiptType = String(url.searchParams.get("receipt_type") || "").trim();
  const rawLimit = Number.parseInt(url.searchParams.get("limit") || String(MAX_GOVERNED_READ_RECEIPTS), 10);
  const rawOffset = Number.parseInt(url.searchParams.get("offset") || "0", 10);
  const oarMvccSnapshot = url.searchParams.get("snapshot") === "oar_mvcc";
  if (!receiptType || receiptType.length > 200) {
    return response(422, { state: "AUDIT_READ_REJECTED", reason: "RECEIPT_TYPE_INVALID" });
  }

  try {
    if (oarMvccSnapshot) {
      if (receiptType !== OAR_RECEIPT_TYPE) {
        return response(422, { state: "AUDIT_READ_REJECTED", reason: "OAR_MVCC_SNAPSHOT_RECEIPT_TYPE_INVALID" });
      }
      // One SQL statement = one PostgreSQL MVCC snapshot. The complete OAR set
      // is materialized before this request returns, so a transaction that commits
      // later cannot appear between client-side chunks of this response.
      const result = await db.sql`
        SELECT receipt_json
        FROM cew_human_receipt_audit
        WHERE receipt_json->>'receipt_type' = ${receiptType}
        ORDER BY submitted_at ASC NULLS LAST, decision_id ASC
      `;
      const rows = rowsOf(result);
      return response(200, {
        state: "AUDIT_READ_OK",
        receipts: rows.map((row) => row.receipt_json),
        snapshot: "SERVER_MVCC_SINGLE_QUERY",
        receipt_count: rows.length,
        authority: "RUNTIME_AUDIT_READ_ONLY",
        canonical_write: false,
        engineering_authority_effect: "NONE",
      });
    }

    if (!Number.isInteger(rawLimit) || rawLimit < 1 || rawLimit > MAX_GOVERNED_READ_PROBE) {
      return response(422, { state: "AUDIT_READ_REJECTED", reason: "READ_LIMIT_INVALID" });
    }
    if (!Number.isInteger(rawOffset) || rawOffset < 0) {
      return response(422, { state: "AUDIT_READ_REJECTED", reason: "READ_OFFSET_INVALID" });
    }
    const result = await db.sql`
      SELECT receipt_json
      FROM cew_human_receipt_audit
      WHERE receipt_json->>'receipt_type' = ${receiptType}
      ORDER BY submitted_at ASC NULLS LAST, decision_id ASC
      LIMIT ${rawLimit}
      OFFSET ${rawOffset}
    `;
    const rows = rowsOf(result);
    const overflowProbe = rawLimit === MAX_GOVERNED_READ_PROBE;
    if (overflowProbe && rows.length > MAX_GOVERNED_READ_RECEIPTS) {
      return response(409, {
        state: "AUDIT_READ_REJECTED",
        reason: "GOVERNED_READ_LIMIT_EXCEEDED",
        limit: MAX_GOVERNED_READ_RECEIPTS,
        authority: "RUNTIME_AUDIT_READ_ONLY",
        canonical_write: false,
        engineering_authority_effect: "NONE",
      });
    }
    return response(200, {
      state: "AUDIT_READ_OK",
      receipts: rows.map((row) => row.receipt_json),
      offset: rawOffset,
      limit: Math.min(rawLimit, MAX_GOVERNED_READ_RECEIPTS),
      overflow_probe: overflowProbe,
      snapshot: "LEGACY_OFFSET",
      authority: "RUNTIME_AUDIT_READ_ONLY",
      canonical_write: false,
      engineering_authority_effect: "NONE",
    });
  } catch (err) {
    console.error("CEW_AUDIT_DB_READ_ERROR", err);
    return response(503, { state: "AUDIT_READ_REJECTED", reason: "AUDIT_DATABASE_UNAVAILABLE" });
  }
}

async function atomicOarAppend(payload, db) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload) || payload.oar_atomic_transition !== true) {
    return null;
  }
  const receipt = payload.receipt_json;
  if (!receipt || typeof receipt !== "object" || Array.isArray(receipt) || receipt.receipt_type !== OAR_RECEIPT_TYPE) {
    return response(422, { state: "AUDIT_REJECTED", reason: "OAR_ATOMIC_RECEIPT_REQUIRED" });
  }
  const decisionId = String(receipt.decision_id || "");
  const bindingId = String(receipt.binding_id || "").trim();
  const supportId = String(receipt.support_id || "").trim();
  const expected = String(receipt.base_proposal_decision_id || "").trim();
  const action = String(receipt.action || "");
  if (!SAFE_DECISION_ID.test(decisionId) || !bindingId || !supportId || !expected || !["PROPOSE_GEOMETRY", "CONFIRM_GEOMETRY"].includes(action)) {
    return response(422, { state: "AUDIT_REJECTED", reason: "OAR_ATOMIC_CONTRACT_VIOLATION" });
  }
  if (receipt.canonical_write_authorized !== false || receipt.structural_identity_authorized !== false || receipt.oar_human_confirmation !== false || receipt.engineering_authority_effect !== "NONE") {
    return response(422, { state: "AUDIT_REJECTED", reason: "AUTHORITY_BOUNDARY_VIOLATION" });
  }

  try {
    await db.sql`CREATE EXTENSION IF NOT EXISTS pgcrypto`;
    await db.sql`
      CREATE TABLE IF NOT EXISTS cew_oar_region_revision_heads (
        binding_id text NOT NULL,
        support_id text NOT NULL,
        current_proposal_decision_id text,
        state text NOT NULL CHECK (state IN ('UNBOUND','PROPOSED','GEOMETRY_CONFIRMED')),
        updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        PRIMARY KEY (binding_id, support_id)
      )
    `;

    const initialAnchor = `CEW_OAR_UNBOUND_REVISION:${supportId}`;
    const result = await db.sql`
      WITH updated AS (
        UPDATE cew_oar_region_revision_heads h
        SET current_proposal_decision_id = CASE WHEN ${action} = 'PROPOSE_GEOMETRY' THEN ${decisionId} ELSE h.current_proposal_decision_id END,
            state = CASE WHEN ${action} = 'PROPOSE_GEOMETRY' THEN 'PROPOSED' ELSE 'GEOMETRY_CONFIRMED' END,
            updated_at = clock_timestamp()
        WHERE h.binding_id = ${bindingId}
          AND h.support_id = ${supportId}
          AND h.current_proposal_decision_id = ${expected}
          AND ((${action} = 'PROPOSE_GEOMETRY' AND h.state = 'PROPOSED')
               OR (${action} = 'CONFIRM_GEOMETRY' AND h.state = 'PROPOSED'))
        RETURNING h.binding_id
      ),
      inserted AS (
        INSERT INTO cew_oar_region_revision_heads
          (binding_id, support_id, current_proposal_decision_id, state, updated_at)
        SELECT ${bindingId}, ${supportId}, ${decisionId}, 'PROPOSED', clock_timestamp()
        WHERE ${action} = 'PROPOSE_GEOMETRY'
          AND ${expected} = ${initialAnchor}
          AND NOT EXISTS (SELECT 1 FROM cew_oar_region_revision_heads h WHERE h.binding_id=${bindingId} AND h.support_id=${supportId})
        ON CONFLICT (binding_id, support_id) DO NOTHING
        RETURNING binding_id
      ),
      transition AS (
        SELECT binding_id FROM updated UNION ALL SELECT binding_id FROM inserted
      ),
      committed AS (
        SELECT jsonb_set(${JSON.stringify(receipt)}::jsonb, '{timestamp}', to_jsonb(clock_timestamp()::text), true) AS receipt_json
        FROM transition
        LIMIT 1
      ),
      stored AS (
        INSERT INTO cew_human_receipt_audit
          (decision_id, task_id, residual_id, receipt_sha256, receipt_json, authority, canonical_write, submitted_at)
        SELECT ${decisionId}, receipt_json->>'task_id', receipt_json->>'residual_id',
               encode(digest(convert_to(receipt_json::text, 'UTF8'), 'sha256'), 'hex'),
               receipt_json, 'RUNTIME_AUDIT_ONLY', false, (receipt_json->>'timestamp')::timestamptz
        FROM committed
        RETURNING receipt_json, receipt_sha256
      )
      SELECT receipt_json, receipt_sha256 FROM stored
    `;
    const rows = rowsOf(result);
    if (rows.length !== 1) {
      return response(409, { state: "AUDIT_REJECTED", reason: "OAR_REGION_REVISION_CONFLICT" });
    }
    return response(201, {
      state: "AUDIT_STORED",
      receipt_json: rows[0].receipt_json,
      runtime_receipt_id: decisionId,
      sha256: rows[0].receipt_sha256,
      atomic_revision: true,
      authority: "RUNTIME_AUDIT_ONLY",
      canonical_write: false,
    });
  } catch (err) {
    if (err?.code === "23505" || String(err?.message || "").toLowerCase().includes("duplicate")) {
      return response(409, { state: "AUDIT_REJECTED", reason: "DUPLICATE_DECISION_ID" });
    }
    console.error("CEW_OAR_ATOMIC_DB_ERROR", err);
    return response(503, { state: "AUDIT_REJECTED", reason: "AUDIT_DATABASE_UNAVAILABLE" });
  }
}

async function appendReceipt(payload, db) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return response(400, { state: "AUDIT_REJECTED", reason: "JSON_OBJECT_REQUIRED" });
  }
  const keys = Object.keys(payload);
  if (keys.length !== REQUIRED.size || keys.some((k) => !REQUIRED.has(k))) {
    return response(422, { state: "AUDIT_REJECTED", reason: "AUDIT_ENVELOPE_CONTRACT_VIOLATION" });
  }
  if (!SAFE_DECISION_ID.test(String(payload.decision_id || ""))) {
    return response(422, { state: "AUDIT_REJECTED", reason: "INVALID_DECISION_ID" });
  }
  if (payload.authority !== "RUNTIME_AUDIT_ONLY" || payload.canonical_write !== false) {
    return response(422, { state: "AUDIT_REJECTED", reason: "AUTHORITY_BOUNDARY_VIOLATION" });
  }
  const raw = stable(payload.receipt_json);
  const digest = crypto.createHash("sha256").update(raw, "utf8").digest("hex");
  if (digest !== payload.receipt_sha256) {
    return response(422, { state: "AUDIT_REJECTED", reason: "RECEIPT_DIGEST_MISMATCH" });
  }
  if (String(payload.receipt_json?.decision_id || "") !== String(payload.decision_id)) {
    return response(422, { state: "AUDIT_REJECTED", reason: "DECISION_ID_MISMATCH" });
  }

  try {
    await db.sql`
      INSERT INTO cew_human_receipt_audit
        (decision_id, task_id, residual_id, receipt_sha256, receipt_json, authority, canonical_write, submitted_at)
      VALUES
        (${payload.decision_id}, ${payload.task_id}, ${payload.residual_id}, ${payload.receipt_sha256}, ${JSON.stringify(payload.receipt_json)}::jsonb, ${payload.authority}, ${payload.canonical_write}, ${payload.submitted_at})
    `;
  } catch (err) {
    if (err?.code === "23505" || String(err?.message || "").toLowerCase().includes("duplicate")) {
      return response(409, { state: "AUDIT_REJECTED", reason: "DUPLICATE_DECISION_ID" });
    }
    console.error("CEW_AUDIT_DB_ERROR", err);
    return response(503, { state: "AUDIT_REJECTED", reason: "AUDIT_DATABASE_UNAVAILABLE" });
  }

  return response(201, {
    state: "AUDIT_STORED",
    runtime_receipt_id: payload.decision_id,
    sha256: payload.receipt_sha256,
    authority: "RUNTIME_AUDIT_ONLY",
    canonical_write: false,
  });
}

export default async (req) => {
  const secret = process.env.CEW_AUDIT_SHARED_SECRET || "";
  const auth = req.headers.get("authorization") || "";
  if (!secret || auth !== `Bearer ${secret}`) {
    return response(401, { state: "AUDIT_REJECTED", reason: "UNAUTHORIZED" });
  }

  const db = getDatabase();
  if (req.method === "GET") return governedRead(req, db);
  if (req.method === "POST") {
    let payload;
    try {
      payload = await req.json();
    } catch {
      return response(400, { state: "AUDIT_REJECTED", reason: "INVALID_JSON" });
    }
    const atomic = await atomicOarAppend(payload, db);
    if (atomic) return atomic;
    return appendReceipt(payload, db);
  }
  return response(405, { state: "AUDIT_REJECTED", reason: "METHOD_NOT_ALLOWED" });
};

export const config = {
  path: "/api/cew-audit",
};
