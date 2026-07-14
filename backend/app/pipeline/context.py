"""Per-run context injected into every agent node.

Agents never touch globals: the graph is built per run with this context bound
via closures, which is what lets us stream each run's events independently.
"""
from __future__ import annotations

import time
import traceback
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from ..config import Settings
from ..llm.client import LLMClient
from .catalog import AGENTS_BY_ID, AgentSpec
from .events import RunRecord


@dataclass
class AgentContext:
    settings: Settings
    run: RunRecord
    llm: LLMClient

    # --- what agents use to narrate their work (the UI thought stream) ---
    def think(self, agent_id: str, text: str, **extra: Any) -> None:
        self.run.emit("agent_thought", agent_id, text=text, **extra)

    def progress(self, agent_id: str, done: int, total: int, label: str = "") -> None:
        self.run.emit("agent_progress", agent_id, done=done, total=total, label=label)


AgentFn = Callable[[AgentContext, dict], Awaitable[dict[str, Any]]]


def make_node(spec: AgentSpec, fn: AgentFn, ctx: AgentContext):
    """Wrap an agent implementation with lifecycle events + timing + error capture."""

    async def node(state: dict) -> dict:
        run = ctx.run
        started = time.time()
        run.agent_status[spec.id] = {"status": "running", "startedAt": int(started * 1000)}
        run.emit("agent_started", spec.id, name=spec.name, wave=spec.wave)
        try:
            output = await fn(ctx, state)
            duration = int((time.time() - started) * 1000)
            summary = output.pop("_summary", "")
            run.outputs[spec.id] = output
            run.agent_status[spec.id].update(status="completed", endedAt=int(time.time() * 1000),
                                             durationMs=duration, summary=summary)
            run.emit("agent_completed", spec.id, durationMs=duration, summary=summary)
            return {spec.id: output}
        except Exception as e:  # noqa: BLE001
            duration = int((time.time() - started) * 1000)
            run.agent_status[spec.id].update(status="failed", endedAt=int(time.time() * 1000),
                                             durationMs=duration, error=str(e))
            run.emit("agent_failed", spec.id, durationMs=duration, error=str(e),
                     traceback=traceback.format_exc()[-2000:])
            raise

    node.__name__ = f"node_{spec.id}"
    return node


def spec(agent_id: str) -> AgentSpec:
    return AGENTS_BY_ID[agent_id]
