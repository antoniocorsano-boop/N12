import { useState } from "react";
import type { ValidationQueue as VQType, ValidationItem } from "../read-model/types";

export interface ValidationDecision {
  propertyId: string;
  candidateId: string | null;
  candidateValue: string | number | null;
  reviewerDecision: "ACCEPT" | "REJECT" | "DEFER";
  evidenceRefs: string[];
  previousState: string;
  resultingState: string;
  timestamp: string;
  reviewerNote?: string;
}

const RESOLUTION_COLORS: Record<string, string> = {
  UNKNOWN: "ev--nd",
  CANDIDATES: "ev--inf",
  CONSISTENT: "ev--ris",
  CONFLICT: "ev--nd",
  PROPOSED: "ev--ris",
  VALIDATED: "ev--doc",
  REJECTED: "ev--nd",
  IMPOSSIBLE: "ev--nd",
  NOT_APPLICABLE: "",
};

function StatsBar({ stats, total }: { stats: VQType["stats"]; total: number }) {
  return (
    <div className="vq__stats">
      <div className="vq__stat vq__stat--ok">
        <span className="vq__stat-value">{stats.validated}</span>
        <span className="vq__stat-label">Validate</span>
      </div>
      <div className="vq__stat vq__stat--warn">
        <span className="vq__stat-value">{stats.candidates}</span>
        <span className="vq__stat-label">Candidati</span>
      </div>
      <div className="vq__stat vq__stat--alert">
        <span className="vq__stat-value">{stats.unknown}</span>
        <span className="vq__stat-label">Da ricercare</span>
      </div>
      <div className="vq__stat">
        <span className="vq__stat-value">{total}</span>
        <span className="vq__stat-label">Totale</span>
      </div>
    </div>
  );
}

function DecisionLog({ decisions }: { decisions: ValidationDecision[] }) {
  if (decisions.length === 0) return null;
  return (
    <div className="vq__decisions">
      <h3>Decisioni registrate ({decisions.length})</h3>
      <div className="vq__decisions-note">
        Ogni decisione è tracciata: propertyId → candidateId → decisione → evidenceRefs → stato
      </div>
      {decisions.map((d, i) => (
        <div key={i} className={`vq__decision vq__decision--${d.reviewerDecision.toLowerCase()}`}>
          <span className="mono">{d.propertyId}</span>
          <span className={`status ${d.reviewerDecision === "ACCEPT" ? "ev--doc" : d.reviewerDecision === "REJECT" ? "ev--nd" : "ev--inf"}`}>
            {d.reviewerDecision}
          </span>
          <span className="note">{d.previousState} → {d.resultingState}</span>
          <span className="note">{d.timestamp}</span>
        </div>
      ))}
    </div>
  );
}

