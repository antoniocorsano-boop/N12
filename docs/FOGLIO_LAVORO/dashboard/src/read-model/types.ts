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

/* ═══════════════════════════════════════════════════
   R1-F: Intelligent Evidence Resolution
   ═══════════════════════════════════════════════════ */

/* ─── F1: Property Resolution Lifecycle ─── */
export type ResolutionState =
  | "UNKNOWN"        // property not yet investigated
  | "SEARCHING"      // resolver actively querying sources
  | "CANDIDATES"     // one or more candidates found
  | "CONSISTENT"     // candidates agree, proposal ready
  | "CONFLICT"       // candidates disagree, human needed
  | "PROPOSED"       // resolver proposal awaiting validation
  | "VALIDATED"      // human accepted proposal → canonical
  | "REJECTED"       // human rejected proposal
  | "IMPOSSIBLE"     // genuinely cannot be determined from sources
  | "NOT_APPLICABLE"; // property doesn't apply to this element

export interface ResolvedProperty {
  key: string;
  entityId?: string;
  label: string;
  layer: ModelLayer;
  resolution: ResolutionState;
  evidenceStatus: EvidenceStatus;
  value: string | number | null;
  candidates: PropertyCandidate[];
  sourceIds: string[];
  confidence: number; // 0-1, informational only
  lastResolved: string;
  humanNote?: string;
  searchHint?: string;
  unknownClassification?: "DOCUMENT_SEARCHABLE" | "RELATION_SEARCHABLE" | "REQUIRES_HUMAN_INTERPRETATION" | "REQUIRES_NEW_EVIDENCE" | "NOT_REQUIRED_FOR_CURRENT_GATE";
  requiredForGate?: boolean;
}

export interface PropertyCandidate {
  id: string;
  value: string | number;
  evidenceStatus: EvidenceStatus;
  sourceId: string;
  sourceType: DocumentSourceType;
  confidence: number;
  reasoning: string; // how this candidate was derived
  analogicalOrigin?: string; // if derived from similar element
}

/* ─── F2: Structural Knowledge Graph ─── */
export type GraphNodeType =
  | "building"
  | "level"
  | "chain"
  | "column"
  | "beam"
  | "span"
  | "frame"
  | "node"
  | "foundation"
  | "document"
  | "detail"
  | "table";

export type GraphEdgeType =
  | "contains"       // building → level, level → column
  | "part_of"        // column → chain, span → beam
  | "same_chain"     // column_G1 → column_G2 (vertical continuity)
  | "same_frame"     // column → frame, beam → frame
  | "same_level"     // column → column (horizontal, same floor)
  | "same_family"    // columns with same documented section type
  | "connected_to"   // column → beam (structural connection)
  | "documented_by"  // element → document
  | "details"        // document → detail
  | "analogous_to";  // element → similar element (inference path)

export interface KnowledgeGraphNode {
  id: string;
  type: GraphNodeType;
  name: string;
  metadata: Record<string, string | number>;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  type: GraphEdgeType;
  weight: number; // 0-1, strength of relationship
  documented: boolean;
}

export interface StructuralKnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

/* ─── F3: Document Knowledge Layer ─── */
export type DocumentSourceType =
  | "csv_canonical"
  | "csv_derived"
  | "decision"
  | "evidence_register"
  | "fronti"
  | "fascicolo";

export interface DocumentSource {
  id: string;
  name: string;
  type: DocumentSourceType;
  path: string;
  description: string;
  propertiesProvided: string[]; // which element properties this source can answer
  elementTypes: GraphNodeType[]; // which element types this source covers
  evidenceStatus: EvidenceStatus;
}

export interface DocumentKnowledgeLayer {
  sources: DocumentSource[];
  propertyIndex: Record<string, string[]>; // property → source IDs that can answer it
  elementTypeIndex: Record<string, string[]>; // element type → source IDs that cover it
}

/* ─── F4: Query Plan ─── */
export type QueryStrategy =
  | "direct_lookup"    // exact match in a CSV
  | "range_match"      // numeric range search
  | "relational"       // traverse knowledge graph edges
  | "analogical"       // find similar elements, borrow property
  | "hierarchical"     // parent/child containment
  | "document_search"; // search document metadata

export interface QueryStep {
  strategy: QueryStrategy;
  sourceId: string;
  description: string;
  parameters: Record<string, string>;
}

export interface PropertyQueryPlan {
  propertyKey: string;
  elementId: string;
  steps: QueryStep[];
  expectedSources: string[];
}

/* ─── F5: Validation Queue ─── */
export type QueueAction = "ACCEPT" | "REJECT" | "INSPECT" | "DEFER" | "REQUEST_EVIDENCE";

export interface ValidationItem {
  id: string;
  entityId: string;
  entityName: string;
  propertyKey: string;
  propertyLabel: string;
  resolution: ResolutionState;
  currentValue: string | number | null;
  proposedValue: string | number | null;
  evidenceStatus: EvidenceStatus;
  candidates: PropertyCandidate[];
  confidence: number;
  reason: string; // why this needs human attention
  searchHint?: string;
  relatedResiduals: string[];
}

export interface ValidationQueue {
  items: ValidationItem[];
  stats: {
    total: number;
    validated: number;
    candidates: number;
    unknown: number;
    proposed: number;
    conflict: number;
    impossible: number;
    rejected: number;
  };
}

/* ─── Extended R1Snapshot ─── */
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
  knowledgeGraph: StructuralKnowledgeGraph;
  documentLayer: DocumentKnowledgeLayer;
  resolvedProperties: ResolvedProperty[];
  validationQueue: ValidationQueue;
}
