import type { Catalog, KG, PipelineEvent, RunSummary } from "./types";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  catalog: (): Promise<Catalog> => fetch("/api/catalog").then((r) => json<Catalog>(r)),
  runs: (): Promise<RunSummary[]> => fetch("/api/runs").then((r) => json<RunSummary[]>(r)),
  run: (id: string): Promise<RunSummary> => fetch(`/api/runs/${id}`).then((r) => json<RunSummary>(r)),
  agentOutput: (id: string, agentId: string): Promise<any> =>
    fetch(`/api/runs/${id}/outputs/${agentId}`).then((r) => json<any>(r)),
  kg: (id: string): Promise<KG> => fetch(`/api/runs/${id}/kg`).then((r) => json<KG>(r)),

  createRun: (file: File, llmProvider: string): Promise<RunSummary> => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("llm_provider", llmProvider);
    return fetch("/api/runs", { method: "POST", body: fd }).then((r) => json<RunSummary>(r));
  },

  createDemoRun: (llmProvider: string): Promise<RunSummary> => {
    const fd = new FormData();
    fd.append("llm_provider", llmProvider);
    return fetch("/api/runs/demo", { method: "POST", body: fd }).then((r) => json<RunSummary>(r));
  },

  /** SSE subscription with full replay; returns an unsubscribe fn. */
  subscribe(runId: string, onEvent: (ev: PipelineEvent) => void, onDone: () => void): () => void {
    const es = new EventSource(`/api/runs/${runId}/events`);
    es.onmessage = (msg) => {
      const ev: PipelineEvent = JSON.parse(msg.data);
      onEvent(ev);
      if (ev.type === "run_finished") {
        es.close();
        onDone();
      }
    };
    es.onerror = () => {
      es.close();
      onDone();
    };
    return () => es.close();
  },
};
