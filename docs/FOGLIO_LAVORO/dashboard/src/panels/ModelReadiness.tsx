import type { ReadinessMatrix } from "../read-model/types";

const LEVEL_COLORS: Record<string, string> = {
  COMPLETO: "ev--doc",
  PARZIALE: "ev--inf",
  ND: "ev--nd",
  BLOCCATO: "ev--nd",
};

export default function ModelReadiness({ readiness }: { readiness: ReadinessMatrix }) {
  return (
    <section className="panel panel--readiness">
      <h2>Preparazione del modello</h2>

      <div className="readiness__status">
        <span className={`status ${LEVEL_COLORS[readiness.overallStatus] ?? ""}`}>
          {readiness.overallStatus}
        </span>
        {readiness.m0GateBlocked && (
          <span className="readiness__gate-badge">M0-G non chiuso</span>
        )}
      </div>

      <table className="readiness__table">
        <thead>
          <tr>
            <th>Dominio</th>
            <th>Stato</th>
            <th className="num">Disponibili</th>
            <th>Mancanze</th>
          </tr>
        </thead>
        <tbody>
          {readiness.cells.map((cell) => (
            <tr key={cell.domain}>
              <td className="readiness__domain">{cell.label}</td>
              <td>
                <span className={`status ${LEVEL_COLORS[cell.level] ?? ""}`}>{cell.level}</span>
              </td>
              <td className="num">
                {cell.total > 0 ? `${cell.available}/${cell.total}` : "—"}
              </td>
              <td className="readiness__missing">
                {cell.missing.map((m, i) => (
                  <div key={i} className="readiness__missing-item">{m}</div>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {readiness.blockingReasons.length > 0 && (
        <div className="readiness__blockers">
          <h3>Perché M0-G non è chiuso</h3>
          <ul>
            {readiness.blockingReasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
