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
  | "IN_ALLINEAMENTO"
  | "PREDOC_GEOMETRICO"
  | "DOC_PARZIALE"
  | "RIF_UTENTE_CORRETTO";

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

export interface PropertyValue {
  value: string | number;
  status: EvidenceStatus;
  source: string;
  evidenceId?: string;
}

export interface ChainProperty {
  key: string;
  label: string;
  level: string;
  property: PropertyValue;
}

export interface BuildingChain {
  nodeId: string;
  chainId: string;
  axisX: string;
  axisY: string;
  coordinates: { x_mm: number; y_mm: number };
  topologyClass?: string;
  topologyGrade?: number;
  levels: {
    level: string;
    section?: PropertyValue;
    reinforcement?: PropertyValue;
    material?: PropertyValue;
    frame?: PropertyValue;
    spans?: PropertyValue;
    development?: PropertyValue;
  }[];
  evidenceIds: string[];
  residualIds: string[];
}

export interface BuildingLevel {
  id: string;
  label: string;
  height_m: number;
  height_status: EvidenceStatus;
  chainCount: number;
}

export interface BuildingFrame {
  id: string;
  name: string;
  levels: string[];
  documented: boolean;
  evidenceIds: string[];
}

export interface BuildingSnapshot {
  levels: BuildingLevel[];
  chains: BuildingChain[];
  frames: BuildingFrame[];
  totalChainLevelEntities: number;
}

export interface R1Snapshot {
  project: ProjectIdentity;
  pipeline: PipelineStage[];
  fronts: Front[];
  evidences: Evidence[];
  artifacts: Artifact[];
  residuals: Residual[];
  evidenceCounts: Record<string, number>;
  nextGlobalAction: string;
  building: BuildingSnapshot;
  canonicalModel: CanonicalStructuralModel;
  readiness: ReadinessMatrix;
  adapters: AdapterStatus[];
}

/* ═══════════════════════════════════════════════════
   R1-E: Canonical Structural Model Contract
   ═══════════════════════════════════════════════════ */

/* ─── E1: Persistent Identity ─── */
export type EntityType =
  | "building"
  | "level"
  | "chain"
  | "column"
  | "beam"
  | "span"
  | "foundation"
  | "node";

export interface CanonicalId {
  raw: string;
  entityType: EntityType;
  level?: string;
  frame?: string;
  chain?: string;
  span?: string;
}

/* ─── E2: Model Layers ─── */
export type ModelLayer = "observed" | "analytical" | "intervention" | "results";

/* ─── E3: Property with per-property provenance ─── */
export interface CanonicalProperty {
  key: string;
  label: string;
  layer: ModelLayer;
  value: string | number | null;
  status: EvidenceStatus;
  source: string;
  evidenceId?: string;
  missingReason?: string;
}

/* ─── E4: Canonical Entity ─── */
export interface CanonicalEntity {
  id: CanonicalId;
  name: string;
  layer: ModelLayer;
  properties: CanonicalProperty[];
  parent?: string;
  children?: string[];
  evidenceIds: string[];
  residualIds: string[];
}

/* ─── Canonical Structural Model ─── */
export interface CanonicalStructuralModel {
  schemaVersion: string;
  generatedAt: string;
  sourceRevision: string;
  gate: string;
  entities: CanonicalEntity[];
  missingProperties: { entityId: string; property: string; reason: string }[];
  blockingResiduals: string[];
}

/* ─── E5: Adapter Contracts ─── */
export type AdapterState = "READY" | "BLOCKED" | "PARTIAL";

export interface AdapterPropertyRequirement {
  property: string;
  required: boolean;
  currentStatus: EvidenceStatus;
  blocker?: string;
}

export interface AdapterStatus {
  id: string;
  name: string;
  state: AdapterState;
  description: string;
  requiredProperties: AdapterPropertyRequirement[];
  blockingProperties: string[];
}

/* ─── E6: Model Readiness Matrix ─── */
export type ReadinessDomain =
  | "geometria"
  | "topologia"
  | "sezioni"
  | "armature"
  | "materiali"
  | "fondazioni"
  | "carichi"
  | "lc_fc";

export type ReadinessLevel = "COMPLETO" | "PARZIALE" | "ND" | "BLOCCATO";

export interface ReadinessCell {
  domain: ReadinessDomain;
  label: string;
  level: ReadinessLevel;
  available: number;
  total: number;
  missing: string[];
  evidenceStatus: EvidenceStatus;
}

export interface ReadinessMatrix {
  cells: ReadinessCell[];
  overallStatus: ReadinessLevel;
  m0GateBlocked: boolean;
  blockingReasons: string[];
}
