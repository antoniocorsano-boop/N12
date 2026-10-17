import type { R1Snapshot, BuildingChain, PropertyValue } from "../read-model/types";

function Field({ label, prop }: { label: string; prop?: PropertyValue }) {
  if (!prop) return null;
  return (
    <div className="inspector__field">
      <dt>{label}</dt>
      <dd>
        <span className="mono">{String(prop.value)}</span>
        <span className={`status ev--${prop.status.startsWith("DOC") || prop.status.startsWith("VER") ? "doc" : prop.status === "RIF" ? "ris" : prop.status.startsWith("INF") || prop.status.startsWith("PREDOC") ? "inf" : "nd"}`}>
          {prop.status}
        </span>
        {prop.evidenceId && (
          <span className="inspector__ev-link mono" title={prop.source}>{prop.evidenceId}</span>
        )}
      </dd>
    </div>
  );
}

export default function ChainInspector({
  chain,
  snapshot,
  onClose,
}: {
  chain: BuildingChain;
  snapshot: R1Snapshot;
  onClose: () => void;
}) {
  const relatedResiduals = snapshot.residuals.filter((r) => chain.residualIds.includes(r.id));
  const relatedEvidences = snapshot.evidences.filter((e) => chain.evidenceIds.includes(e.id));

  return (
    <aside className="inspector">
      <div className="inspector__header">
        <h3>Catena {chain.chainId}</h3>
        <button className="inspector__close" onClick={onClose}>×</button>
      </div>

      <div className="inspector__section">
        <h4>Identità</h4>
        <dl>
          <Field label="Nodo" prop={{ value: chain.nodeId, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" }} />
          <Field label="Catena" prop={{ value: chain.chainId, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" }} />
          <Field label="Asse X" prop={{ value: chain.axisX, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" }} />
          <Field label="Asse Y" prop={{ value: chain.axisY, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" }} />
        </dl>
      </div>

      <div className="inspector__section">
        <h4>Geometria</h4>
        <dl>
          <Field label="X (mm)" prop={{ value: chain.coordinates.x_mm, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" }} />
          <Field label="Y (mm)" prop={{ value: chain.coordinates.y_mm, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" }} />
        </dl>
      </div>

      <div className="inspector__section">
        <h4>Proprietà per livello</h4>
        {chain.levels.map((lev) => (
          <div key={lev.level} className="inspector__level">
            <h5>{lev.level}</h5>
            <dl>
              <Field label="Sezione" prop={lev.section} />
              <Field label="Trave" prop={lev.frame} />
              <Field label="Campate" prop={lev.spans} />
              <Field label="Sviluppo" prop={lev.development} />
            </dl>
          </div>
        ))}
      </div>

      {relatedResiduals.length > 0 && (
        <div className="inspector__section">
          <h4>Residui collegati</h4>
          {relatedResiduals.map((r) => (
            <div key={r.id} className="inspector__residual">
              <span className="mono">{r.id}</span>
              <span className={`status rs--${r.state.toLowerCase().replace(" ", "-")}`}>{r.state}</span>
              <span>{r.description}</span>
            </div>
          ))}
        </div>
      )}

      <div className="inspector__section">
        <h4>Evidenze ({relatedEvidences.length})</h4>
        {relatedEvidences.map((e) => (
          <div key={e.id} className="inspector__evidence">
            <span className="mono">{e.id}</span>
            <span className={`status ev--${e.status.startsWith("DOC") || e.status.startsWith("VER") ? "doc" : e.status === "RIF" ? "ris" : e.status.startsWith("INF") || e.status.startsWith("PREDOC") ? "inf" : "nd"}`}>{e.status}</span>
            <span className="note">{e.description}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}
