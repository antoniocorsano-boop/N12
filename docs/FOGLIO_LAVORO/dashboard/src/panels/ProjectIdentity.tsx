import type { ProjectIdentity } from "../read-model/types";

export default function ProjectIdentityPanel({ project }: { project: ProjectIdentity }) {
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
    </section>
  );
}
