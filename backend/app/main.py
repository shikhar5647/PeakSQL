"""PeakSQL backend — Stage 1: KG construction pipeline with live event streaming."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import get_settings
from .pipeline.events import run_manager

app = FastAPI(title="PeakSQL", version="0.1.0")
run_manager.restore_from_disk(get_settings().runs_dir)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/api/health")
async def health():
    s = get_settings()
    return {"status": "ok", "llmProvider": s.llm_provider,
            "neo4j": bool(s.neo4j_uri)}
