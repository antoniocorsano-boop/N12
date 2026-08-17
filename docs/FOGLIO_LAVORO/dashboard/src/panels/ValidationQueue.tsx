import { useState } from "react";
import type { ValidationQueue as VQType, ValidationItem, ResolutionState } from "../read-model/types";

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

function StatsBar({ stats }: { stats: VQType["stats"] }) {
  const pct = stats.total > 0 ? Math.round((stats.resolved / stats.total) * 100) : 0;
  return (
    <div className="vq__stats">
      <div className="vq__stat">
        <span className="vq__stat-value">{stats.total}</span>
        <span className="vq__stat-label">Totale</span>
      </div>
      <div className="vq__stat vq__stat--ok">
        <span className="vq__stat-value">{stats.resolved}</span>
        <span className="vq__stat-label">Risolte</span>
      </div>
      <div className="vq__stat vq__stat--warn">
        <span className="vq__stat-value">{stats.unknown}</span>
        <span className="vq__stat-label">Sconosciute</span>
      </div>
      <div className="vq__stat vq__stat--info">
        <span className="vq__stat-value">{stats.proposed}</span>
        <span className="vq__stat-label">Proposte</span>
      </div>
      <div className="vq__progress">
        <div className="vq__progress-bar" style={{ width: `${pct}%` }} />
        <span className="vq__progress-label">{pct}% risolto</span>
      </div>
    </div>
  );
}

function QueueItem({
  item,
  onAction,
}: {
  item: ValidationItem;
  onAction: (id: string, action: string) => void;
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

          <div className="vq__actions">
            {item.resolution === "CANDIDATES" && (
              <>
                <button className="vq__btn vq__btn--accept" onClick={() => onAction(item.id, "ACCEPT")}>
                  Accetta proposta
                </button>
                <button className="vq__btn vq__btn--reject" onClick={() => onAction(item.id, "REJECT")}>
                  Rifiuta
                </button>
              </>
            )}
            <button className="vq__btn" onClick={() => onAction(item.id, "INSPECT")}>
              Apri evidenze
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

  const filtered = filter === "all" ? items : items.filter((i) => i.resolution === filter);

  const handleAction = (id: string, action: string) => {
    setItems((prev) =>
      prev.map((item) =>
        item.id === id
          ? { ...item, resolution: action === "ACCEPT" ? "VALIDATED" : action === "REJECT" ? "REJECTED" : item.resolution }
          : item
      )
    );
  };

  return (
    <section className="panel panel--vq">
      <h2>Coda di validazione</h2>

      <StatsBar stats={queue.stats} />

      <div className="vq__filters">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">Tutti ({items.length})</option>
          <option value="UNKNOWN">Sconosciute ({items.filter((i) => i.resolution === "UNKNOWN").length})</option>
          <option value="CANDIDATES">Candidati ({items.filter((i) => i.resolution === "CANDIDATES").length})</option>
          <option value="CONFLICT">Conflitti ({items.filter((i) => i.resolution === "CONFLICT").length})</option>
        </select>
      </div>

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
