import type { ProjectIdentity, ValidationQueue } from "../read-model/types";

export default function ProjectIdentityPanel({ project, validationQueue }: { project: ProjectIdentity; validationQueue?: ValidationQueue }) {
  const stats = validationQueue?.stats;
  const total = stats?.total ?? 0;

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
      {stats && (
        <div className="identity__validation">
          <span className="identity__validation-label">Risoluzione proprietà</span>
          <div className="identity__validation-breakdown">
            <span className="identity__validation-item identity__validation-item--ok">
              {stats.validated}/{total} validate
            </span>
            <span className="identity__validation-item identity__validation-item--warn">
              {stats.candidates}/{total} candidati
            </span>
            <span className="identity__validation-item identity__validation-item--alert">
              {stats.unknown}/{total} da ricercare
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
