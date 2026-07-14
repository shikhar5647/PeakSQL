export interface CatalogAgent {
  id: string;
  num: number;
  name: string;
  phase: number;
  phaseName: string;
  wave: number;
  usesLlm: boolean;
  isBarrier: boolean;
  description: string;
  dependsOn: string[];
}

export interface Catalog {
  phases: Record<string, string>;
  agents: CatalogAgent[];
  waves: number;
}

export interface AgentStatus {
  status: "pending" | "running" | "completed" | "failed";
  startedAt?: number;
  endedAt?: number;
  durationMs?: number;
  summary?: string;
  error?: string;
}

export interface RunSummary {
  runId: string;
  createdAt: number;
  inputFilename: string;
  inputType: string;
  llmProvider: string;
  status: "pending" | "running" | "completed" | "completed_with_warnings" | "failed";
  error: string | null;
  agents: Record<string, AgentStatus>;
}

export interface PipelineEvent {
  seq: number;
  runId: string;
  ts: number;
  type: string;
  agentId: string | null;
  payload: Record<string, any>;
}

export interface AgentLive extends AgentStatus {
  progress?: { done: number; total: number; label: string };
}

export interface KGNode {
  id: string;
  label: string;
  properties: Record<string, any>;
}

export interface KGRel {
  id: string;
  type: string;
  source: string;
  target: string;
  properties: Record<string, any>;
}

export interface KG {
  nodes: KGNode[];
  relationships: KGRel[];
}
