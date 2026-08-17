import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const FOGLIO = join(import.meta.dirname, "..", "..");
const CANONICAL = join(ROOT, "data", "canonical");

function read(rel: string): string {
  const p = join(FOGLIO, rel);
  if (!existsSync(p)) throw new Error(`Missing FOGLIO: ${p}`);
  return readFileSync(p, "utf-8");
}

function readCanonical(filename: string): string {
  const p = join(CANONICAL, filename);
  if (!existsSync(p)) throw new Error(`Missing CANONICAL: ${p}`);
  return readFileSync(p, "utf-8");
}

function parseCsv(content: string): { headers: string[]; rows: Record<string, string>[] } {
  const lines = content.split("\n").filter((l) => l.trim());
  if (lines.length < 2) return { headers: [], rows: [] };
  const sep = lines[0].includes(";") ? ";" : ",";
  const headers = lines[0].split(sep).map((h) => h.trim());
  const rows = lines.slice(1).map((line) => {
    const cells = line.split(sep).map((c) => c.trim().replace(/^"|"$/g, ""));
    const row: Record<string, string> = {};
    headers.forEach((h, i) => (row[h] = cells[i] ?? ""));
    return row;
  });
  return { headers, rows };
}

interface MdTable {
  headers: string[];
  rows: string[][];
}

function parseMdTable(content: string, startLine: number): MdTable | null {
  const lines = content.split("\n");
  let i = startLine;
  while (i < lines.length && !lines[i].trim().startsWith("|")) i++;
  if (i >= lines.length) return null;

  const parseRow = (line: string): string[] =>
    line
      .split("|")
      .slice(1, -1)
      .map((c) => c.trim());

  const headers = parseRow(lines[i]);
  i++;

  if (i < lines.length && /^\|[\s\-:|]+\|$/.test(lines[i])) i++;

  const rows: string[][] = [];
  while (i < lines.length && lines[i].trim().startsWith("|")) {
    const cells = parseRow(lines[i]);
    if (cells.length === headers.length) rows.push(cells);
    i++;
  }

  return { headers, rows };
}

function parseAllTables(content: string): MdTable[] {
  const tables: MdTable[] = [];
  const lines = content.split("\n");
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().startsWith("|")) {
      const t = parseMdTable(content, i);
      if (t && t.rows.length > 0) {
        tables.push(t);
        while (i < lines.length && lines[i].trim().startsWith("|")) i++;
        i--;
      }
    }
  }
  return tables;
}

/* ─── Evidences ─── */
interface Evidence {
  id: string;
  scope: string;
  description: string;
  status: string;
  source: string;
  note: string;
}

function parseEvidences(): Evidence[] {
  const md = read("REGISTRO_EVIDENZE.md");
  const tables = parseAllTables(md);
  const evs: Evidence[] = [];

  for (const t of tables) {
    if (t.headers[0] !== "ID") continue;
    for (const row of t.rows) {
      if (!row[0].startsWith("EV-")) continue;
      evs.push({
        id: row[0],
        scope: row[1],
        description: row[2],
        status: row[3],
        source: row[4],
        note: row[5] ?? "",
      });
    }
  }
  return evs;
}

/* ─── Artifacts ─── */
interface Artifact {
  id: string;
  name: string;
  path: string;
  status: string;
  provenance: string;
  front: string;
  evidenceIds: string[];
}

function parseArtifacts(): Artifact[] {
  const md = read("MATRICE_ARTEFATTI.md");
  const tables = parseAllTables(md);
  const arts: Artifact[] = [];

  for (const t of tables) {
    if (t.headers[0] !== "ID") continue;
    for (const row of t.rows) {
      if (
        !row[0].startsWith("AP-") &&
        !row[0].startsWith("AF-") &&
        !row[0].startsWith("AD-") &&
        !row[0].startsWith("AZ-") &&
        !row[0].startsWith("AM-") &&
        !row[0].startsWith("AT-") &&
        !row[0].startsWith("FF-")
      )
        continue;

      const evCell = row.length >= 7 ? row[6] : "—";
      const evidenceIds =
        evCell === "—" || evCell === ""
          ? []
          : evCell
              .split(",")
              .map((s) => s.trim())
              .filter((s) => s.startsWith("EV-") && !s.includes("*"));

      arts.push({
        id: row[0],
        name: row[1],
        path: row[2],
        status: row[3],
        provenance: row[4],
        front: row[5],
        evidenceIds,
      });
    }
  }
  return arts;
}

/* ─── Residuals ─── */
interface Residual {
  id: string;
  type: string;
  front: string;
  description: string;
  state: string;
  evidenceIds: string[];
  dependencies: string[];
}

function parseResiduals(): Residual[] {
  const md = read("RESIDUI.md");
  const tables = parseAllTables(md);
  const res: Residual[] = [];

  for (const t of tables) {
    if (t.headers[0] !== "ID") continue;
    for (const row of t.rows) {
      if (!row[0].startsWith("R-")) continue;

      const evCell = row[5] ?? "—";
      const evidenceIds =
        evCell === "—" || evCell === ""
          ? []
          : evCell
              .split(",")
              .map((s) => s.trim())
              .filter((s) => s.startsWith("EV-"));

      const depCell = row[6] ?? "";
      const dependencies =
        depCell === "—" || depCell === ""
          ? []
          : depCell.split(",").map((s) => s.trim());

      res.push({
        id: row[0],
        type: row[1],
        front: row[2],
        description: row[3],
        state: row[4],
        evidenceIds,
        dependencies,
      });
    }
  }
  return res;
}

