import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import AgentDetail from "../components/AgentDetail";
import EventLog from "../components/EventLog";
import KGView from "../components/KGView";
import PipelineGraph, { PHASE_COLORS } from "../components/PipelineGraph";
import ValidationView from "../components/ValidationView";
import type { Catalog, RunSummary } from "../types";
import { useRun } from "../useRun";

type Tab = "agent" | "events" | "kg" | "validation";

export default function Studio() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("events");
  const [provider, setProvider] = useState<string>("");
  const [starting, setStarting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const run = useRun(activeRunId);

  useEffect(() => {
    api.catalog().then(setCatalog);
    api.runs().then((rs) => {
      setRuns(rs);
      if (rs.length > 0) setActiveRunId(rs[0].runId);
    });
  }, []);

  // keep the sidebar list fresh while a run is live and when its status settles
  useEffect(() => {
    api.runs().then(setRuns);
    if (!run.live) return;
    const t = setInterval(() => api.runs().then(setRuns), 3000);
    return () => clearInterval(t);
  }, [run.live, run.summary?.status]);

  async function startDemo() {
    setStarting(true);
    try {
      const r = await api.createDemoRun(provider);
      afterStart(r);
    } finally {
      setStarting(false);
    }
  }

  async function startUpload() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setStarting(true);
    try {
      const r = await api.createRun(file, provider);
      afterStart(r);
    } finally {
      setStarting(false);
    }
  }

  function afterStart(r: RunSummary) {
    setRuns((prev) => [r, ...prev]);
    setActiveRunId(r.runId);
    setSelectedAgent(null);
    setTab("events");
  }

  function selectAgent(id: string) {
    setSelectedAgent(id);
    setTab("agent");
  }

  const kgReady = run.agents["a12"]?.status === "completed";
  const validationReady = run.agents["a13"]?.status === "completed";
  const agentSpec = catalog?.agents.find((a) => a.id === selectedAgent) ?? null;

  return (
    <div className="studio">
      <div className="studio-strip">
        <span className="logo-sub">Semantic Layer Studio · Stage 1 — KG construction</span>
        <span className="spacer" />
        {run.summary && (
          <>
            <span className="health">
              {run.summary.inputFilename} · LLM: {run.summary.llmProvider}
            </span>
            <span className={`badge ${run.summary.status}`}>
              <span className={`dot ${run.summary.status === "running" ? "running" : run.summary.status}`} />
              {run.summary.status.replaceAll("_", " ")}
            </span>
          </>
        )}
      </div>

      <div className="body">
        <aside className="sidebar">
          <div className="panel">
            <h3>New run</h3>
            <div className="field">
              <label>Database (.db / .sqlite / .csv / .json)</label>
              <input type="file" ref={fileRef} accept=".db,.sqlite,.sqlite3,.csv,.json" />
            </div>
            <div className="field">
              <label>LLM provider</label>
              <select value={provider} onChange={(e) => setProvider(e.target.value)}>
                <option value="">server default</option>
                <option value="mock">mock (no API key)</option>
                <option value="gemini">gemini</option>
                <option value="vllm">vLLM (open-source)</option>
                <option value="openai">openai-compatible</option>
              </select>
            </div>
            <button className="primary block" onClick={startUpload} disabled={starting}>
              Build knowledge graph
            </button>
            <div style={{ height: 8 }} />
            <button className="block" onClick={startDemo} disabled={starting}>
              ▶ Run demo (e-commerce DB)
            </button>
          </div>

          <div className="panel" style={{ flex: 1 }}>
            <h3>Runs</h3>
            {runs.length === 0 && <div className="empty">No runs yet.</div>}
            {runs.map((r) => (
              <div
                key={r.runId}
                className={`run-item ${r.runId === activeRunId ? "active" : ""}`}
                onClick={() => {
                  setActiveRunId(r.runId);
                  setSelectedAgent(null);
                  setTab("events");
                }}
              >
                <span className="name">
                  <span className={`dot ${r.status === "running" ? "running" : r.status}`} />
                  {r.inputFilename}
                </span>
                <span className="meta">
                  {new Date(r.createdAt).toLocaleTimeString([], { hour12: false })} · {r.llmProvider} · {r.status.replaceAll("_", " ")}
                </span>
              </div>
            ))}
          </div>

          {catalog && (
            <div className="panel">
              <h3>Phases</h3>
              {Object.entries(catalog.phases).map(([num, name]) => (
                <div key={num} className="graph-legend" style={{ position: "static", background: "none", padding: "2px 0" }}>
                  <span className="key">
                    <span className="swatch" style={{ background: PHASE_COLORS[Number(num)] }} />
                    {num}. {name}
                  </span>
                </div>
              ))}
            </div>
          )}
        </aside>

        <main className="main">
          <section className="graph-wrap">
            {catalog ? (
              <PipelineGraph catalog={catalog} agents={run.agents} selected={selectedAgent} onSelect={selectAgent} />
            ) : (
              <div className="empty">Loading pipeline catalog…</div>
            )}
          </section>

          <section className="bottom">
            <nav className="tabs">
              <button className={`tab ${tab === "agent" ? "active" : ""}`} onClick={() => setTab("agent")}>
                Agent detail{agentSpec && <span className="chip">A{agentSpec.num}</span>}
              </button>
              <button className={`tab ${tab === "events" ? "active" : ""}`} onClick={() => setTab("events")}>
                Live events<span className="chip">{run.events.length}</span>
              </button>
              <button className={`tab ${tab === "kg" ? "active" : ""}`} onClick={() => setTab("kg")}>
                Knowledge graph{kgReady && <span className="chip">ready</span>}
              </button>
              <button className={`tab ${tab === "validation" ? "active" : ""}`} onClick={() => setTab("validation")}>
                Validation{validationReady && <span className="chip">ready</span>}
              </button>
            </nav>

            <div className="tab-body">
              {tab === "agent" &&
                (agentSpec && activeRunId ? (
                  <AgentDetail
                    runId={activeRunId}
                    agent={agentSpec}
                    live={run.agents[agentSpec.id] ?? { status: "pending" }}
                    events={run.events}
                  />
                ) : (
                  <div className="empty">Click an agent in the pipeline to inspect its thoughts, LLM calls and output.</div>
                ))}
              {tab === "events" && catalog && <EventLog events={run.events} catalog={catalog} />}
              {tab === "kg" && activeRunId && <KGView runId={activeRunId} ready={kgReady} />}
              {tab === "kg" && !activeRunId && <div className="empty">Start a run first.</div>}
              {tab === "validation" && activeRunId && <ValidationView runId={activeRunId} ready={validationReady} />}
              {tab === "validation" && !activeRunId && <div className="empty">Start a run first.</div>}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
