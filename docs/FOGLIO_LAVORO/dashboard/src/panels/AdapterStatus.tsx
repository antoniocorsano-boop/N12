import type { AdapterStatus } from "../read-model/types";

const STATE_COLORS: Record<string, string> = {
  READY: "ev--doc",
  PARTIAL: "ev--inf",
  BLOCKED: "ev--nd",
};

export default function AdapterStatusPanel({ adapters }: { adapters: AdapterStatus[] }) {
  return (
    <section className="panel panel--adapters">
      <h2>Adattatori</h2>
      <div className="adapters__list">
        {adapters.map((adapter) => (
          <div key={adapter.id} className={`adapter adapter--${adapter.state.toLowerCase()}`}>
            <div className="adapter__header">
              <h3>{adapter.name}</h3>
              <span className={`status ${STATE_COLORS[adapter.state] ?? ""}`}>{adapter.state}</span>
            </div>
            <p className="adapter__desc">{adapter.description}</p>

            <div className="adapter__requirements">
              <h4>Proprietà richieste</h4>
              <table>
                <thead>
                  <tr>
                    <th>Proprietà</th>
                    <th>Richiesta</th>
                    <th>Stato attuale</th>
                    <th>Blocker</th>
                  </tr>
                </thead>
                <tbody>
                  {adapter.requiredProperties.map((req) => (
                    <tr key={req.property}>
                      <td className="mono">{req.property}</td>
                      <td>{req.required ? "Sì" : "No"}</td>
                      <td>
                        <span className={`status ev--${req.currentStatus.startsWith("DOC") || req.currentStatus.startsWith("VER") ? "doc" : req.currentStatus === "RIF" ? "ris" : req.currentStatus.startsWith("INF") || req.currentStatus.startsWith("PREDOC") ? "inf" : "nd"}`}>
                          {req.currentStatus}
                        </span>
                      </td>
                      <td className="note">{req.blocker ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {adapter.blockingProperties.length > 0 && (
              <div className="adapter__blocking">
                <span className="adapter__blocking-label">Bloccato da:</span>
                {adapter.blockingProperties.map((p) => (
                  <span key={p} className="adapter__blocking-prop mono">{p}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
