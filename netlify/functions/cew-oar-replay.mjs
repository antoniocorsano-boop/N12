const OAR_RECEIPT_TYPE = "CEW_OAR_REGION_GEOMETRY_RECEIPT_v1";
const PROPOSAL_ACTION = "PROPOSE_GEOMETRY";
const CONFIRM_ACTION = "CONFIRM_GEOMETRY";
const UNBOUND_PREFIX = "CEW_OAR_UNBOUND_REVISION:";
const CONFIRM_EQUIVALENCE_FIELDS = [
  "support_id",
  "evidence_object_id",
  "family_id",
  "pilot_id",
  "binding_id",
  "source_version_id",
  "page_id",
  "derived_asset_id",
  "page_transform_id",
  "coordinate_system",
  "base_proposal_decision_id",
  "authority",
  "oar_human_confirmation",
  "structural_identity_authorized",
  "canonical_write_authorized",
  "engineering_authority_effect",
];

function fail(marker) {
  const err = new Error(marker);
  err.code = marker;
  throw err;
}

function timestampMicros(value) {
  const text = String(value || "");
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|([+-])(\d{2}):(\d{2}))$/);
  if (!match) fail("OAR_REGION_TIMESTAMP_TIMEZONE_REQUIRED");
  const [, yy, mo, dd, hh, mm, ss, fraction = "", zone, sign, offH = "00", offM = "00"] = match;
  const baseMs = Date.UTC(Number(yy), Number(mo) - 1, Number(dd), Number(hh), Number(mm), Number(ss));
  if (!Number.isFinite(baseMs)) fail("OAR_REGION_TIMESTAMP_INVALID");
  let micros = BigInt(baseMs) * 1000n + BigInt((fraction + "000000").slice(0, 6));
  if (zone !== "Z") {
    const offset = BigInt(Number(offH) * 60 + Number(offM)) * 60n * 1000000n;
    micros += sign === "+" ? -offset : offset;
  }
  return micros;
}

function textCompare(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}

function normalizeBbox(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) fail("OAR_REGION_BBOX_REQUIRED");
  const bbox = {};
  for (const key of ["x", "y", "w", "h"]) {
    const number = Number(value[key]);
    if (!Number.isFinite(number)) fail("OAR_REGION_BBOX_INVALID");
    bbox[key] = number;
  }
  if (Object.values(bbox).some((number) => number < 0 || number > 1)) fail("OAR_REGION_BBOX_OUT_OF_RANGE");
  if (bbox.w <= 0 || bbox.h <= 0) fail("OAR_REGION_BBOX_EMPTY");
  if (bbox.x + bbox.w > 1 || bbox.y + bbox.h > 1) fail("OAR_REGION_BBOX_EXCEEDS_PAGE");
  return bbox;
}

function bboxEqual(a, b) {
  return a && b && ["x", "y", "w", "h"].every((key) => Number(a[key]) === Number(b[key]));
}

function equivalentConfirmation(existing, receipt, bbox) {
  if (receipt.action !== CONFIRM_ACTION) return false;
  if (CONFIRM_EQUIVALENCE_FIELDS.some((key) => existing[key] !== receipt[key])) return false;
  return bboxEqual(existing.bbox, bbox);
}

function validateGovernance(receipt, bindingId, supportId) {
  if (!receipt || typeof receipt !== "object" || Array.isArray(receipt)) fail("OAR_REGION_RECEIPT_INVALID");
  if (receipt.receipt_type !== OAR_RECEIPT_TYPE) fail("OAR_REGION_RECEIPT_TYPE_INVALID");
  if (String(receipt.binding_id || "") !== bindingId || String(receipt.support_id || "") !== supportId) {
    fail("OAR_REGION_RECEIPT_SCOPE_MISMATCH");
  }
  if (![PROPOSAL_ACTION, CONFIRM_ACTION].includes(receipt.action)) fail("OAR_REGION_ACTION_INVALID");
  const expectedAuthority = receipt.action === PROPOSAL_ACTION ? "WORKING_GEOMETRY_ONLY" : "HUMAN_EVIDENCE_LOCALIZATION_ONLY";
  if (receipt.authority !== expectedAuthority || receipt.oar_human_confirmation !== false || receipt.structural_identity_authorized !== false || receipt.canonical_write_authorized !== false || receipt.engineering_authority_effect !== "NONE") {
    fail("OAR_REGION_GOVERNED_AUTHORITY_MISMATCH");
  }
  const decisionId = String(receipt.decision_id || "");
  if (!decisionId) fail("OAR_REGION_DECISION_ID_REQUIRED");
  if (decisionId.startsWith(UNBOUND_PREFIX)) fail("OAR_REGION_DECISION_ID_RESERVED");
  const anchor = receipt.base_proposal_decision_id;
  if (anchor !== null && anchor !== undefined && !String(anchor).trim()) fail("OAR_REGION_BASE_PROPOSAL_DECISION_ID_INVALID");
  timestampMicros(receipt.timestamp);
  return normalizeBbox(receipt.bbox);
}

