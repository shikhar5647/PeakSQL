import { useEffect, useReducer } from "react";
import { api } from "./api";
import type { AgentLive, PipelineEvent, RunSummary } from "./types";

export interface RunState {
  summary: RunSummary | null;
  events: PipelineEvent[];
  agents: Record<string, AgentLive>;
  live: boolean;
}

const empty: RunState = { summary: null, events: [], agents: {}, live: false };

type Action =
  | { kind: "reset" }
  | { kind: "summary"; summary: RunSummary }
  | { kind: "event"; ev: PipelineEvent }
  | { kind: "done" };

function reducer(state: RunState, action: Action): RunState {
  switch (action.kind) {
    case "reset":
      return empty;
    case "summary": {
      const agents: Record<string, AgentLive> = { ...state.agents };
      for (const [id, st] of Object.entries(action.summary.agents ?? {})) {
        agents[id] = { ...agents[id], ...st };
      }
      return { ...state, summary: action.summary, agents, live: action.summary.status === "running" };
    }
    case "event": {
      const { ev } = action;
      const events = [...state.events, ev];
      const agents = { ...state.agents };
      let summary = state.summary;
      if (ev.agentId) {
        const cur: AgentLive = agents[ev.agentId] ?? { status: "pending" };
        if (ev.type === "agent_started") agents[ev.agentId] = { ...cur, status: "running", startedAt: ev.ts };
        else if (ev.type === "agent_progress")
          agents[ev.agentId] = {
            ...cur,
            progress: { done: ev.payload.done, total: ev.payload.total, label: ev.payload.label },
          };
        else if (ev.type === "agent_completed")
          agents[ev.agentId] = { ...cur, status: "completed", durationMs: ev.payload.durationMs, summary: ev.payload.summary };
        else if (ev.type === "agent_failed")
          agents[ev.agentId] = { ...cur, status: "failed", durationMs: ev.payload.durationMs, error: ev.payload.error };
      }
      if (ev.type === "run_finished" && summary) {
        summary = { ...summary, status: ev.payload.status, error: ev.payload.error ?? summary.error };
      }
      return { ...state, events, agents, summary, live: ev.type !== "run_finished" };
    }
    case "done":
      return { ...state, live: false };
  }
}

/** Subscribes to one run's event stream and folds it into live UI state. */
export function useRun(runId: string | null): RunState {
  const [state, dispatch] = useReducer(reducer, empty);

  useEffect(() => {
    dispatch({ kind: "reset" });
    if (!runId) return;
    let cancelled = false;
    api.run(runId).then((summary) => {
      if (!cancelled) dispatch({ kind: "summary", summary });
    });
    const unsub = api.subscribe(
      runId,
      (ev) => dispatch({ kind: "event", ev }),
      () => {
        dispatch({ kind: "done" });
        // refresh the final summary (status, durations) once the stream ends
        api.run(runId).then((summary) => {
          if (!cancelled) dispatch({ kind: "summary", summary });
        });
      },
    );
    return () => {
      cancelled = true;
      unsub();
    };
  }, [runId]);

  return state;
}
