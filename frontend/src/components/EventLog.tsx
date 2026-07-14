import { useEffect, useRef } from "react";
import type { Catalog, PipelineEvent } from "../types";
import { mdCode } from "./AgentDetail";

const ICONS: Record<string, string> = {
  run_started: "🚀",
  run_finished: "🏁",
  agent_started: "▶",
  agent_thought: "💭",
  agent_llm: "✨",
  agent_progress: "…",
  agent_completed: "✔",
  agent_failed: "✘",
};

/** The global, auto-following firehose of everything the pipeline is doing. */
export default function EventLog({ events, catalog }: { events: PipelineEvent[]; catalog: Catalog }) {
  const endRef = useRef<HTMLDivElement>(null);
  const names = Object.fromEntries(catalog.agents.map((a) => [a.id, `A${a.num}`]));

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [events.length]);

  const visible = events.filter((e) => e.type !== "agent_progress");
  if (visible.length === 0) return <div className="empty">Events will stream here when a run starts.</div>;

  return (
    <div>
      {visible.map((e) => (
        <div className="thought-row" key={e.seq}>
          <span className="t">{new Date(e.ts).toLocaleTimeString([], { hour12: false })}</span>
          <span className="icon">{ICONS[e.type] ?? "·"}</span>
          <span className="txt">
            {e.agentId && <span className="agent-tag">[{names[e.agentId] ?? e.agentId}] </span>}
            {describe(e)}
          </span>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}

function describe(e: PipelineEvent) {
  const p = e.payload;
  switch (e.type) {
    case "run_started":
      return <>Run started on <code>{p.inputFilename}</code> (LLM provider: {p.llmProvider})</>;
    case "run_finished":
      return <>Run finished — status: <b>{p.status}</b>{p.error ? ` · ${p.error}` : ""}</>;
    case "agent_started":
      return <>{p.name} started (wave {p.wave})</>;
    case "agent_thought":
      return mdCode(p.text);
    case "agent_llm":
      return <>LLM call: {p.label} · {p.durationMs} ms{p.error ? ` · ⚠ ${p.error}` : ""}</>;
    case "agent_completed":
      return <>completed in {p.durationMs} ms — {p.summary}</>;
    case "agent_failed":
      return <span style={{ color: "var(--critical)" }}>FAILED: {p.error}</span>;
    default:
      return e.type;
  }
}
