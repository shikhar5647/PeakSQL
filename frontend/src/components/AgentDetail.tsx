import { useEffect, useState } from "react";
import { api } from "../api";
import type { AgentLive, CatalogAgent, PipelineEvent } from "../types";
import JsonTree from "./JsonTree";
import { PHASE_COLORS } from "./PipelineGraph";

interface Props {
  runId: string;
  agent: CatalogAgent;
  live: AgentLive;
  events: PipelineEvent[];
}

/** Everything one agent did: its thought stream, LLM calls, and full output. */
export default function AgentDetail({ runId, agent, live, events }: Props) {
  const [view, setView] = useState<"thoughts" | "llm" | "output">("thoughts");
  const [output, setOutput] = useState<any>(null);

  const mine = events.filter((e) => e.agentId === agent.id);
  const thoughts = mine.filter((e) => e.type === "agent_thought");
  const llmCalls = mine.filter((e) => e.type === "agent_llm");

  useEffect(() => {
    setOutput(null);
    setView("thoughts");
  }, [agent.id, runId]);

  useEffect(() => {
    if (view === "output" && output === null && live.status === "completed") {
      api.agentOutput(runId, agent.id).then(setOutput).catch(() => setOutput({ error: "output unavailable" }));
    }
  }, [view, output, live.status, runId, agent.id]);

  return (
    <div>
      <div className="agent-head">
        <span className="dot" style={{ background: PHASE_COLORS[agent.phase] }} />
        <h2>
          Agent {agent.num} · {agent.name}
        </h2>
        <span className={`badge ${live.status}`}>{live.status}</span>
        {live.durationMs !== undefined && <span className="badge">{live.durationMs} ms</span>}
        {agent.usesLlm && <span className="badge">✨ LLM</span>}
        {agent.isBarrier && <span className="badge">🔗 join barrier</span>}
        <div className="desc">{agent.description}</div>
      </div>

      <div className="tabs" style={{ padding: 0, marginBottom: 10 }}>
        <button className={`tab ${view === "thoughts" ? "active" : ""}`} onClick={() => setView("thoughts")}>
          Thought stream<span className="chip">{thoughts.length}</span>
        </button>
        <button className={`tab ${view === "llm" ? "active" : ""}`} onClick={() => setView("llm")}>
          LLM calls<span className="chip">{llmCalls.length}</span>
        </button>
        <button className={`tab ${view === "output" ? "active" : ""}`} onClick={() => setView("output")}>
          Output JSON
        </button>
      </div>

      {view === "thoughts" &&
        (thoughts.length === 0 ? (
          <div className="empty">No thoughts yet — this agent hasn't started.</div>
        ) : (
          thoughts.map((e) => (
            <div className="thought-row" key={e.seq}>
              <span className="t">{time(e.ts)}</span>
              <span className="icon">💭</span>
              <span className="txt">{mdCode(e.payload.text)}</span>
            </div>
          ))
        ))}

      {view === "llm" &&
        (llmCalls.length === 0 ? (
          <div className="empty">
            {agent.usesLlm ? "No LLM calls yet." : "This agent is deterministic — it never calls the LLM."}
          </div>
        ) : (
          llmCalls.map((e) => (
            <div className="llm-call" key={e.seq}>
              <div className="meta">
                <span>{e.payload.label}</span>
                <span>{e.payload.provider} / {e.payload.model}</span>
                <span>{e.payload.durationMs} ms</span>
                {e.payload.error && <span style={{ color: "var(--critical)" }}>⚠ {e.payload.error}</span>}
              </div>
              {e.payload.promptPreview && (
                <>
                  <div className="lbl">prompt</div>
                  <pre>{e.payload.promptPreview}</pre>
                </>
              )}
              {e.payload.responsePreview && (
                <>
                  <div className="lbl">response</div>
                  <pre>{e.payload.responsePreview}</pre>
                </>
              )}
            </div>
          ))
        ))}

      {view === "output" &&
        (live.status !== "completed" ? (
          <div className="empty">Output appears once the agent completes.</div>
        ) : output === null ? (
          <div className="empty">Loading…</div>
        ) : (
          <div className="json-tree">
            <JsonTree data={output} />
          </div>
        ))}
    </div>
  );
}

function time(ts: number): string {
  return new Date(ts).toLocaleTimeString([], { hour12: false }) ;
}

/** Render `code` spans in thought text. */
export function mdCode(text: string) {
  const parts = String(text ?? "").split(/(`[^`]+`)/g);
  return parts.map((p, i) =>
    p.startsWith("`") && p.endsWith("`") ? <code key={i}>{p.slice(1, -1)}</code> : <span key={i}>{p}</span>,
  );
}
