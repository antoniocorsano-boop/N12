import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const snapshotPath = join(import.meta.dirname, "..", "src", "read-model", "r1-snapshot.json");
const current = readFileSync(snapshotPath, "utf-8");

const { execSync } = await import("node:child_process");
execSync("tsx scripts/generate-snapshot.ts", {
  cwd: join(import.meta.dirname, ".."),
  stdio: "pipe",
});

const regenerated = readFileSync(snapshotPath, "utf-8");

if (current === regenerated) {
  console.log("snapshot:check PASS — committed snapshot matches regenerated output");
  process.exit(0);
} else {
  console.error("snapshot:check FAIL — committed snapshot differs from regenerated output");
  console.error("  Run 'npm run snapshot:generate' to update, then commit the change.");
  process.exit(1);
}
