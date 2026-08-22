import type { R1Snapshot } from "../read-model/types";

type Tab = "panoramica" | "edificio" | "modello" | "validazione" | "evidenze" | "residui" | "artefatti";

const TABS: { id: Tab; label: string; available: boolean }[] = [
  { id: "panoramica", label: "Panoramica", available: true },
  { id: "edificio", label: "Stato di fatto", available: true },
  { id: "modello", label: "Modello", available: true },
  { id: "validazione", label: "Validazione", available: true },
  { id: "evidenze", label: "Evidenze", available: true },
  { id: "residui", label: "Residui", available: true },
  { id: "artefatti", label: "Artefatti", available: true },
];

export default function Navigation({
  activeTab,
  onTabChange,
  snapshot,
}: {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
  snapshot: R1Snapshot;
}) {
  const unresolvedCount = snapshot.validationQueue.items.length;
  return (
    <nav className="nav">
      <div className="nav__tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`nav__tab ${activeTab === tab.id ? "nav__tab--active" : ""} ${!tab.available ? "nav__tab--disabled" : ""}`}
            onClick={() => tab.available && onTabChange(tab.id)}
            disabled={!tab.available}
          >
            {tab.label}
            {tab.id === "validazione" && unresolvedCount > 0 && (
              <span className="nav__badge">{unresolvedCount}</span>
            )}
          </button>
        ))}
      </div>
      <div className="nav__meta">
        <span className="nav__gate">Gate: {snapshot.project.currentGate}</span>
        <span className="nav__chains">{snapshot.building.chains.length} catene · {snapshot.building.totalChainLevelEntities} entità</span>
      </div>
    </nav>
  );
}
