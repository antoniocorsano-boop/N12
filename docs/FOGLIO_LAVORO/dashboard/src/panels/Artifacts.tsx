import type { Artifact } from "../read-model/types";

const PROV_BADGES: Record<string, string> = {
  main: "badge--main",
  "main→M0-G": "badge--main-m0g",
  "M0-G": "badge--m0g",
  "R1-A": "badge--r1a",
  "R1-B": "badge--r1b",
};

export default function Artifacts({ artifacts }: { artifacts: Artifact[] }) {
  return (
    <section className="panel panel--artifacts">
      <h2>Artefatti</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nome</th>
            <th>Provenienza</th>
            <th>Stato</th>
            <th>Fronte</th>
            <th>Evidenze collegate</th>
          </tr>
        </thead>
        <tbody>
          {artifacts.map((a) => (
            <tr key={a.id}>
              <td className="mono">{a.id}</td>
              <td>{a.name}</td>
              <td>
                <span className={`badge ${PROV_BADGES[a.provenance] ?? ""}`}>{a.provenance}</span>
              </td>
              <td className="mono">{a.status}</td>
              <td className="mono">{a.front}</td>
              <td className="mono">{a.evidenceIds.length > 0 ? a.evidenceIds.join(", ") : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
