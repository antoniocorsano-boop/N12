import snapshot from "./read-model/r1-snapshot.json";
import type { R1Snapshot } from "./read-model/types";
import ProjectIdentityPanel from "./panels/ProjectIdentity";
import Pipeline from "./panels/Pipeline";
import Fronts from "./panels/Fronts";
import NextAction from "./panels/NextAction";
import Evidences from "./panels/Evidences";
import Artifacts from "./panels/Artifacts";
import Residuals from "./panels/Residuals";

const data = snapshot as R1Snapshot;

export default function StructuralProfessionalWorkspace() {
  return (
    <div className="r1-workspace">
      <header className="r1-header">
        <h1>Fascicolo R1 — {data.project.name}</h1>
        <span className="r1-version">{data.project.fascicoloVersion}</span>
      </header>

      <main className="r1-grid">
        <div className="r1-grid__left">
          <ProjectIdentityPanel project={data.project} />
          <NextAction action={data.nextGlobalAction} />
          <Fronts fronts={data.fronts} />
        </div>

        <div className="r1-grid__right">
          <Pipeline pipeline={data.pipeline} fronts={data.fronts} />
          <Evidences evidences={data.evidences} />
          <Artifacts artifacts={data.artifacts} />
          <Residuals residuals={data.residuals} />
        </div>
      </main>

      <footer className="r1-footer">
        <span>Fonte: FOGLIO_LAVORO/ — deterministico, nessun parsing Markdown a runtime</span>
        <span>Aggiornamento: {data.project.lastUpdate}</span>
      </footer>
    </div>
  );
}