export function replayOarHead(receipts, bindingId, supportId) {
  bindingId = String(bindingId || "").trim();
  supportId = String(supportId || "").trim();
  if (!bindingId || !supportId) fail("OAR_REGION_REPLAY_SCOPE_REQUIRED");
  const initialAnchor = `${UNBOUND_PREFIX}${supportId}`;
  const ordered = [...receipts]
    .filter((receipt) => receipt?.receipt_type === OAR_RECEIPT_TYPE && String(receipt.binding_id || "") === bindingId && String(receipt.support_id || "") === supportId)
    .sort((a, b) => {
      const ta = timestampMicros(a.timestamp);
      const tb = timestampMicros(b.timestamp);
      if (ta < tb) return -1;
      if (ta > tb) return 1;
      return textCompare(String(a.decision_id || ""), String(b.decision_id || ""));
    });

  const history = new Map();
  const seen = new Set();
  let latestProposal = null;
  let confirmed = null;
  let hasInitialProposal = false;
  let lastTransitionAt = null;
  let staleTransitionCount = 0;

  for (const receipt of ordered) {
    const bbox = validateGovernance(receipt, bindingId, supportId);
    const decisionId = String(receipt.decision_id);
    if (seen.has(decisionId)) fail("OAR_REGION_DUPLICATE_DECISION_ID");
    seen.add(decisionId);
    const anchor = receipt.base_proposal_decision_id == null ? null : String(receipt.base_proposal_decision_id);

    if (receipt.action === PROPOSAL_ACTION) {
      if (confirmed) {
        const sameConfirmedBase = anchor !== null && anchor === confirmed.base_proposal_decision_id;
        const sameInitialBase = anchor === initialAnchor && hasInitialProposal;
        if (sameConfirmedBase || sameInitialBase) {
          staleTransitionCount += 1;
          continue;
        }
        fail("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED");
      }
      if (latestProposal && anchor !== null && anchor !== latestProposal.decision_id) {
        staleTransitionCount += 1;
        continue;
      }
      if (!latestProposal && anchor !== null) {
        if (anchor === initialAnchor) {
          // governed initial revision
        } else if (history.has(anchor)) {
          staleTransitionCount += 1;
          continue;
        } else {
          fail("OAR_REGION_BASE_PROPOSAL_NOT_FOUND");
        }
      }
      latestProposal = { ...receipt, bbox };
      history.set(decisionId, latestProposal);
      if (anchor === initialAnchor) hasInitialProposal = true;
      lastTransitionAt = receipt.timestamp;
      continue;
    }

    if (confirmed) {
      if (equivalentConfirmation(confirmed, receipt, bbox)) continue;
      const anchored = anchor === null ? null : history.get(anchor);
      if (anchored && bboxEqual(anchored.bbox, bbox)) {
        staleTransitionCount += 1;
        continue;
      }
      fail("OAR_REGION_GEOMETRY_ALREADY_CONFIRMED");
    }
    if (!latestProposal) fail("OAR_REGION_CONFIRMATION_WITHOUT_PROPOSAL");
    if (anchor !== null && anchor !== latestProposal.decision_id) {
      const anchored = history.get(anchor);
      if (anchored && bboxEqual(anchored.bbox, bbox)) {
        staleTransitionCount += 1;
        continue;
      }
      fail("OAR_REGION_BASE_PROPOSAL_MISMATCH");
    }
    if (!bboxEqual(bbox, latestProposal.bbox)) fail("OAR_REGION_CONFIRMATION_BBOX_MISMATCH");
    confirmed = { ...receipt, bbox };
    lastTransitionAt = receipt.timestamp;
  }

  return {
    binding_id: bindingId,
    support_id: supportId,
    current_proposal_decision_id: latestProposal ? latestProposal.decision_id : initialAnchor,
    state: confirmed ? "GEOMETRY_CONFIRMED" : latestProposal ? "PROPOSED" : "UNBOUND",
    receipt_count: ordered.length,
    stale_transition_count: staleTransitionCount,
    updated_at: lastTransitionAt,
    authority: "RUNTIME_REVISION_PROJECTION_ONLY",
    canonical_write_authorized: false,
    structural_identity_authorized: false,
    oar_human_confirmation: false,
    engineering_authority_effect: "NONE",
  };
}
