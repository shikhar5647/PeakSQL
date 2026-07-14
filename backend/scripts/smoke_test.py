"""End-to-end smoke test: run the full 13-agent pipeline in mock mode against
the bundled demo DB and print every event + the final verdict.

Usage:  .venv/bin/python scripts/smoke_test.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.demo import ensure_demo_db          # noqa: E402
from app.config import get_settings              # noqa: E402
from app.pipeline.events import run_manager      # noqa: E402
from app.pipeline.runner import execute_run      # noqa: E402


async def main() -> int:
    settings = get_settings()
    demo = ensure_demo_db(settings)
    run = run_manager.create(demo.name, "db", "mock")

    async def watch():
        async for ev in run.subscribe():
            p = ev.payload
            if ev.type == "agent_started":
                print(f"  ▶ wave {p['wave']} · {ev.agent_id} {p['name']}")
            elif ev.type == "agent_thought":
                print(f"      💭 [{ev.agent_id}] {p['text'][:110]}")
            elif ev.type == "agent_completed":
                print(f"  ✔ {ev.agent_id} done in {p['durationMs']}ms — {p['summary']}")
            elif ev.type == "agent_failed":
                print(f"  ✘ {ev.agent_id} FAILED: {p['error']}")
            elif ev.type == "run_finished":
                print(f"\nRUN FINISHED: {p}")
                return

    watcher = asyncio.create_task(watch())
    await execute_run(run, str(demo), {"industry": "retail"})
    await watcher

    ok = run.status in ("completed", "completed_with_warnings")
    agents_done = sum(1 for a in run.agent_status.values() if a["status"] == "completed")
    kg = settings.runs_dir / run.run_id / "kg.json"
    print(f"\nstatus={run.status} · {agents_done}/13 agents completed · kg.json exists={kg.exists()}")
    return 0 if ok and agents_done == 13 and kg.exists() else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
