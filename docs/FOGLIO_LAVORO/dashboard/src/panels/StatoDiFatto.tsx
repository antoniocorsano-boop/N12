import { useState } from "react";
import type { R1Snapshot, BuildingChain } from "../read-model/types";
import ChainInspector from "./ChainInspector";

function StatusChip({ status }: { status: string }) {
  const cls =
    status.startsWith("DOC") || status.startsWith("VER")
      ? "ev--doc"
      : status === "RIF" || status === "RIF_UTENTE_CORRETTO"
        ? "ev--ris"
        : status.startsWith("INF") || status.startsWith("PREDOC")
          ? "ev--inf"
          : status === "ND" || status === "INC"
            ? "ev--nd"
            : status.startsWith("PLACEHOLDER")
              ? "ev--nd"
              : "";
  return <span className={`status ${cls}`}>{status}</span>;
}

function ChainRow({
  chain,
  isSelected,
  onSelect,
}: {
  chain: BuildingChain;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const hasNd = chain.levels.some((l) => l.section?.value === "ND" || l.section?.status === "ND");
  const hasDoc = chain.levels.some((l) => l.section?.status === "DOC");
  const sectionSummary = chain.levels
    .filter((l) => l.section)
    .map((l) => `${l.level}: ${l.section!.value}`)
    .join(", ");

  return (
    <tr
      className={`chain-row ${isSelected ? "chain-row--selected" : ""} ${hasNd ? "chain-row--nd" : ""}`}
      onClick={onSelect}
    >
      <td className="mono">{chain.nodeId}</td>
      <td className="mono">{chain.chainId}</td>
      <td className="mono">{chain.axisX} / {chain.axisY}</td>
      <td className="num">{chain.coordinates.x_mm.toFixed(0)}</td>
      <td className="num">{chain.coordinates.y_mm.toFixed(0)}</td>
      <td>
        {hasDoc && !hasNd ? (
          <StatusChip status="DOC" />
        ) : hasNd ? (
          <StatusChip status="ND" />
        ) : (
          <StatusChip status="PREDOC_GEOMETRICO" />
        )}
      </td>
      <td className="mono" style={{ fontSize: 11 }}>{sectionSummary || "—"}</td>
      <td className="mono">{chain.evidenceIds.length}</td>
    </tr>
  );
}

export default function StatoDiFatto({ snapshot }: { snapshot: R1Snapshot }) {
  const [selectedChain, setSelectedChain] = useState<BuildingChain | null>(null);
  const [filterLevel, setFilterLevel] = useState<string>("all");

  const { building } = snapshot;
  const filteredChains =
    filterLevel === "all"
      ? building.chains
      : building.chains.filter((c) => c.levels.some((l) => l.level === filterLevel));

  return (
    <div className="stato-fatto">
      <div className="stato-fatto__header">
        <h2>Edificio — Catene verticali</h2>
        <div className="stato-fatto__filters">
          <label>Piano:</label>
          <select value={filterLevel} onChange={(e) => setFilterLevel(e.target.value)}>
            <option value="all">Tutti ({building.chains.length})</option>
            {building.levels.map((l) => (
              <option key={l.id} value={l.id}>{l.label} (h={l.height_m}m)</option>
            ))}
          </select>
        </div>
      </div>

      <div className="stato-fatto__summary">
        <div className="summary-card">
          <span className="summary-card__value">{building.chains.length}</span>
          <span className="summary-card__label">Catene</span>
        </div>
        <div className="summary-card">
          <span className="summary-card__value">{building.levels.length}</span>
          <span className="summary-card__label">Livelli</span>
        </div>
        <div className="summary-card">
          <span className="summary-card__value">{building.totalChainLevelEntities}</span>
          <span className="summary-card__label">Entità catena×livello</span>
        </div>
        <div className="summary-card summary-card--warn">
          <span className="summary-card__value">
            {building.chains.filter((c) => c.levels.some((l) => l.section?.value === "ND")).length}
          </span>
          <span className="summary-card__label">Sezione ND</span>
        </div>
      </div>

      <div className="stato-fatto__content">
        <div className="stato-fatto__table">
          <table>
            <thead>
              <tr>
                <th>Nodo</th>
                <th>Catena</th>
                <th>Assi</th>
                <th className="num">X (mm)</th>
                <th className="num">Y (mm)</th>
                <th>Stato</th>
                <th>Sezioni per livello</th>
                <th className="num">EV</th>
              </tr>
            </thead>
            <tbody>
              {filteredChains.map((chain) => (
                <ChainRow
                  key={chain.nodeId}
                  chain={chain}
                  isSelected={selectedChain?.nodeId === chain.nodeId}
                  onSelect={() => setSelectedChain(chain)}
                />
              ))}
            </tbody>
          </table>
        </div>

        {selectedChain && (
          <ChainInspector
            chain={selectedChain}
            snapshot={snapshot}
            onClose={() => setSelectedChain(null)}
          />
        )}
      </div>
    </div>
  );
}
