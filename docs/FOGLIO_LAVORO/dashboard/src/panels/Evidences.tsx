import type { Evidence } from "../read-model/types";

const STATUS_ORDER: Record<string, number> = {
  DOC: 0,
  "DOC-ARTEFATTO": 1,
  "DOC-famiglia": 2,
  "DOC-STORICO": 3,
  VER: 10,
  VER_GEOMETRIC: 11,
  RIF: 20,
  PREDOC_TOPOLOGICO: 30,
  INF: 40,
  INF_DA_QUOTARE: 41,
  ND: 50,
  INC: 51,
  PLACEHOLDER: 60,
  PLACEHOLDER_GEOMETRY_ONLY: 61,
  IN_CORSO: 70,
  IN_ALLINEAMENTO: 71,
};

const STATUS_CLASSES: Record<string, string> = {
  DOC: "ev--doc",
  "DOC-ARTEFATTO": "ev--doc",
  "DOC-famiglia": "ev--doc",
  "DOC-STORICO": "ev--doc",
  VER: "ev--doc",
  VER_GEOMETRIC: "ev--doc",
  RIF: "ev--ris",
  PREDOC_TOPOLOGICO: "ev--inf",
  INF: "ev--inf",
  INF_DA_QUOTARE: "ev--inf",
  ND: "ev--nd",
  PLACEHOLDER: "ev--nd",
  PLACEHOLDER_GEOMETRY_ONLY: "ev--nd",
};

export default function Evidences({ evidences }: { evidences: Evidence[] }) {
  const sorted = [...evidences].sort(
    (a, b) => (STATUS_ORDER[a.status] ?? 99) - (STATUS_ORDER[b.status] ?? 99)
  );
  return (
    <section className="panel panel--evidences">
      <h2>Evidenze</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Ambito</th>
            <th>Descrizione</th>
            <th>Stato</th>
            <th>Fonte</th>
            <th>Note</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((e) => (
            <tr key={e.id}>
              <td className="mono">{e.id}</td>
              <td>{e.scope}</td>
              <td>{e.description}</td>
              <td>
                <span className={`status ${STATUS_CLASSES[e.status] ?? ""}`}>{e.status}</span>
              </td>
              <td className="mono">{e.source}</td>
              <td className="note">{e.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
