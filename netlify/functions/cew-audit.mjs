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
  if (!receiptType || receiptType.length > 200) {
    return response(422, { state: "AUDIT_READ_REJECTED", reason: "RECEIPT_TYPE_INVALID" });
  }
  if (!Number.isInteger(rawLimit) || rawLimit < 1 || rawLimit > MAX_GOVERNED_READ_PROBE) {
    return response(422, { state: "AUDIT_READ_REJECTED", reason: "READ_LIMIT_INVALID" });
  }
  if (!Number.isInteger(rawOffset) || rawOffset < 0) {
    return response(422, { state: "AUDIT_READ_REJECTED", reason: "READ_OFFSET_INVALID" });
  }
  try {
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
      authority: "RUNTIME_AUDIT_READ_ONLY",
      canonical_write: false,
      engineering_authority_effect: "NONE",
    });
  } catch (err) {
    console.error("CEW_AUDIT_DB_READ_ERROR", err);
    return response(503, { state: "AUDIT_READ_REJECTED", reason: "AUDIT_DATABASE_UNAVAILABLE" });
  }
}

async function appendReceipt(req, db) {
  let payload;
  try {
    payload = await req.json();
  } catch {
    return response(400, { state: "AUDIT_REJECTED", reason: "INVALID_JSON" });
  }
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
  if (req.method === "POST") return appendReceipt(req, db);
  return response(405, { state: "AUDIT_REJECTED", reason: "METHOD_NOT_ALLOWED" });
};

export const config = {
  path: "/api/cew-audit",
};