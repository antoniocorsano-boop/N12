import type { Residual } from "../read-model/types";

const TYPE_ICONS: Record<string, string> = {
  BLOCCANTE: "🔴",
  RISCHIO: "🟡",
  CONFORMITA: "🟠",
  OPERATIVO: "🔵",
};

const STATE_CLASSES: Record<string, string> = {
  APERTO: "rs--aperto",
  "IN CORSO": "rs--in-corso",
  BLOCCATO: "rs--bloccato",
  CHIUSO: "rs--chiuso",
};

export default function Residuals({ residuals }: { residuals: Residual[] }) {
  const open = residuals.filter((r) => r.state !== "CHIUSO");
  const closed = residuals.filter((r) => r.state === "CHIUSO");
  return (
    <section className="panel panel--residuals">
      <h2>Residui</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Tipo</th>
            <th>Fronte</th>
            <th>Descrizione</th>
            <th>Stato</th>
            <th>Dipendenze</th>
          </tr>
        </thead>
        <tbody>
          {open.map((r) => (
            <tr key={r.id}>
              <td className="mono">{r.id}</td>
              <td>{TYPE_ICONS[r.type] ?? ""} {r.type}</td>
              <td className="mono">{r.front}</td>
              <td>{r.description}</td>
              <td>
                <span className={`status ${STATE_CLASSES[r.state] ?? ""}`}>{r.state}</span>
              </td>
              <td className="mono">{r.dependencies.length > 0 ? r.dependencies.join(", ") : "—"}</td>
            </tr>
          ))}
          {closed.length > 0 && (
            <>
              <tr className="residuals__separator"><td colSpan={6}>Chiusi</td></tr>
              {closed.map((r) => (
                <tr key={r.id} className="residuals__closed">
                  <td className="mono">{r.id}</td>
                  <td>{r.type}</td>
                  <td className="mono">{r.front}</td>
                  <td>{r.description}</td>
                  <td><span className="status rs--chiuso">CHIUSO</span></td>
                  <td className="mono">—</td>
                </tr>
              ))}
            </>
          )}
        </tbody>
      </table>
    </section>
  );
}
