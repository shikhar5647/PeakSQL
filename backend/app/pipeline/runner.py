"""Executes one pipeline run: builds the graph with per-run context, invokes it
with SQLite checkpointing (thread_id = run_id, so failed runs are resumable
without re-paying Agent 4's LLM cost), and persists all agent outputs."""
from __future__ import annotations

import json
from typing import Any

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ..config import get_settings
from ..llm.client import LLMClient
from .context import AgentContext
from .events import RunRecord
from .graph import build_graph


async def execute_run(run: RunRecord, input_path: str, options: dict[str, Any] | None = None) -> None:
    settings = get_settings()
    ctx = AgentContext(settings=settings, run=run, llm=LLMClient(settings, run))
    run.status = "running"
    run.emit("run_started", inputFilename=run.input_filename, inputType=run.input_type,
             llmProvider=ctx.llm.provider)

    initial_state = {
        "run_id": run.run_id,
        "input_path": input_path,
        "input_type": run.input_type,
        "options": options or {},
    }

    try:
        async with AsyncSqliteSaver.from_conn_string(str(settings.checkpoints_path)) as checkpointer:
            graph = build_graph(ctx).compile(checkpointer=checkpointer)
            final_state = await graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": run.run_id}, "recursion_limit": 50},
            )

        _persist_outputs(settings, run)

        verdict = (final_state.get("a13") or {}).get("validation_report", {}).get("overall_status", "passed")
        if verdict == "failed":
            run.status = "failed"
            run.error = "Validation gate failed — KG has critical gaps (see Agent 13 report)."
        elif verdict == "warning":
            run.status = "completed_with_warnings"
        else:
            run.status = "completed"
        run.emit("run_finished", status=run.status, validationStatus=verdict)
    except Exception as e:  # noqa: BLE001
        _persist_outputs(settings, run)
        run.status = "failed"
        run.error = str(e)
        run.emit("run_finished", status="failed", error=str(e))


def _persist_outputs(settings, run: RunRecord) -> None:
    run_dir = settings.runs_dir / run.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outputs.json").write_text(json.dumps(run.outputs, default=str))
    (run_dir / "run.json").write_text(json.dumps(run.summary_json(), default=str))
