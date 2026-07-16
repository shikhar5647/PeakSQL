"""HTTP + SSE API surface for the frontend."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from ..config import get_settings
from ..pipeline.catalog import catalog_json
from ..pipeline.events import run_manager
from ..pipeline.runner import execute_run
from .demo import ensure_demo_db

router = APIRouter(prefix="/api")

EXT_TO_TYPE = {".db": "db", ".sqlite": "db", ".sqlite3": "db", ".csv": "csv", ".json": "json"}


@router.get("/catalog")
async def get_catalog():
    return catalog_json()


@router.get("/runs")
async def list_runs():
    return [r.summary_json() for r in run_manager.list()]


@router.post("/runs")
async def create_run(
    file: UploadFile = File(...),
    llm_provider: str = Form(""),
    industry: str = Form("general"),
    glossary: str = Form(""),   # optional JSON array of {term, definition}
):
    settings = get_settings()
    ext = Path(file.filename or "upload.db").suffix.lower()
    input_type = EXT_TO_TYPE.get(ext)
    if not input_type:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Use .db / .sqlite / .csv / .json")

    run = run_manager.create(file.filename or f"upload{ext}", input_type,
                             llm_provider or settings.llm_provider)
    dest = settings.uploads_dir / run.run_id / (file.filename or f"upload{ext}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(await file.read())

    options: dict = {"industry": industry}
    if glossary.strip():
        try:
            options["glossary"] = json.loads(glossary)
        except json.JSONDecodeError:
            raise HTTPException(400, "glossary must be a JSON array")

    asyncio.create_task(execute_run(run, str(dest), options))
    return run.summary_json()


@router.post("/runs/demo")
async def create_demo_run(llm_provider: str = Form("")):
    """One-click run against the bundled e-commerce demo database."""
    settings = get_settings()
    demo_path = ensure_demo_db(settings)
    run = run_manager.create(demo_path.name, "db", llm_provider or settings.llm_provider)
    asyncio.create_task(execute_run(run, str(demo_path), {"industry": "retail"}))
    return run.summary_json()


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    run = run_manager.get(run_id)
    if not run:
        raise HTTPException(404, "run not found")
    return run.summary_json()


@router.get("/runs/{run_id}/events")
async def stream_events(run_id: str, after: int = 0):
    """SSE stream: replays history after `after`, then follows live events."""
    run = run_manager.get(run_id)
    if not run:
        raise HTTPException(404, "run not found")

    async def gen():
        # for already-finished runs, close after replaying the last stored event
        # (covers restored runs whose log predates the run_finished event)
        terminal = run.status not in ("pending", "running")
        last_seq = run.events[-1].seq if terminal and run.events else None
        async for ev in run.subscribe(after_seq=after):
            yield f"id: {ev.seq}\ndata: {ev.to_json()}\n\n"
            if ev.type == "run_finished" or (last_seq is not None and ev.seq >= last_seq):
                break

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/runs/{run_id}/outputs/{agent_id}")
async def get_agent_output(run_id: str, agent_id: str):
    run = run_manager.get(run_id)
    if not run:
        raise HTTPException(404, "run not found")
    if agent_id not in run.outputs:
        raise HTTPException(404, f"no output for agent '{agent_id}' (yet)")
    return run.outputs[agent_id]


@router.get("/runs/{run_id}/kg")
async def get_kg(run_id: str):
    settings = get_settings()
    kg_path = settings.runs_dir / run_id / "kg.json"
    if not kg_path.exists():
        raise HTTPException(404, "KG not built yet")
    return json.loads(kg_path.read_text())