/* ─── Fronts ─── */
interface Front {
  id: string;
  name: string;
  status: string;
  evidenceCount: number;
  residualCount: number;
  blockingResiduals: number;
  nextAction: string;
}

function parseFronts(evidences: Evidence[], residuals: Residual[]): Front[] {
  const frontDir = join(FOGLIO, "fronti");
  const fronts: Front[] = [];

  const defs: { id: string; name: string; nextAction: string }[] = [
    { id: "F0", name: "Progetto / Committenza", nextAction: "Formalizzare committenza nel protocollo" },
    { id: "F1", name: "Fonti / Quadro Conoscitivo", nextAction: "Verificare integrità archivio v25" },
    { id: "F2", name: "Stato di fatto strutturale", nextAction: "Raccordo 57 nodi topologici" },
    { id: "F3", name: "Modello globale M0-G", nextAction: "Normalizzare coordinate e costruire rete globale" },
    { id: "F4", name: "Sezioni e armature M0-S/A", nextAction: "Completare M0-G prima di assegnare sezioni puntuali" },
    { id: "F5", name: "Materiali, conoscenza, carichi", nextAction: "Raccogliere dati materiali e definire LC/FC" },
    { id: "F6", name: "Diagnosi", nextAction: "In attesa di M0-G + M0-S completi" },
    { id: "F7", name: "Interventi", nextAction: "In attesa di diagnosi" },
    { id: "F8", name: "Verifica normativa M0-V", nextAction: "In attesa di M0-L e modello validato" },
    { id: "F9", name: "Progettazione interventi M1", nextAction: "In attesa di M0-V e diagnosi" },
    { id: "F10", name: "Esecuzione / Cantiere", nextAction: "Fuori scope fase R1" },
    { id: "F11", name: "Post operam", nextAction: "Fuori scope fase R1" },
    { id: "F12", name: "Fascicolo finale", nextAction: "Compilazione ultima dopo tutti i fronti" },
  ];

  for (const def of defs) {
    const fPath = join(frontDir, `${def.id}_*.md`);
    let status = "NOT STARTED";
    if (existsSync(join(frontDir))) {
      const files = readdirSync(frontDir).filter((f) => f.startsWith(def.id + "_"));
      if (files.length > 0) {
        const content = read(join("fronti", files[0]));
        const statusMatch = content.match(/##\s*Stato\s*\n\s*(.+)/i);
        if (statusMatch) status = statusMatch[1].trim();
      }
    }

    const evCount = evidences.filter((e) => {
      const src = e.source.toLowerCase();
      return src.includes(def.id.toLowerCase());
    }).length;

    const resCount = residuals.filter((r) => r.front === def.id).length;
    const blocking = residuals.filter(
      (r) => r.front === def.id && (r.type === "BLOCCANTE" || r.type === "RISCHIO") && r.state !== "CHIUSO"
    ).length;

    fronts.push({
      id: def.id,
      name: def.name,
      status,
      evidenceCount: evCount,
      residualCount: resCount,
      blockingResiduals: blocking,
      nextAction: def.nextAction,
    });
  }
  return fronts;
}

/* ─── Pipeline ─── */
function buildPipeline(): { id: string; name: string; fronts: string[]; status: string }[] {
  return [
    { id: "progetto", name: "Progetto", fronts: ["F0"], status: "PARTIAL" },
    { id: "fonti", name: "Fonti", fronts: ["F1"], status: "ADVANCING" },
    { id: "stato-fatto", name: "Stato di fatto", fronts: ["F2"], status: "ADVANCING" },
    { id: "modello", name: "Modello", fronts: ["F3", "F4", "F5"], status: "IN CORSO" },
    { id: "diagnosi", name: "Diagnosi", fronts: ["F6"], status: "BLOCKED" },
    { id: "interventi", name: "Interventi", fronts: ["F7", "F8", "F9"], status: "BLOCKED" },
    { id: "verifica", name: "Verifica", fronts: ["F8"], status: "BLOCKED" },
    { id: "post-operam", name: "Post operam", fronts: ["F11"], status: "N/A" },
    { id: "fascicolo", name: "Fascicolo", fronts: ["F12"], status: "BLOCKED" },
  ];
}

/* ─── Next global action ─── */
function nextGlobalAction(residuals: Residual[]): string {
  const blocking = residuals
    .filter((r) => r.type === "BLOCCANTE" && r.state === "BLOCCATO")
    .sort((a, b) => a.id.localeCompare(b.id));
  if (blocking.length === 0) return "Nessun residuo bloccante aperto";
  const top = blocking[0];
  return `${top.id}: ${top.description} — lavoro sul modello strutturale canonico, rispetta il gate M0-G.`;
}

/* ─── Evidence counts ─── */
function evidenceCounts(evidences: Evidence[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const e of evidences) {
    counts[e.status] = (counts[e.status] ?? 0) + 1;
  }
  return counts;
}

/* ─── Building data from canonical CSVs ─── */
interface CsvRow {
  [key: string]: string;
}

function buildBuilding() {
  // 1. Read nodes (27 chains with coordinates)
  const nodesCsv = parseCsv(readCanonical("nodes.csv"));
  const nodesMap = new Map<string, CsvRow>();
  for (const row of nodesCsv.rows) nodesMap.set(row.node_id, row);

  // 2. Read column fixed lines (section data per chain)
  const colCsv = parseCsv(readCanonical("column_fixed_lines.csv"));
  const colMap = new Map<string, CsvRow>();
  for (const row of colCsv.rows) colMap.set(row.column_chain_id, row);

  // 3. Read telaio 5 (frame data)
  const t5Csv = parseCsv(readCanonical("telaio_5.csv"));
  const t5Levels = t5Csv.rows;

  // 4. Read storey heights
  const heightCsv = parseCsv(readCanonical("storey_height_status.csv"));
  const heightRow = heightCsv.rows[0];
  const storeyHeight = heightRow ? parseFloat(heightRow.value_m) || 3.2 : 3.2;
  const heightStatus = (heightRow?.evidence_status ?? "RIF") as string;

  // 5. Read pillar assignment status
  const pillarCsv = parseCsv(readCanonical("pillar_section_assignment_status.csv"));
  const pillarRow = pillarCsv.rows.find((r) => r.scope === "ALL_27_CHAINS");
  const pillarStatus = pillarRow?.status ?? "ND";

  // Build levels
  const levels = ["G1", "G2", "G3", "G4", "G5"].map((id, i) => ({
    id,
    label: `Piano ${id}`,
    height_m: storeyHeight,
    height_status: heightStatus as any,
    chainCount: 27,
  }));

  // Build chains from nodes
  const chains = Array.from(nodesMap.values()).map((node) => {
    const chainId = node.chain_id;
    const nodeId = node.node_id;

    // Find T5 data for this chain's node range
    const nodeNum = parseInt(nodeId.replace("N", ""), 10);
    const t5Level = t5Levels.find((t) => {
      const range = t.nodi.split("-");
      const lo = parseInt(range[0], 10);
      const hi = parseInt(range[1], 10);
      return nodeNum >= lo && nodeNum <= hi;
    });

    // Find column fixed line data
    const colData = colMap.get(chainId);

    // Map section data from T5 or column data
    const sectionBase = colData?.section_base ?? "ND";
    const sectionTop = colData?.section_top ?? "ND";
    const continuity = colData?.continuity_status ?? "ND";

    const evIds: string[] = ["EV-G01", "EV-P02"];
    if (t5Level) evIds.push("EV-T07");
    if (colData) evIds.push("EV-S05");

    const levels_data = ["G1", "G2", "G3", "G4", "G5"].map((lev) => {
      const inT5 = t5Level && t5Level.livello === lev;
      return {
        level: lev,
        section: inT5
          ? { value: t5Level.sezioni, status: "DOC" as const, source: t5Level.provenienza, evidenceId: "EV-T07" }
          : colData
            ? { value: sectionBase === "ND" ? "ND" : `${sectionBase}`, status: sectionBase === "ND" ? ("ND" as const) : ("DOC_PARZIALE" as const), source: colData.source_ref ?? "CATENE_VERTICALI_PILASTRI_v20", evidenceId: "EV-S05" }
            : undefined,
        frame: inT5
          ? { value: "T5", status: "DOC" as const, source: t5Level.provenienza, evidenceId: "EV-T07" }
          : undefined,
        spans: inT5
          ? { value: t5Level.campate, status: "DOC" as const, source: t5Level.provenienza, evidenceId: "EV-T07" }
          : undefined,
        development: inT5
          ? { value: parseFloat(t5Level.sviluppo_m) || 0, status: "DOC" as const, source: t5Level.provenienza, evidenceId: "EV-T07" }
          : undefined,
      };
    });

    return {
      nodeId,
      chainId,
      axisX: node.axis_x_geom,
      axisY: node.axis_y_geom,
      coordinates: { x_mm: parseFloat(node.x_mm) || 0, y_mm: parseFloat(node.y_mm) || 0 },
      levels: levels_data,
      evidenceIds: [...new Set(evIds)],
      residualIds: [] as string[],
    };
  });

  // Assign residuals to chains based on R-1A-06 (section assignment)
  for (const chain of chains) {
    const hasNd = chain.levels.some((l) => l.section?.value === "ND" || l.section?.status === "ND");
    if (hasNd) chain.residualIds.push("R-1A-06");
  }

  // Build frames
  const frames = [
    {
      id: "T5",
      name: "Telaio 5 (S-S'-T-U-V-Z-A'-B'-C')",
      levels: ["G1", "G2", "G3", "G4", "G5"],
      documented: true,
      evidenceIds: ["EV-T04", "EV-T05", "EV-T06", "EV-T07"],
    },
  ];

  return {
    levels,
    chains,
    frames,
    totalChainLevelEntities: 27 * 5,
  };
}

/* ─── Canonical Structural Model (E4) ─── */
function buildCanonicalModel(building: ReturnType<typeof buildBuilding>, residuals: Residual[]) {
  const entities: any[] = [];
  const missing: { entityId: string; property: string; reason: string }[] = [];

  // Build entities from building chains
  for (const chain of building.chains) {
    // Column entity (observed layer)
    const colProps: any[] = [
      { key: "nodeId", label: "Nodo", layer: "observed", value: chain.nodeId, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" },
      { key: "chainId", label: "Catena", layer: "observed", value: chain.chainId, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" },
      { key: "axisX", label: "Asse X", layer: "observed", value: chain.axisX, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" },
      { key: "axisY", label: "Asse Y", layer: "observed", value: chain.axisY, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" },
      { key: "x_mm", label: "X (mm)", layer: "observed", value: chain.coordinates.x_mm, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" },
      { key: "y_mm", label: "Y (mm)", layer: "observed", value: chain.coordinates.y_mm, status: "VER_GEOMETRIC", source: "CATENE_VERTICALI_PILASTRI_v20.csv", evidenceId: "EV-G01" },
    ];

    // Add level-specific properties
    for (const lev of chain.levels) {
      if (lev.section) {
        colProps.push({ key: `section_${lev.level}`, label: `Sezione ${lev.level}`, layer: "observed", value: lev.section.value, status: lev.section.status, source: lev.section.source, evidenceId: lev.section.evidenceId });
      } else {
        const reason = "Sezione non documentata per questo livello";
        colProps.push({ key: `section_${lev.level}`, label: `Sezione ${lev.level}`, layer: "observed", value: null, status: "ND", source: "—", missingReason: reason });
        missing.push({ entityId: `N12.column.${lev.level}.${chain.chainId}`, property: `section_${lev.level}`, reason });
      }
      if (lev.frame) {
        colProps.push({ key: `frame_${lev.level}`, label: `Trave ${lev.level}`, layer: "observed", value: lev.frame.value, status: lev.frame.status, source: lev.frame.source, evidenceId: lev.frame.evidenceId });
      }
      // Material: always ND (E4 — no completions)
      colProps.push({ key: `material_${lev.level}`, label: `Materiale ${lev.level}`, layer: "observed", value: null, status: "ND", source: "—", missingReason: "Materiali non indagati" });
      missing.push({ entityId: `N12.column.${lev.level}.${chain.chainId}`, property: `material_${lev.level}`, reason: "Materiali non indagati" });
      // Reinforcement: always ND
      colProps.push({ key: `reinforcement_${lev.level}`, label: `Armatura ${lev.level}`, layer: "observed", value: null, status: "ND", source: "—", missingReason: "Armature non documentate" });
      missing.push({ entityId: `N12.column.${lev.level}.${chain.chainId}`, property: `reinforcement_${lev.level}`, reason: "Armature non documentate" });
    }

    entities.push({
      id: { raw: `N12.column.*.${chain.chainId}`, entityType: "column", chain: chain.chainId },
      name: `Pilastro ${chain.chainId}`,
      layer: "observed",
      properties: colProps,
      parent: `N12.building.N12`,
      evidenceIds: chain.evidenceIds,
      residualIds: chain.residualIds,
    });
  }

  // Missing properties summary
  const blockingResiduals = residuals
    .filter((r) => r.type === "BLOCCANTE" && r.state !== "CHIUSO")
    .map((r) => r.id);

  return {
    schemaVersion: "N12-CSM-0001",
    generatedAt: new Date().toISOString().slice(0, 10),
    sourceRevision: "e489225",
    gate: "M0-G",
    entities,
    missingProperties: missing,
    blockingResiduals,
  };
}

/* ─── Readiness Matrix (E6) ─── */
function buildReadiness(model: ReturnType<typeof buildCanonicalModel>, residuals: Residual[]) {
  const chains = model.entities.filter((e: any) => e.id.entityType === "column");
  const total = chains.length;
  const levels = ["G1", "G2", "G3", "G4", "G5"];

  function countForDomain(domain: string): { available: number; missing: string[]; status: string } {
    let available = 0;
    const miss: string[] = [];
    for (const chain of chains) {
      const props = chain.properties;
      const relevant = props.filter((p: any) => p.key.includes(domain));
      if (relevant.length === 0) {
        miss.push(`${chain.name}: non applicabile`);
        continue;
      }
      const hasDoc = relevant.some((p: any) => p.status.startsWith("DOC") || p.status.startsWith("VER") || p.status === "RIF");
      const allNd = relevant.every((p: any) => p.status === "ND");
      if (hasDoc) available++;
      else if (allNd) miss.push(`${chain.name}: ND`);
      else miss.push(`${chain.name}: parziale`);
    }
    const status = available === total ? "COMPLETO" : available > 0 ? "PARZIALE" : "ND";
    return { available, missing: miss.slice(0, 5), status };
  }

  const geom = countForDomain("x_mm");
  const sect = countForDomain("section");
  const mat = countForDomain("material");
  const reinf = countForDomain("reinforcement");

  const cells = [
    { domain: "geometria" as const, label: "Geometria", level: geom.status as any, available: geom.available, total, missing: geom.missing, evidenceStatus: "VER_GEOMETRIC" as const },
    { domain: "topologia" as const, label: "Topologia", level: "ND" as const, available: 0, total, missing: ["57 nodi topologici: PREDOC_TOPOLOGICO, non verificati"], evidenceStatus: "PREDOC_TOPOLOGICO" as const },
    { domain: "sezioni" as const, label: "Sezioni", level: sect.status as any, available: sect.available, total, missing: sect.missing, evidenceStatus: "DOC_PARZIALE" as const },
    { domain: "armature" as const, label: "Armature", level: "ND" as const, available: 0, total, missing: ["Nessuna armatura documentata"], evidenceStatus: "ND" as const },
    { domain: "materiali" as const, label: "Materiali", level: "ND" as const, available: 0, total, missing: ["Materiali non indagati"], evidenceStatus: "ND" as const },
    { domain: "fondazioni" as const, label: "Fondazioni", level: "PARZIALE" as const, available: 7, total: 27, missing: ["7 catene fondazioni ricostruite, 20 mancanti"], evidenceStatus: "DOC-ARTEFATTO" as const },
    { domain: "carichi" as const, label: "Carichi", level: "ND" as const, available: 0, total: 0, missing: ["Carichi non definiti"], evidenceStatus: "ND" as const },
    { domain: "lc_fc" as const, label: "LC/FC", level: "ND" as const, available: 0, total: 0, missing: ["Livello di conoscenza non definito"], evidenceStatus: "ND" as const },
  ];

  const blockingReasons = residuals
    .filter((r) => r.type === "BLOCCANTE" && r.state !== "CHIUSO")
    .map((r) => `${r.id}: ${r.description}`);

  return {
    cells,
    overallStatus: "BLOCCATO" as const,
    m0GateBlocked: true,
    blockingReasons,
  };
}

/* ─── Adapter Status (E5) ─── */
function buildAdapters(): any[] {
  return [
    {
      id: "edilus",
      name: "EdiLus-EE",
      state: "BLOCKED",
      description: "Esportazione modello EdiLus per verifica normativa",
      requiredProperties: [
        { property: "geometria", required: true, currentStatus: "VER_GEOMETRIC" },
        { property: "sezioni", required: true, currentStatus: "DOC_PARZIALE", blocker: "Sezioni non assegnate a tutte le 27 catene" },
        { property: "armature", required: true, currentStatus: "ND", blocker: "Armature non documentate" },
        { property: "materiali", required: true, currentStatus: "ND", blocker: "Materiali non indagati" },
        { property: "carichi", required: true, currentStatus: "ND", blocker: "Carichi non definiti" },
        { property: "lc_fc", required: true, currentStatus: "ND", blocker: "LC/FC non definito" },
      ],
      blockingProperties: ["sezioni", "armature", "materiali", "carichi", "lc_fc"],
    },
    {
      id: "bim_ifc",
      name: "usBIM / IFC",
      state: "BLOCKED",
      description: "Esportazione modello BIM per coordinamento",
      requiredProperties: [
        { property: "geometria", required: true, currentStatus: "VER_GEOMETRIC" },
        { property: "sezioni", required: true, currentStatus: "DOC_PARZIALE", blocker: "Sezioni non complete" },
        { property: "materiali", required: false, currentStatus: "ND" },
      ],
      blockingProperties: ["sezioni"],
    },
    {
      id: "fem",
      name: "FEM (OpenSees / altro)",
      state: "BLOCKED",
      description: "Analisi numerica per verifiche sismiche",
      requiredProperties: [
        { property: "geometria", required: true, currentStatus: "VER_GEOMETRIC" },
        { property: "topologia", required: true, currentStatus: "PREDOC_TOPOLOGICO", blocker: "57 nodi: PREDOC, non verificati" },
        { property: "sezioni", required: true, currentStatus: "DOC_PARZIALE", blocker: "Sezioni non assegnate" },
        { property: "armature", required: true, currentStatus: "ND", blocker: "Armature non documentate" },
        { property: "materiali", required: true, currentStatus: "ND", blocker: "Materiali non indagati" },
        { property: "connettivita", required: true, currentStatus: "INF_DA_QUOTARE", blocker: "141 connessioni candidate, non verificate" },
        { property: "vincoli", required: true, currentStatus: "PLACEHOLDER", blocker: "Solo base incastrata (placeholder)" },
        { property: "carichi", required: true, currentStatus: "ND", blocker: "Carichi non definiti" },
      ],
      blockingProperties: ["topologia", "sezioni", "armature", "materiali", "connettivita", "vincoli", "carichi"],
    },
  ];
}

/* ─── Knowledge Graph (F2) ─── */
function buildKnowledgeGraph(building: ReturnType<typeof buildBuilding>) {
  const nodes: any[] = [];
  const edges: any[] = [];

  // Building node
  nodes.push({ id: "N12", type: "building", name: "N12", metadata: {} });

  // Level nodes
  for (const lev of building.levels) {
    nodes.push({ id: `N12.level.${lev.id}`, type: "level", name: lev.label, metadata: { height_m: lev.height_m } });
    edges.push({ source: "N12", target: `N12.level.${lev.id}`, type: "contains", weight: 1, documented: true });
  }

  // Chain/column nodes
  for (const chain of building.chains) {
    const colId = `N12.column.${chain.chainId}`;
    nodes.push({ id: colId, type: "column", name: `Pilastro ${chain.chainId}`, metadata: { x_mm: chain.coordinates.x_mm, y_mm: chain.coordinates.y_mm } });

    // Link to building
    edges.push({ source: "N12", target: colId, type: "contains", weight: 1, documented: true });

    // Vertical continuity (same chain, different levels)
    for (let i = 0; i < chain.levels.length - 1; i++) {
      const above = `${colId}.${chain.levels[i].level}`;
      const below = `${colId}.${chain.levels[i + 1].level}`;
      edges.push({ source: above, target: below, type: "same_chain", weight: 0.9, documented: true });
    }

    // Level membership
    for (const lev of chain.levels) {
      const levColId = `${colId}.${lev.level}`;
      edges.push({ source: `N12.level.${lev.level}`, target: levColId, type: "contains", weight: 1, documented: true });

      // Frame membership
      if (lev.frame) {
        const frameId = `N12.frame.${lev.frame.value}`;
        if (!nodes.find((n) => n.id === frameId)) {
          nodes.push({ id: frameId, type: "frame", name: `Telaio ${lev.frame.value}`, metadata: {} });
        }
        edges.push({ source: levColId, target: frameId, type: "same_frame", weight: 0.8, documented: true });
      }
    }

    // Same-level relationships (all columns on same floor)
    for (const lev of chain.levels) {
      edges.push({ source: colId, target: `N12.level.${lev.level}`, type: "same_level", weight: 0.5, documented: false });
    }
  }

  // Frame nodes
  for (const frame of building.frames) {
    if (!nodes.find((n) => n.id === `N12.frame.${frame.id}`)) {
      nodes.push({ id: `N12.frame.${frame.id}`, type: "frame", name: frame.name, metadata: {} });
    }
  }

  return { nodes, edges };
}

/* ─── Document Knowledge Layer (F3) ─── */
function buildDocumentLayer() {
  const sources = [
    { id: "DOC nodes.csv", name: "Nodi 27 catene", type: "csv_canonical" as const, path: "data/canonical/nodes.csv", description: "Coordinate X/Y delle 27 catene verticali", propertiesProvided: ["position", "axisX", "axisY", "chainId"], elementTypes: ["column" as const], evidenceStatus: "VER_GEOMETRIC" as const },
    { id: "DOC column_fixed_lines.csv", name: "Fili fissi pilastri", type: "csv_canonical" as const, path: "data/canonical/column_fixed_lines.csv", description: "Fili fissi geometrici e sezioni documentate", propertiesProvided: ["section", "continuity", "fixedLine"], elementTypes: ["column" as const], evidenceStatus: "PREDOC_GEOMETRICO" as const },
    { id: "DOC telaio_5.csv", name: "Telaio 5 geometria", type: "csv_canonical" as const, path: "data/canonical/telaio_5.csv", description: "Campate, sviluppi e sezioni di T5", propertiesProvided: ["section", "spans", "development", "frame"], elementTypes: ["column" as const, "beam" as const], evidenceStatus: "DOC" as const },
    { id: "DOC storey_height_status.csv", name: "Altezza interpiano", type: "csv_canonical" as const, path: "data/canonical/storey_height_status.csv", description: "Altezza estradosso-estradosso 3.20m", propertiesProvided: ["height"], elementTypes: ["level" as const], evidenceStatus: "RIF" as const },
    { id: "DOC pillar_section_assignment_status.csv", name: "Assegnazione pilastri", type: "csv_canonical" as const, path: "data/canonical/pillar_section_assignment_status.csv", description: "Stato assegnazione sezioni a 27 catene", propertiesProvided: ["section_assignment"], elementTypes: ["column" as const], evidenceStatus: "ND" as const },
    { id: "DOC tav5_topology_nodes_57.csv", name: "Topologia 57 nodi", type: "csv_canonical" as const, path: "data/canonical/tav5_topology_nodes_57.csv", description: "57 nodi topologici TAV.5", propertiesProvided: ["topology"], elementTypes: ["node" as const], evidenceStatus: "PREDOC_TOPOLOGICO" as const },
    { id: "DOC tav5_topology_connections_v07.csv", name: "141 connessioni", type: "csv_canonical" as const, path: "data/canonical/tav5_topology_connections_v07.csv", description: "Connessioni candidate TAV.5", propertiesProvided: ["connectivity"], elementTypes: ["beam" as const, "span" as const], evidenceStatus: "INF_DA_QUOTARE" as const },
    { id: "DOC telaio5_tav5_candidate_matrix_v1.csv", name: "Candidati T5↔TAV.5", type: "csv_canonical" as const, path: "data/canonical/telaio5_tav5_candidate_matrix_v1.csv", description: "Matrice candidati allineamento T5 con TAV.5", propertiesProvided: ["alignment"], elementTypes: ["frame" as const], evidenceStatus: "INF" as const },
    { id: "DOC fem_section_placeholders.csv", name: "Sezioni FEM placeholder", type: "csv_canonical" as const, path: "data/canonical/fem_section_placeholders.csv", description: "Sezioni placeholder per smoke-test FEM", propertiesProvided: ["section_fem"], elementTypes: ["column" as const, "beam" as const], evidenceStatus: "PLACEHOLDER_GEOMETRY_ONLY" as const },
    { id: "REGISTRO_EVIDENZE", name: "Registro Evidenze", type: "evidence_register" as const, path: "docs/FOGLIO_LAVORO/REGISTRO_EVIDENZE.md", description: "28 evidenze strutturali con stato e fonte", propertiesProvided: [], elementTypes: ["column" as const, "beam" as const, "level" as const, "building" as const], evidenceStatus: "DOC" as const },
    { id: "RESIDUI", name: "Residui", type: "fascicolo" as const, path: "docs/FOGLIO_LAVORO/RESIDUI.md", description: "16 residui aperti con dipendenze", propertiesProvided: [], elementTypes: ["column" as const, "beam" as const, "building" as const], evidenceStatus: "DOC" as const },
  ];

  const propertyIndex: Record<string, string[]> = {};
  for (const src of sources) {
    for (const prop of src.propertiesProvided) {
      if (!propertyIndex[prop]) propertyIndex[prop] = [];
      propertyIndex[prop].push(src.id);
    }
  }

  const elementTypeIndex: Record<string, string[]> = {};
  for (const src of sources) {
    for (const et of src.elementTypes) {
      if (!elementTypeIndex[et]) elementTypeIndex[et] = [];
      elementTypeIndex[et].push(src.id);
    }
  }

  return { sources, propertyIndex, elementTypeIndex };
}

/* ─── Resolved Properties (F4) ─── */
function buildResolvedProperties(building: ReturnType<typeof buildBuilding>, docLayer: any) {
  const resolved: any[] = [];

  for (const chain of building.chains) {
    for (const lev of chain.levels) {
      const entityId = `N12.column.${lev.level}.${chain.chainId}`;

      // Position — always resolved from nodes.csv
      resolved.push({
        key: `position_${lev.level}_${chain.chainId}`, entityId, label: `Posizione ${chain.chainId} ${lev.level}`, layer: "observed",
        resolution: "VALIDATED", evidenceStatus: "VER_GEOMETRIC",
        value: `${chain.coordinates.x_mm}, ${chain.coordinates.y_mm}`,
        candidates: [{ id: `C-pos-${chain.chainId}-${lev.level}`, value: `${chain.coordinates.x_mm}, ${chain.coordinates.y_mm}`, evidenceStatus: "VER_GEOMETRIC", sourceId: "DOC nodes.csv", sourceType: "csv_canonical", confidence: 1, reasoning: `Coordinate dirette da nodes.csv (catena ${chain.chainId})` }],
        sourceIds: ["DOC nodes.csv"], confidence: 1, lastResolved: new Date().toISOString().slice(0, 10),
      });

      // Section — resolved ONLY if in T5 with actual value (not ND)
      const hasRealSection = lev.section && lev.section.value && lev.section.value !== "ND";
      if (hasRealSection) {
        resolved.push({
          key: `section_${lev.level}_${chain.chainId}`, entityId, label: `Sezione ${chain.chainId} ${lev.level}`, layer: "observed",
          resolution: "VALIDATED", evidenceStatus: lev.section.status,
          value: lev.section.value,
          candidates: [{ id: `C-sec-${chain.chainId}-${lev.level}`, value: lev.section.value, evidenceStatus: lev.section.status, sourceId: "DOC telaio_5.csv", sourceType: "csv_canonical", confidence: 0.9, reasoning: `Sezione documentata da telaio_5.csv (catena ${chain.chainId}, ${lev.level})` }],
          sourceIds: ["DOC telaio_5.csv"], confidence: 0.9, lastResolved: new Date().toISOString().slice(0, 10),
        });
      } else {
        // No section or ND — try analogical resolution from same-frame, same-level columns
        const sameFrameChains = building.chains.filter((c) =>
          c.nodeId !== chain.nodeId &&
          c.levels.some((l) => l.frame?.value && l.level === lev.level && l.section?.value && l.section.value !== "ND")
        );
        const analogicalCandidates = sameFrameChains
          .slice(0, 3)
          .map((c) => {
            const cLev = c.levels.find((l) => l.level === lev.level);
            return {
              value: cLev?.section?.value ?? null,
              status: cLev?.section?.status ?? "ND",
              chain: c.chainId,
              frame: cLev?.frame?.value ?? "?",
            };
          })
          .filter((c) => c.value && c.value !== "ND");

        const resolution = analogicalCandidates.length > 0 ? "CANDIDATES" : "UNKNOWN";
        const candidates = analogicalCandidates.map((ac, i) => ({
          id: `C-sec-analog-${chain.chainId}-${lev.level}-${i}`,
          value: ac.value,
          evidenceStatus: ac.status as any,
          sourceId: "analogy",
          sourceType: "csv_derived" as const,
          confidence: 0.4,
          reasoning: `Analogia con catena ${ac.chain} (livello ${lev.level}, telaio ${ac.frame})`,
          analogicalOrigin: ac.chain,
        }));

        resolved.push({
          key: `section_${lev.level}_${chain.chainId}`, entityId, label: `Sezione ${chain.chainId} ${lev.level}`, layer: "observed",
          resolution, evidenceStatus: "ND",
          value: null, candidates, sourceIds: [], confidence: candidates.length > 0 ? 0.4 : 0,
          searchHint: resolution === "UNKNOWN"
            ? "Cercare sezione in tavole originali o raccordi strutturali"
            : "Candidato analogico da validare contro documentazione",
          unknownClassification: resolution === "UNKNOWN" ? "DOCUMENT_SEARCHABLE" : undefined,
          requiredForGate: false,
          lastResolved: new Date().toISOString().slice(0, 10),
        });
      }

      // Material — UNKNOWN (no source in current CSVs)
      resolved.push({
        key: `material_${lev.level}_${chain.chainId}`, entityId, label: `Materiale ${chain.chainId} ${lev.level}`, layer: "observed",
        resolution: "UNKNOWN", evidenceStatus: "ND",
        value: null, candidates: [], sourceIds: [], confidence: 0,
        searchHint: "Verificare certificati fornitura, relazioni di prova, schede materiali negli archivi",
        unknownClassification: "DOCUMENT_SEARCHABLE",
        requiredForGate: false,
        lastResolved: new Date().toISOString().slice(0, 10),
      });

      // Reinforcement — UNKNOWN (no source in current CSVs)
      resolved.push({
        key: `reinforcement_${lev.level}_${chain.chainId}`, entityId, label: `Armatura ${chain.chainId} ${lev.level}`, layer: "observed",
        resolution: "UNKNOWN", evidenceStatus: "ND",
        value: null, candidates: [], sourceIds: [], confidence: 0,
        searchHint: "Verificare calcoli di progetto originali, dettagli armatura, o indagini destructive",
        unknownClassification: "REQUIRES_NEW_EVIDENCE",
        requiredForGate: false,
        lastResolved: new Date().toISOString().slice(0, 10),
      });
    }
  }

  return resolved;
}

/* ─── Validation Queue (F5) ─── */
function buildValidationQueue(resolved: any[], residuals: any[]) {
  const items = resolved
    .filter((r) => r.resolution === "CANDIDATES" || r.resolution === "CONFLICT" || r.resolution === "UNKNOWN")
    .map((r) => ({
      id: `VQ-${r.key}`,
      entityId: r.entityId ?? r.key,
      entityName: r.label ?? r.key,
      propertyKey: r.key,
      propertyLabel: r.label,
      resolution: r.resolution,
      currentValue: r.value,
      proposedValue: r.candidates.length > 0 ? r.candidates[0].value : null,
      evidenceStatus: r.evidenceStatus,
      candidates: r.candidates,
      confidence: r.confidence,
      searchHint: r.searchHint,
      reason: r.resolution === "UNKNOWN"
        ? r.searchHint ?? "Nessuna fonte documentale disponibile per questa proprietà"
        : r.resolution === "CONFLICT"
          ? "Le evidenze candidate sono in conflitto"
          : `${r.candidates.length} candidati trovati, da validare`,
      relatedResiduals: residuals.filter((res: any) => res.evidenceIds?.some((eid: string) => r.sourceIds.includes(eid))).map((res: any) => res.id),
    }));

  const stats = {
    total: resolved.length,
    validated: resolved.filter((r) => r.resolution === "VALIDATED").length,
    candidates: resolved.filter((r) => r.resolution === "CANDIDATES").length,
    unknown: resolved.filter((r) => r.resolution === "UNKNOWN").length,
    proposed: resolved.filter((r) => r.resolution === "PROPOSED").length,
    conflict: resolved.filter((r) => r.resolution === "CONFLICT").length,
    impossible: resolved.filter((r) => r.resolution === "IMPOSSIBLE").length,
    rejected: resolved.filter((r) => r.resolution === "REJECTED").length,
  };

  return { items, stats };
}

/* ─── Validation ─── */
function validate(evidences: Evidence[], artifacts: Artifact[], residuals: Residual[]): void {
  const errors: string[] = [];

  const evIds = new Set<string>();
  for (const e of evidences) {
    if (evIds.has(e.id)) errors.push(`Duplicate evidence ID: ${e.id}`);
    evIds.add(e.id);
  }

  const artIds = new Set<string>();
  for (const a of artifacts) {
    if (artIds.has(a.id)) errors.push(`Duplicate artifact ID: ${a.id}`);
    artIds.add(a.id);
    for (const evId of a.evidenceIds) {
      if (!evIds.has(evId)) errors.push(`Artifact ${a.id} references missing evidence: ${evId}`);
    }
  }

  const resIds = new Set<string>();
  for (const r of residuals) {
    if (resIds.has(r.id)) errors.push(`Duplicate residual ID: ${r.id}`);
    resIds.add(r.id);
    for (const evId of r.evidenceIds) {
      if (!evIds.has(evId)) errors.push(`Residual ${r.id} references missing evidence: ${evId}`);
    }
  }

  if (errors.length > 0) {
    console.error("VALIDATION FAILED:");
    for (const e of errors) console.error(`  ✗ ${e}`);
    process.exit(1);
  }
}

/* ─── Main ─── */
console.log("Reading FOGLIO_LAVORO sources...");

const evidences = parseEvidences();
console.log(`  Evidences: ${evidences.length}`);

const artifacts = parseArtifacts();
console.log(`  Artifacts: ${artifacts.length}`);

const residuals = parseResiduals();
console.log(`  Residuals: ${residuals.length}`);

validate(evidences, artifacts, residuals);
console.log("  Validation: PASS");

const fronts = parseFronts(evidences, residuals);
const pipeline = buildPipeline();
const nextAction = nextGlobalAction(residuals);
const counts = evidenceCounts(evidences);

console.log("Building entity model from canonical CSVs...");
const building = buildBuilding();
console.log(`  Chains: ${building.chains.length}`);
console.log(`  Levels: ${building.levels.length}`);
console.log(`  Chain-level entities: ${building.totalChainLevelEntities}`);

console.log("Building canonical structural model...");
const canonicalModel = buildCanonicalModel(building, residuals);
console.log(`  Entities: ${canonicalModel.entities.length}`);
console.log(`  Missing properties: ${canonicalModel.missingProperties.length}`);

console.log("Building readiness matrix...");
const readiness = buildReadiness(canonicalModel, residuals);
console.log(`  Overall: ${readiness.overallStatus} (M0-G blocked: ${readiness.m0GateBlocked})`);

console.log("Building adapter status...");
const adapters = buildAdapters();
console.log(`  Adapters: ${adapters.map((a) => `${a.id}=${a.state}`).join(", ")}`);

console.log("Building structural knowledge graph...");
const knowledgeGraph = buildKnowledgeGraph(building);
console.log(`  Nodes: ${knowledgeGraph.nodes.length}, Edges: ${knowledgeGraph.edges.length}`);

console.log("Building document knowledge layer...");
const documentLayer = buildDocumentLayer();
console.log(`  Sources: ${documentLayer.sources.length}`);

console.log("Building resolved properties...");
const resolvedProperties = buildResolvedProperties(building, documentLayer);
console.log(`  Properties: ${resolvedProperties.length}`);
console.log(`  Validated: ${resolvedProperties.filter((r) => r.resolution === "VALIDATED").length}`);
console.log(`  Candidates: ${resolvedProperties.filter((r) => r.resolution === "CANDIDATES").length}`);
console.log(`  Unknown: ${resolvedProperties.filter((r) => r.resolution === "UNKNOWN").length}`);

console.log("Building validation queue...");
const validationQueue = buildValidationQueue(resolvedProperties, residuals);
console.log(`  Queue items: ${validationQueue.items.length}`);
console.log(`  Stats: validated=${validationQueue.stats.validated} candidates=${validationQueue.stats.candidates} unknown=${validationQueue.stats.unknown} proposed=${validationQueue.stats.proposed} conflict=${validationQueue.stats.conflict}`);

const snapshot = {
  project: {
    name: "N12 — Edificio esistente in c.a. Ariano Irpino",
    location: "Ariano Irpino (AV)",
    target: "Modello completo EdiLus-EE",
    currentGate: "M0-G (geometria globale)",
    fascicoloVersion: "R1-A-0002 / R1-B RE-0001",
    lastUpdate: new Date().toISOString().slice(0, 10),
  },
  pipeline,
  fronts,
  evidences,
  artifacts,
  residuals,
  evidenceCounts: counts,
  nextGlobalAction: nextAction,
  building,
  canonicalModel,
  readiness,
  adapters,
  knowledgeGraph,
  documentLayer,
  resolvedProperties,
  validationQueue,
};

const outPath = join(import.meta.dirname, "..", "src", "read-model", "r1-snapshot.json");
writeFileSync(outPath, JSON.stringify(snapshot, null, 2) + "\n", "utf-8");
console.log(`  Written: ${outPath}`);
console.log("DONE");
