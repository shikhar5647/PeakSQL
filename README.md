# PeakSQL

Text-to-SQL product built on a **knowledge-graph semantic layer**. A 15-agent
LangGraph pipeline (Stage 1) reads your database, understands it — names,
descriptions, relationships, metrics, synonyms — and materializes that
understanding as a Neo4j knowledge graph. The text2sql runtime (Stage 2,
Arctic-Text2SQL-R1-7B) consults that graph to generate grounded SQL.

**This repo currently implements Stage 1** — the KG construction pipeline — plus
the *Semantic Layer Studio*, a live UI where every agent's status, thought
process, LLM calls, and outputs are visible in real time.

![status](https://img.shields.io/badge/stage%201-implemented-brightgreen)

## Architecture (Stage 1)

13 agents across 5 phases, executed with **dependency-driven parallelism**
(9 waves instead of 13 sequential steps; agents 8 and 12 are join barriers):

| Phase | Agents |
|---|---|
| 1 · Ingestion & Extraction | A1 Schema Parser · A2 Data Profiler |
| 2 · Semantic Enrichment | A3 Naming Analyzer · **A4 Description Generator ⭐ (LLM)** · A5 Domain Integrator |
| 3 · Relationship Discovery | A6 Explicit · A7 Implicit · A8 Semantic Enricher 🔗 |
| 4 · Business Intelligence | A9 Metrics · A10 Query Patterns · A11 Synonyms |
| 5 · KG Construction & Validation | A12 Graph Builder 🔗 · A13 Validation gate |

- **State**: one shared TypedDict; each agent writes only its own key.
- **Checkpointing**: SQLite checkpointer snapshots after every agent — a
  downstream failure never re-runs A4's expensive LLM calls.
- **LLM**: one OpenAI-compatible client for everything. `mock` (deterministic,
  no key) / `gemini` / `vllm` (open-source models, guided JSON decoding) /
  `openai`. Every LLM agent has a deterministic fallback, so the pipeline
  never dies on a bad response.
- **KG**: always built in-memory and persisted as `kg.json`; flushed to Neo4j
  with idempotent MERGEs when configured.
- **Validation is a gate**: critical gaps fail the run.

## Quick start

```bash
# backend (Python 3.11+)
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                      # defaults to mock LLM — no key needed
.venv/bin/uvicorn app.main:app --port 8000

# frontend (Node 18+)
cd frontend
npm install
npm run dev                               # http://localhost:5173
```

Open the studio, click **“Run demo (e-commerce DB)”**, and watch the pipeline
execute live — including Agent 7 *discovering* the deliberately undeclared
`order_items.prod_id → products` relationship from data-value overlap.

Sanity check without the UI:

```bash
cd backend && .venv/bin/python scripts/smoke_test.py
```

## Configuration

All via `backend/.env` (prefix `PEAKSQL_`, see `.env.example`):

| Variable | Purpose |
|---|---|
| `PEAKSQL_LLM_PROVIDER` | `mock` \| `gemini` \| `vllm` \| `openai` |
| `PEAKSQL_LLM_MODEL` / `_BASE_URL` / `_API_KEY` | model + OpenAI-compatible endpoint |
| `PEAKSQL_NEO4J_URI` / `_USER` / `_PASSWORD` | optional Neo4j write target |

## Repo layout

```
backend/
  app/pipeline/catalog.py    # single source of truth: agents, waves, edges
  app/pipeline/graph.py      # LangGraph wiring (barriers, checkpointing)
  app/pipeline/agents/       # a01 … a13
  app/llm/client.py          # provider-agnostic structured LLM client
  app/api/routes.py          # REST + SSE event stream
frontend/
  src/components/            # live DAG, agent detail, KG + validation views
peaksql.docx                 # full product specification
```

## Roadmap

- Stage 2: text2sql runtime (Arctic-Text2SQL-R1-7B via vLLM) consuming the KG
- Agents 14–15: continuous enhancement / feedback loops
- Evaluation harness on BIRD-dev (execution accuracy)
