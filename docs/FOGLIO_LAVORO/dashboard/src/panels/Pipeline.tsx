import type { PipelineStage, Front } from "../read-model/types";

const STATUS_COLORS: Record<string, string> = {
  ADVANCING: "#22c55e",
  PARTIAL: "#eab308",
  "IN CORSO": "#3b82f6",
  BLOCKED: "#ef4444",
  "NOT STARTED": "#9ca3af",
  "N/A": "#d1d5db",
};

export default function Pipeline({ pipeline, fronts }: { pipeline: PipelineStage[]; fronts: Front[] }) {
  const frontMap = new Map(fronts.map((f) => [f.id, f]));
  return (
    <section className="panel panel--pipeline">
      <h2>Pipeline</h2>
      <div className="pipeline">
        {pipeline.map((stage, i) => {
          const stageFronts = stage.fronts.map((fid) => frontMap.get(fid)!);
          const blocking = stageFronts.reduce((a, f) => a + f.blockingResiduals, 0);
          return (
            <div key={stage.id} className="pipeline__stage">
              <div
                className="pipeline__bar"
                style={{ backgroundColor: STATUS_COLORS[stage.status] ?? "#9ca3af" }}
              >
                <span className="pipeline__label">{stage.name}</span>
                {blocking > 0 && <span className="pipeline__badge">{blocking}</span>}
              </div>
              <div className="pipeline__fronts">
                {stageFronts.map((f) => (
                  <span
                    key={f.id}
                    className={`pipeline__front pipeline__front--${f.status.replace(/\s+/g, "-").toLowerCase()}`}
                    title={`${f.name} — ${f.status}`}
                  >
                    {f.id}
                  </span>
                ))}
              </div>
              {i < pipeline.length - 1 && <span className="pipeline__arrow">→</span>}
            </div>
          );
        })}
      </div>
    </section>
  );
}
