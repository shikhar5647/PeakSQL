"""Run registry + event bus.

Everything an agent does — starting, thinking, calling the LLM, progressing,
finishing — is emitted as a PipelineEvent. The API streams these over SSE
(with full replay for reconnects), which is what makes the UI a live window
into the pipeline rather than a spinner.
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class PipelineEvent:
    seq: int
    run_id: str
    ts: int
    type: str                      # run_*, agent_started, agent_thought, agent_progress, agent_llm, agent_completed, agent_failed
    agent_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({
            "seq": self.seq, "runId": self.run_id, "ts": self.ts,
            "type": self.type, "agentId": self.agent_id, "payload": self.payload,
        }, default=str)


@dataclass
class RunRecord:
    run_id: str
    created_at: int
    input_filename: str
    input_type: str
    llm_provider: str
    status: str = "pending"        # pending | running | completed | completed_with_warnings | failed
    events: list[PipelineEvent] = field(default_factory=list)
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    agent_status: dict[str, dict] = field(default_factory=dict)   # agent_id -> {status, startedAt, endedAt, durationMs, summary}
    outputs: dict[str, Any] = field(default_factory=dict)         # agent_id -> full output JSON
    error: str | None = None
    _seq: int = 0

    def emit(self, type: str, agent_id: str | None = None, **payload: Any) -> PipelineEvent:
        self._seq += 1
        ev = PipelineEvent(self._seq, self.run_id, now_ms(), type, agent_id, payload)
        self.events.append(ev)
        for q in list(self.subscribers):
            q.put_nowait(ev)
        return ev

    async def subscribe(self, after_seq: int = 0):
        """Async generator: replay history after `after_seq`, then stream live."""
        q: asyncio.Queue[PipelineEvent] = asyncio.Queue()
        self.subscribers.append(q)
        try:
            for ev in list(self.events):
                if ev.seq > after_seq:
                    yield ev
            while True:
                ev = await q.get()
                yield ev
        finally:
            if q in self.subscribers:
                self.subscribers.remove(q)

    def summary_json(self) -> dict:
        return {
            "runId": self.run_id,
            "createdAt": self.created_at,
            "inputFilename": self.input_filename,
            "inputType": self.input_type,
            "llmProvider": self.llm_provider,
            "status": self.status,
            "error": self.error,
            "agents": self.agent_status,
        }


class RunManager:
    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}

    def create(self, input_filename: str, input_type: str, llm_provider: str) -> RunRecord:
        run_id = uuid.uuid4().hex[:12]
        rec = RunRecord(run_id=run_id, created_at=now_ms(),
                        input_filename=input_filename, input_type=input_type,
                        llm_provider=llm_provider)
        self._runs[run_id] = rec
        return rec

    def get(self, run_id: str) -> RunRecord | None:
        return self._runs.get(run_id)

    def list(self) -> list[RunRecord]:
        return sorted(self._runs.values(), key=lambda r: r.created_at, reverse=True)


run_manager = RunManager()
