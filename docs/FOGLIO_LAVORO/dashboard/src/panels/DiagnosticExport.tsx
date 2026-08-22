import type { CanonicalStructuralModel } from "../read-model/types";

export default function DiagnosticExport({ model }: { model: CanonicalStructuralModel }) {
  return (
    <section className="panel panel--diagnostic">
      <h2>Export diagnostico — canonical-structural-model.json</h2>

      <div className="diagnostic__meta">
        <dl>
          <dt>Schema</dt>
          <dd className="mono">{model.schemaVersion}</dd>
          <dt>Generato</dt>
          <dd className="mono">{model.generatedAt}</dd>
          <dt>Rivisione sorgente</dt>
          <dd className="mono">{model.sourceRevision}</dd>
          <dt>Gate</dt>
          <dd className="mono">{model.gate}</dd>
        </dl>
      </div>

      <div className="diagnostic__summary">
        <div className="summary-card">
          <span className="summary-card__value">{model.entities.length}</span>
          <span className="summary-card__label">Entità</span>
        </div>
        <div className="summary-card summary-card--warn">
          <span className="summary-card__value">{model.missingProperties.length}</span>
          <span className="summary-card__label">Proprietà mancanti</span>
        </div>
        <div className="summary-card summary-card--warn">
          <span className="summary-card__value">{model.blockingResiduals.length}</span>
          <span className="summary-card__label">Residui bloccanti</span>
        </div>
      </div>

      <div className="diagnostic__note">
        Questo file è un artefatto derivato e diagnostico. Non è un modello FEM pronto.
        Contiene solo le proprietà derivabili deterministicamente dalle fonti canoniche.
      </div>

      {model.blockingResiduals.length > 0 && (
        <div className="diagnostic__blockers">
          <h3>Residui bloccanti</h3>
          <ul>
            {model.blockingResiduals.map((r) => (
              <li key={r} className="mono">{r}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
