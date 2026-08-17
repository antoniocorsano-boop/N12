import { useState } from "react";
import snapshot from "./read-model/r1-snapshot.json";
import type { R1Snapshot } from "./read-model/types";
import Navigation from "./panels/Navigation";
import ProjectIdentityPanel from "./panels/ProjectIdentity";
import Pipeline from "./panels/Pipeline";
import Fronts from "./panels/Fronts";
import NextAction from "./panels/NextAction";
import Evidences from "./panels/Evidences";
import Artifacts from "./panels/Artifacts";
import Residuals from "./panels/Residuals";
import StatoDiFatto from "./panels/StatoDiFatto";
import ModelReadiness from "./panels/ModelReadiness";
import AdapterStatusPanel from "./panels/AdapterStatus";
import DiagnosticExport from "./panels/DiagnosticExport";

const data = snapshot as R1Snapshot;

function Panoramica() {
  return (
    <div className="r1-grid">
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
    </div>
  );
}

function ModelView() {
  return (
    <div className="r1-grid">
      <div className="r1-grid__left">
        <ModelReadiness readiness={data.readiness} />
        <DiagnosticExport model={data.canonicalModel} />
      </div>
      <div className="r1-grid__right">
        <AdapterStatusPanel adapters={data.adapters} />
      </div>
    </div>
  );
}

export default function StructuralProfessionalWorkspace() {
  const [activeTab, setActiveTab] = useState<"panoramica" | "edificio" | "modello" | "evidenze" | "residui" | "artefatti">("panoramica");

  return (
    <div className="r1-workspace">
      <header className="r1-header">
        <h1>Fascicolo R1 — {data.project.name}</h1>
        <span className="r1-version">{data.project.fascicoloVersion}</span>
      </header>

      <Navigation activeTab={activeTab} onTabChange={setActiveTab} snapshot={data} />

      <main className="r1-main">
        {activeTab === "panoramica" && <Panoramica />}
        {activeTab === "edificio" && <StatoDiFatto snapshot={data} />}
        {activeTab === "modello" && <ModelView />}
        {activeTab === "evidenze" && (
          <div className="r1-single-panel"><Evidences evidences={data.evidences} /></div>
        )}
        {activeTab === "residui" && (
          <div className="r1-single-panel"><Residuals residuals={data.residuals} /></div>
        )}
        {activeTab === "artefatti" && (
          <div className="r1-single-panel"><Artifacts artifacts={data.artifacts} /></div>
        )}
      </main>

      <footer className="r1-footer">
        <span>Fonte: FOGLIO_LAVORO/ + data/canonical/ — deterministico, nessun parsing a runtime</span>
        <span>Aggiornamento: {data.project.lastUpdate}</span>
      </footer>
    </div>
  );
}
