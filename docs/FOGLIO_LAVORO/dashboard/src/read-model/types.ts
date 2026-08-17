export type EvidenceStatus =
  | "DOC"
  | "DOC-ARTEFATTO"
  | "DOC-famiglia"
  | "DOC-STORICO"
  | "VER"
  | "VER_GEOMETRIC"
  | "RIF"
  | "PREDOC_TOPOLOGICO"
  | "INF_DA_QUOTARE"
  | "INF"
  | "ND"
  | "INC"
  | "PLACEHOLDER"
  | "PLACEHOLDER_GEOMETRY_ONLY"
  | "IN_CORSO"
  | "IN_ALLINEAMENTO";

export type FrontStatus =
  | "PARTIAL"
  | "ADVANCING"
  | "IN CORSO"
  | "NOT STARTED"
  | "BLOCKED"
  | "N/A";

export type ResidualType = "BLOCCANTE" | "RISCHIO" | "CONFORMITA" | "OPERATIVO";
export type ResidualState = "APERTO" | "IN CORSO" | "BLOCCATO" | "CHIUSO";

export type ArtifactProvenance = "main" | "main→M0-G" | "M0-G" | "R1-A" | "R1-B";

export interface ProjectIdentity {
  name: string;
  location: string;
  target: string;
  currentGate: string;
  fascicoloVersion: string;
  lastUpdate: string;
}

export interface PipelineStage {
  id: string;
  name: string;
  fronts: string[];
  status: FrontStatus;
}

export interface Front {
  id: string;
  name: string;
  status: FrontStatus;
  evidenceCount: number;
  residualCount: number;
  blockingResiduals: number;
  nextAction: string;
}

export interface Evidence {
  id: string;
  scope: string;
  description: string;
  status: EvidenceStatus;
  source: string;
  note: string;
}

export interface Artifact {
  id: string;
  name: string;
  path: string;
  status: string;
  provenance: ArtifactProvenance;
  front: string;
  evidenceIds: string[];
}

export interface Residual {
  id: string;
  type: ResidualType;
  front: string;
  description: string;
  state: ResidualState;
  evidenceIds: string[];
  dependencies: string[];
}

export interface R1Snapshot {
  project: ProjectIdentity;
  pipeline: PipelineStage[];
  fronts: Front[];
  evidences: Evidence[];
  artifacts: Artifact[];
  residuals: Residual[];
  evidenceCounts: Record<EvidenceStatus, number>;
  nextGlobalAction: string;
}
