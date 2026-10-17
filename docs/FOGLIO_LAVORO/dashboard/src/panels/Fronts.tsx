import type { Front } from "../read-model/types";

const STATUS_ICONS: Record<string, string> = {
  ADVANCING: "🟢",
  PARTIAL: "🟡",
  "IN CORSO": "🔵",
  BLOCKED: "🔴",
  "NOT STARTED": "⚪",
  "N/A": "⬛",
};

export default function Fronts({ fronts }: { fronts: Front[] }) {
  return (
    <section className="panel panel--fronts">
      <h2>Fronti</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nome</th>
            <th>Stato</th>
            <th className="num">Evidenze</th>
            <th className="num">Residui</th>
            <th className="num">Bloccanti</th>
            <th>Prossima azione</th>
          </tr>
        </thead>
        <tbody>
          {fronts.map((f) => (
            <tr key={f.id} className={`fronts__row fronts__row--${f.status.replace(/\s+/g, "-").toLowerCase()}`}>
              <td className="mono">{f.id}</td>
              <td>{f.name}</td>
              <td>
                <span className="status">{STATUS_ICONS[f.status] ?? ""} {f.status}</span>
              </td>
              <td className="num">{f.evidenceCount}</td>
              <td className="num">{f.residualCount}</td>
              <td className="num">{f.blockingResiduals}</td>
              <td className="action">{f.nextAction}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
