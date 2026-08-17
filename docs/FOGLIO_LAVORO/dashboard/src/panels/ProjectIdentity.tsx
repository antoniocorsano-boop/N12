import type { ProjectIdentity, ValidationQueue } from "../read-model/types";

export default function ProjectIdentityPanel({ project, validationQueue }: { project: ProjectIdentity; validationQueue?: ValidationQueue }) {
  const pct = validationQueue && validationQueue.stats.total > 0
    ? Math.round((validationQueue.stats.resolved / validationQueue.stats.total) * 100)
    : null;

  return (
    <section className="panel panel--identity">
      <h2>Progetto</h2>
      <dl>
        <dt>Edificio</dt>
        <dd>{project.name}</dd>
        <dt>Località</dt>
        <dd>{project.location}</dd>
        <dt>Obiettivo</dt>
        <dd>{project.target}</dd>
        <dt>Gate corrente</dt>
        <dd className="gate">{project.currentGate}</dd>
        <dt>Versione fascicolo</dt>
        <dd>{project.fascicoloVersion}</dd>
        <dt>Ultimo aggiornamento</dt>
        <dd>{project.lastUpdate}</dd>
      </dl>
      {pct !== null && (
        <div className="identity__validation">
          <span className="identity__validation-label">Risoluzione proprietà</span>
          <div className="identity__validation-bar">
            <div className="identity__validation-fill" style={{ width: `${pct}%` }} />
          </div>
          <span className="identity__validation-pct">{pct}%</span>
        </div>
      )}
    </section>
  );
}
