import { useMemo } from "react";
import type { AgentLive, Catalog, CatalogAgent } from "../types";

const COL_W = 214;
const NODE_W = 172;
const NODE_H = 78;
const ROW_H = 104;
const TOP = 26;

export const PHASE_COLORS: Record<number, string> = {
  1: "var(--phase-1)",
  2: "var(--phase-2)",
  3: "var(--phase-3)",
  4: "var(--phase-4)",
  5: "var(--phase-5)",
};

const STATUS_ICON: Record<string, string> = {
  pending: "○",
  running: "◐",
  completed: "✓",
  failed: "✕",
};

interface Props {
  catalog: Catalog;
  agents: Record<string, AgentLive>;
  selected: string | null;
  onSelect: (id: string) => void;
}

export default function PipelineGraph({ catalog, agents, selected, onSelect }: Props) {
  const layout = useMemo(() => computeLayout(catalog), [catalog]);
  const width = catalog.waves * COL_W + 10;
  const height = TOP + layout.maxRows * ROW_H + 10;

  return (
    <div className="dag" style={{ width, height }}>
      <svg width={width} height={height}>
        {layout.edges.map(({ from, to }, i) => {
          const a = layout.pos[from];
          const b = layout.pos[to];
          const x1 = a.x + NODE_W;
          const y1 = a.y + NODE_H / 2;
          const x2 = b.x;
          const y2 = b.y + NODE_H / 2;
          const mx = (x1 + x2) / 2;
          const srcDone = agents[from]?.status === "completed";
          const tgtRunning = agents[to]?.status === "running";
          return (
            <path
              key={i}
              d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
              fill="none"
              stroke={tgtRunning && srcDone ? "var(--running)" : srcDone ? "#52514e" : "var(--grid)"}
              strokeWidth={tgtRunning && srcDone ? 2 : 1.5}
              strokeDasharray={tgtRunning && srcDone ? "6 5" : undefined}
            >
              {tgtRunning && srcDone && (
                <animate attributeName="stroke-dashoffset" from="22" to="0" dur="0.9s" repeatCount="indefinite" />
              )}
            </path>
          );
        })}
      </svg>

      {Array.from({ length: catalog.waves }, (_, w) => (
        <div key={w} className="wave-label" style={{ left: w * COL_W + 8 }}>
          wave {w + 1}
        </div>
      ))}

      {catalog.agents.map((a) => {
        const p = layout.pos[a.id];
        const live = agents[a.id] ?? { status: "pending" as const };
        const cls = ["agent-node", live.status, selected === a.id ? "selected" : ""].join(" ");
        return (
          <div
            key={a.id}
            className={cls}
            style={{ left: p.x, top: p.y, borderLeftColor: PHASE_COLORS[a.phase] }}
            onClick={() => onSelect(a.id)}
            onKeyDown={(e) => e.key === "Enter" && onSelect(a.id)}
            role="button"
            tabIndex={0}
            aria-label={`Agent ${a.num} · ${a.name} — ${live.status}`}
            title={a.description}
          >
            <div className="head">
              <span style={{ color: statusColor(live.status) }}>{STATUS_ICON[live.status]}</span>
              <span>Agent {a.num}</span>
              <span className="icons">
                {a.usesLlm && <span title="calls the LLM">✨</span>}
                {a.isBarrier && <span title="join barrier — waits for all inputs">🔗</span>}
              </span>
            </div>
            <div className="name">{a.name}</div>
            <div className="sub">
              {live.status === "completed" && live.summary
                ? live.summary
                : live.status === "completed"
                  ? `done in ${live.durationMs}ms`
                  : live.status === "failed"
                    ? (live.error ?? "failed")
                    : live.status === "running"
                      ? (live.progress?.label ?? "working…")
                      : a.phaseName}
            </div>
            {live.status === "running" && live.progress && live.progress.total > 0 && (
              <div className="progress">
                <div style={{ width: `${(100 * live.progress.done) / live.progress.total}%` }} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function statusColor(status: string): string {
  if (status === "completed") return "var(--good)";
  if (status === "failed") return "var(--critical)";
  if (status === "running") return "var(--running)";
  return "var(--muted)";
}

function computeLayout(catalog: Catalog) {
  const byWave = new Map<number, CatalogAgent[]>();
  for (const a of catalog.agents) {
    const list = byWave.get(a.wave) ?? [];
    list.push(a);
    byWave.set(a.wave, list);
  }
  const maxRows = Math.max(...[...byWave.values()].map((l) => l.length));
  const pos: Record<string, { x: number; y: number }> = {};
  for (const [wave, list] of byWave) {
    list.sort((a, b) => a.num - b.num);
    const offset = ((maxRows - list.length) * ROW_H) / 2;
    list.forEach((a, i) => {
      pos[a.id] = { x: (wave - 1) * COL_W + 8, y: TOP + offset + i * ROW_H };
    });
  }
  const edges = catalog.agents.flatMap((a) => a.dependsOn.map((dep) => ({ from: dep, to: a.id })));
  return { pos, edges, maxRows };
}