function QueueItem({
  item,
  onAction,
}: {
  item: ValidationItem;
  onAction: (id: string, action: string, candidateId?: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`vq__item vq__item--${item.resolution.toLowerCase()}`}>
      <div className="vq__item-header" onClick={() => setExpanded(!expanded)}>
        <div className="vq__item-main">
          <span className="vq__item-entity mono">{item.entityName}</span>
          <span className="vq__item-property">{item.propertyLabel}</span>
          {item.proposedValue && (
            <span className="vq__item-value mono">{String(item.proposedValue)}</span>
          )}
        </div>
        <div className="vq__item-meta">
          <span className={`status ${RESOLUTION_COLORS[item.resolution] ?? ""}`}>{item.resolution}</span>
          <span className={`status ev--${item.evidenceStatus.startsWith("DOC") || item.evidenceStatus.startsWith("VER") ? "doc" : item.evidenceStatus === "RIF" ? "ris" : "nd"}`}>{item.evidenceStatus}</span>
          {item.confidence > 0 && (
            <span className="vq__confidence">{Math.round(item.confidence * 100)}%</span>
          )}
        </div>
      </div>

      {expanded && (
        <div className="vq__item-detail">
          <p className="vq__reason">{item.reason}</p>

          {item.searchHint && (
            <div className="vq__search-hint">
              <strong>Suggerimento ricerca:</strong> {item.searchHint}
            </div>
          )}

          {item.candidates.length > 0 && (
            <div className="vq__candidates">
              <h4>Candidati</h4>
              {item.candidates.map((c) => (
                <div key={c.id} className="vq__candidate">
                  <span className="mono">{String(c.value)}</span>
                  <span className={`status ev--${c.evidenceStatus.startsWith("DOC") ? "doc" : "nd"}`}>{c.evidenceStatus}</span>
                  <span className="note">{c.reasoning}</span>
                  {c.analogicalOrigin && (
                    <span className="vq__analog">via {c.analogicalOrigin}</span>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="vq__decision-notice">
            La decisione verrà registrata come ValidationDecision tracciabile.
            Non modifica il dataset canonico — produce solo una registrazione.
          </div>

          <div className="vq__actions">
            {item.resolution === "CANDIDATES" && (
              <>
                <button className="vq__btn vq__btn--accept" onClick={() => onAction(item.id, "ACCEPT")}>
                  Accetta (registra)
                </button>
                <button className="vq__btn vq__btn--reject" onClick={() => onAction(item.id, "REJECT")}>
                  Rifiuta (registra)
                </button>
              </>
            )}
            <button className="vq__btn vq__btn--defer" onClick={() => onAction(item.id, "DEFER")}>
              Deferisci
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ValidationQueuePanel({ queue }: { queue: VQType }) {
  const [filter, setFilter] = useState<string>("all");
  const [items, setItems] = useState(queue.items);
  const [decisions, setDecisions] = useState<ValidationDecision[]>([]);

  const filtered = filter === "all" ? items : items.filter((i) => i.resolution === filter);

  const handleAction = (id: string, action: string, candidateId?: string) => {
    const item = items.find((i) => i.id === id);
    if (!item) return;

    const decision: ValidationDecision = {
      propertyId: item.propertyId,
      candidateId: candidateId ?? item.candidates[0]?.id ?? null,
      candidateValue: item.proposedValue,
      reviewerDecision: action as "ACCEPT" | "REJECT" | "DEFER",
      evidenceRefs: item.candidates.map((c) => c.sourceId),
      previousState: item.resolution,
      resultingState: action === "ACCEPT" ? "VALIDATED" : action === "REJECT" ? "REJECTED" : item.resolution,
      timestamp: new Date().toISOString(),
    };

    setDecisions((prev) => [...prev, decision]);

    if (action !== "DEFER") {
      setItems((prev) =>
        prev.map((i) =>
          i.id === id
            ? { ...i, resolution: decision.resultingState as any }
            : i
        )
      );
    }
  };

  return (
    <section className="panel panel--vq">
      <h2>Coda di validazione</h2>

      <StatsBar stats={queue.stats} total={queue.stats.total} />

      <div className="vq__filters">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">Tutti ({items.length})</option>
          <option value="UNKNOWN">Da ricercare ({items.filter((i) => i.resolution === "UNKNOWN").length})</option>
          <option value="CANDIDATES">Candidati ({items.filter((i) => i.resolution === "CANDIDATES").length})</option>
          <option value="CONFLICT">Conflitti ({items.filter((i) => i.resolution === "CONFLICT").length})</option>
          <option value="VALIDATED">Validate ({items.filter((i) => i.resolution === "VALIDATED").length})</option>
        </select>
      </div>

      <DecisionLog decisions={decisions} />

      <div className="vq__list">
        {filtered.length === 0 && (
          <div className="vq__empty">Nessun elemento in coda per questo filtro.</div>
        )}
        {filtered.map((item) => (
          <QueueItem key={item.id} item={item} onAction={handleAction} />
        ))}
      </div>
    </section>
  );
}
